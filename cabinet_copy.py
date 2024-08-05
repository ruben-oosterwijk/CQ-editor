import cadquery as cq
import csv
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from enum import IntEnum
from typing import List, Tuple, Dict

# Enums for better readability
class FrontType(IntEnum):
    NONE = 0
    DOOR = -1
    DOUBLE_DOORS = -2

class ConnectorType(IntEnum):
    SIDES_WIN = 0
    TOP_BOTTOM_WIN = 1
    MITERED = 2

def assign_colors(materials: List[str]) -> Dict[str, cq.Color]:
    """
    Assign unique colors to each material.
    """
    unique_materials = list(set(materials))
    colors = [
        cq.Color(0, 0, 1), cq.Color(0.6, 0.4, 0.2), cq.Color(1, 0, 0), cq.Color(0, 1, 0), cq.Color(1, 1, 0),
        cq.Color(0.5, 0, 0.5), cq.Color(1, 0.5, 0), cq.Color(1, 0.75, 0.8), cq.Color(0.5, 0.5, 0.5), cq.Color(0, 0, 0)
    ]
    return {material: colors[i % len(colors)] for i, material in enumerate(unique_materials)}

def get_panel_thickness(global_thickness: float, panel_thickness_override: str) -> float:
    """
    Get panel thickness, using global thickness if no override is provided.
    """
    return global_thickness if panel_thickness_override is None or panel_thickness_override.strip() == "" else float(panel_thickness_override)

def create_cabinet(width: float, height: float, depth: float, front_type: int, global_thickness: float,
                   top_thickness: float, bottom_thickness: float, left_thickness: float, right_thickness: float,
                   back_thickness: float, front_thickness: float, shelf_thickness: float, shelf_amount: int,
                   connector_type: int, corpus_color: cq.Color, front_color: cq.Color) -> Tuple[Dict[str, cq.Workplane], List[cq.Workplane], List[cq.Workplane]]:
    """
    Create a 3D model of the cabinet.
    """
    adjusted_depth = depth - front_thickness if front_type != FrontType.NONE else depth

    if connector_type == ConnectorType.MITERED:
        width_adjustment = height_adjustment = 0
    elif connector_type == ConnectorType.TOP_BOTTOM_WIN:
        width_adjustment = 0
        height_adjustment = top_thickness + bottom_thickness
    elif connector_type == ConnectorType.SIDES_WIN:
        width_adjustment = left_thickness + right_thickness
        height_adjustment = 0
    else:
        raise ValueError("Invalid connector type")

    panels = {
        "top": cq.Workplane("XY").box(width - width_adjustment, top_thickness, adjusted_depth).translate((0, height - top_thickness / 2, 0)),
        "bottom": cq.Workplane("XY").box(width - width_adjustment, bottom_thickness, adjusted_depth).translate((0, bottom_thickness / 2, 0)),
        "left_side": cq.Workplane("XY").box(left_thickness, height - height_adjustment, adjusted_depth).translate((-width / 2 + left_thickness / 2, height / 2, 0)),
        "right_side": cq.Workplane("XY").box(right_thickness, height - height_adjustment, adjusted_depth).translate((width / 2 - right_thickness / 2, height / 2, 0)),
        "back": cq.Workplane("XY").box(width - left_thickness - right_thickness, height - top_thickness - bottom_thickness, back_thickness).translate((0, (height - top_thickness - bottom_thickness) / 2 + bottom_thickness, -adjusted_depth / 2 + back_thickness / 2))
    }

    fronts = []
    if front_type == FrontType.DOOR:
        fronts = [cq.Workplane("XY").box(width, height, front_thickness).translate((0, height / 2, adjusted_depth / 2 + front_thickness / 2))]
    elif front_type == FrontType.DOUBLE_DOORS:
        door_width = width / 2
        fronts = [
            cq.Workplane("XY").box(door_width, height, front_thickness).translate((-width / 4, height / 2, adjusted_depth / 2 + front_thickness / 2)),
            cq.Workplane("XY").box(door_width, height, front_thickness).translate((width / 4, height / 2, adjusted_depth / 2 + front_thickness / 2))
        ]
    elif front_type > 0:  # drawers
        drawer_height = height / front_type
        for i in range(front_type):
            fronts.append(cq.Workplane("XY").box(width, drawer_height, front_thickness).translate((0, drawer_height / 2 + i * drawer_height, adjusted_depth / 2 + front_thickness / 2)))

    shelves = []
    if shelf_amount > 0:
        shelf_spacing = (height - top_thickness - bottom_thickness) / (shelf_amount + 1)
        shelf_width = width - left_thickness - right_thickness
        shelf_depth = adjusted_depth if back_thickness == 0 else adjusted_depth - back_thickness
        for i in range(shelf_amount):
            shelf_height = bottom_thickness + (i + 1) * shelf_spacing
            shelves.append(cq.Workplane("XY").box(shelf_width, shelf_thickness, shelf_depth).translate((-width / 2 + left_thickness + shelf_width / 2, shelf_height, -depth / 2 + front_thickness + shelf_depth / 2)))

    return panels, fronts, shelves

def read_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Read CSV file and return rows as a list of dictionaries.
    """
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        return list(reader)

def add_cabinet_to_assembly(assembly: cq.Assembly, name: str, parts: Tuple[Dict[str, cq.Workplane], List[cq.Workplane], List[cq.Workplane]], color: cq.Color, position: float, width: float, depth: float):
    """
    Add cabinet parts to the main assembly.
    """
    panels, fronts, shelves = parts
    for part_name, part in panels.items():
        assembly.add(part, name=part_name.capitalize(), loc=cq.Location(cq.Vector(position + width / 2, 0, -depth / 2)), color=color)
    for i, front in enumerate(fronts):
        assembly.add(front, name=f"Front {i + 1}", loc=cq.Location(cq.Vector(position + width / 2, 0, -depth / 2)), color=color)
    for i, shelf in enumerate(shelves):
        assembly.add(shelf, name=f"Shelf {i + 1}", loc=cq.Location(cq.Vector(position + width / 2, 0, -depth / 2)), color=color)

def main():
    """
    Main function to run the program.
    """
    # Hide the main tkinter window
    Tk().withdraw()

    # Ask the user to select the CSV file
    csv_path = askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not csv_path:
        print("No file selected. Exiting.")
        return

    try:
        data_rows = read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

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
        front_type = int(data["Front type (0=none, -1=door, -2=2 doors, n>0=drawer number)"]) if data["Front type (0=none, -1=door, -2=2 doors, n>0=drawer number)"].strip() != "" else FrontType.NONE
        connector_type = int(data["Connection type (0=sides win, 1=top/bottom win, 2=mitered)"]) if data["Connection type (0=sides win, 1=top/bottom win, 2=mitered)"].strip() != "" else ConnectorType.SIDES_WIN
        
        top_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (top)"))
        bottom_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (bottom)"))
        left_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (left)"))
        right_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (right)"))
        back_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (back)"))
        front_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (front)"))
        shelf_thickness = get_panel_thickness(global_thickness, data.get("Thickness override (shelf)"))

        corpus_color = corpus_color_map[corpus_material]
        front_color = front_color_map[front_material]

        parts = create_cabinet(width, height, depth, front_type, global_thickness,
                               top_thickness, bottom_thickness, left_thickness,
                               right_thickness, back_thickness, front_thickness, shelf_thickness, shelf_amount, connector_type,
                               corpus_color, front_color)

        cabinet_assembly = cq.Assembly(name=cabinet_name)
        add_cabinet_to_assembly(cabinet_assembly, cabinet_name, parts, corpus_color, current_x_position, width, depth)

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
