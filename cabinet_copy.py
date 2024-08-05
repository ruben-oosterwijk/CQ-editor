import cadquery as cq
import csv
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Define a function to assign unique colors to materials
def assign_colors(materials):
    unique_materials = list(set(materials))
    color_map = {}
    colors = [
        cq.Color(0, 0, 1), cq.Color(0.6, 0.4, 0.2), cq.Color(1, 0, 0), cq.Color(0, 1, 0), cq.Color(1, 1, 0),
        cq.Color(0.5, 0, 0.5), cq.Color(1, 0.5, 0), cq.Color(1, 0.75, 0.8), cq.Color(0.5, 0.5, 0.5), cq.Color(0, 0, 0)
    ]
    for i, material in enumerate(unique_materials):
        color_map[material] = colors[i % len(colors)]
    return color_map

def get_panel_thickness(global_thickness, panel_thickness_override):
    if panel_thickness_override is None or panel_thickness_override.strip() == "":
        return global_thickness
    else:
        return float(panel_thickness_override)

def create_cabinet(width, height, depth, front_type, global_thickness, top_thickness, bottom_thickness, left_thickness, right_thickness, back_thickness, front_thickness, shelf_thickness, shelf_amount, connector_type, corpus_color, front_color):
    # Adjust depth to account for the front panel
    adjusted_depth = depth - front_thickness if front_type != 0 else depth

    if connector_type == 2:  # mitered
        width_adjustment = 0
        height_adjustment = 0
    elif connector_type == 1:  # top/bottom win
        width_adjustment = 0
        height_adjustment = top_thickness + bottom_thickness
    elif connector_type == 0:  # sides win
        width_adjustment = left_thickness + right_thickness
        height_adjustment = 0
    else:
        raise ValueError("Invalid connector type")

    top_width = width - width_adjustment
    top_height = top_thickness
    top_depth = adjusted_depth
    top_translation = (0, height - top_thickness / 2, 0)

    bottom_width = width - width_adjustment
    bottom_height = bottom_thickness
    bottom_depth = adjusted_depth
    bottom_translation = (0, bottom_thickness / 2, 0)

    left_width = left_thickness
    left_height = height - height_adjustment
    left_depth = adjusted_depth
    left_translation = (-width / 2 + left_thickness / 2, height / 2, 0)

    right_width = right_thickness
    right_height = height - height_adjustment
    right_depth = adjusted_depth
    right_translation = (width / 2 - right_thickness / 2, height / 2, 0)

    back_width = width - left_thickness - right_thickness
    back_height = height - top_thickness - bottom_thickness
    back_depth = back_thickness
    back_translation = (0, back_height / 2 + bottom_thickness, -adjusted_depth / 2 + back_thickness / 2)

    fronts = []
    front_names = []
    if front_type == -1:  # single door
        front_width = width
        front_height = height
        front_depth = front_thickness
        front_translation = (0, height / 2, adjusted_depth / 2 + front_thickness / 2)
        fronts = [cq.Workplane("XY").box(front_width, front_height, front_depth).translate(front_translation)]
        front_names = ["Single Door"]
    elif front_type == -2:  # two doors
        door_width = width / 2
        front_height = height
        front_depth = front_thickness
        left_door_translation = (-width / 4, height / 2, adjusted_depth / 2 + front_thickness / 2)
        right_door_translation = (width / 4, height / 2, adjusted_depth / 2 + front_thickness / 2)
        fronts = [
            cq.Workplane("XY").box(door_width, front_height, front_depth).translate(left_door_translation),
            cq.Workplane("XY").box(door_width, front_height, front_depth).translate(right_door_translation)
        ]
        front_names = ["Double Door Left", "Double Door Right"]
    elif front_type > 0:  # drawers
        drawer_height = height / front_type
        for i in range(front_type):
            front_translation = (0, drawer_height / 2 + i * drawer_height, adjusted_depth / 2 + front_thickness / 2)
            fronts.append(cq.Workplane("XY").box(width, drawer_height, front_thickness).translate(front_translation))
            front_names.append(f"Drawer Front {i + 1}")

    # Create panels
    top = cq.Workplane("XY").box(top_width, top_height, top_depth).translate(top_translation)
    bottom = cq.Workplane("XY").box(bottom_width, bottom_height, bottom_depth).translate(bottom_translation)
    left_side = cq.Workplane("XY").box(left_width, left_height, left_depth).translate(left_translation)
    right_side = cq.Workplane("XY").box(right_width, right_height, right_depth).translate(right_translation)
    back = cq.Workplane("XY").box(back_width, back_height, back_depth).translate(back_translation)

    # Create shelves
    shelves = []
    if shelf_amount > 0:
        shelf_spacing = (height - top_thickness - bottom_thickness) / (shelf_amount + 1)
        shelf_width = width - left_thickness - right_thickness
        shelf_depth = adjusted_depth if back_thickness == 0 else adjusted_depth - back_thickness
        for i in range(shelf_amount):
            shelf_height = bottom_thickness + (i + 1) * shelf_spacing
            shelf_translation = (-width / 2 + left_thickness + shelf_width / 2, shelf_height, -depth / 2 + front_thickness + shelf_depth / 2)
            shelf = cq.Workplane("XY").box(shelf_width, shelf_thickness, shelf_depth).translate(shelf_translation)
            shelves.append(shelf)

    return top, bottom, left_side, right_side, back, fronts, shelves, front_names

def read_csv(file_path):
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        return list(reader)  # Return all rows as a list of dictionaries

def main():
    # Hide the main tkinter window
    Tk().withdraw()

    # Ask the user to select the CSV file
    csv_path = askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not csv_path:
        print("No file selected. Exiting.")
        return

    data_rows = read_csv(csv_path)

    corpus_materials = [row["Material corpus (Each unique entry will become a unique color)"] for row in data_rows]
    front_materials = [row["Material front (Each unique entry will become a unique color)"] for row in data_rows]

    corpus_color_map = assign_colors(corpus_materials)
    front_color_map = assign_colors(front_materials)

    parent_assembly_name = Path(csv_path).stem
    parent_assembly = cq.Assembly(name=parent_assembly_name)

    current_x_position = 0  # Track the current x position for the next cabinet

    for data in data_rows:
        corpus_material = data["Material corpus (Each unique entry will become a unique color)"]
        front_material = data["Material front (Each unique entry will become a unique color)"]

        cabinet_name = data["Name of cabinet (parent component)"]
        width = float(data["Corpus  Width (mm)"])
        height = float(data["Corpus Height (mm)"])
        depth = float(data["Corpus Dept (mm)"])
        global_thickness = float(data["Global Thickness (mm)"])
        shelf_amount = int(data["Shelf amount"])
        front_type = int(data["Front type (0=none, -1=door, -2=2 doors, n>0=drawer number)"]) if data["Front type (0=none, -1=door, -2=2 doors, n>0=drawer number)"].strip() != "" else 0
        connector_type = int(data["Connection type (0=sides win, 1=top/bottom win, 2=mitered)"]) if data["Connection type (0=sides win, 1=top/bottom win, 2=mitered)"].strip() != "" else 0
        
        top_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (top)"))
        bottom_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (bottom)"))
        left_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (left)"))
        right_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (right)"))
        back_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (back)"))
        front_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (front)"))
        shelf_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (shelf)"))

        corpus_color = corpus_color_map[corpus_material]
        front_color = front_color_map[front_material]

        top, bottom, left_side, right_side, back, fronts, shelves, front_names = create_cabinet(
            width, height, depth, front_type, global_thickness,
            top_thickness, bottom_thickness, left_thickness,
            right_thickness, back_thickness, front_thickness, shelf_thickness, shelf_amount, connector_type,
            corpus_color, front_color
        )

        cabinet_assembly = cq.Assembly(name=cabinet_name)
        cabinet_assembly.add(top, name="Top Panel", loc=cq.Location(cq.Vector(current_x_position+(width/2), 0, -depth/2)), color=corpus_color)
        cabinet_assembly.add(bottom, name="Bottom Panel", loc=cq.Location(cq.Vector(current_x_position+(width/2), 0, -depth/2)), color=corpus_color)
        cabinet_assembly.add(left_side, name="Left Side Panel", loc=cq.Location(cq.Vector(current_x_position+(width/2), 0, -depth/2)), color=corpus_color)
        cabinet_assembly.add(right_side, name="Right Side Panel", loc=cq.Location(cq.Vector(current_x_position+(width/2), 0, -depth/2)), color=corpus_color)
        cabinet_assembly.add(back, name="Back Panel", loc=cq.Location(cq.Vector(current_x_position+(width/2), 0, -depth/2)), color=corpus_color)
        for i, (front, front_name) in enumerate(zip(fronts, front_names)):
            cabinet_assembly.add(front, name=front_name, loc=cq.Location(cq.Vector(current_x_position+(width/2), 0, -depth/2)), color=front_color)
        for i, shelf in enumerate(shelves):
            cabinet_assembly.add(shelf, name=f"Shelf {i + 1}", loc=cq.Location(cq.Vector(current_x_position+(width/2), 0, -depth/2)), color=corpus_color)

        parent_assembly.add(cabinet_assembly)

        # Update the current x position for the next cabinet
        current_x_position += width

    # Save the STEP file with the name derived from the CSV file name
    step_file_name = Path(csv_path).stem + ".step"
    file_path = Path(step_file_name).resolve()
    parent_assembly.save(str(file_path))
    print(f"Cabinet model has been saved as {file_path}")

    try:
        from cq_editor import show_object
        show_object(parent_assembly, name='Cabinet')
    except ImportError:
        print("CQ-editor is not installed. Please install it to visualize the model.")

if __name__ == "__main__":
    main()
