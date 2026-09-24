"""
Nothing-Inspired Desktop Hardware Monitor Enclosure (PULSE v2)
Faithful reproduction of reference design:
- 4" SPI TFT 480x320 display (108mm x 61.65mm)
- Arduino Uno R3 internal chassis
- Rounded-corner unibody with Nothing design language
- Top transparent observation window revealing microcontroller
- Curved shoulder Glyph Matrix LED light bar
- Side pill ventilation slots & exposed Torx screws
- Bottom-left Nothing Red power indicator dot
- Rear service lid with cable pass-through and rubber foot pockets
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix
import os

OUTPUT_DIR = "/home/mahdi/Programming/perfomance-monitor/enclosure"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001
    
    col = bpy.data.collections.new("Nothing_Pulse_Case")
    scene.collection.children.link(col)
    return col

def create_materials():
    # 1. Obsidian Black Matte Shell
    mat_shell = bpy.data.materials.new("Nothing_Mat_ObsidianMatte")
    mat_shell.use_nodes = True
    bsdf = mat_shell.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.018, 0.018, 0.020, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.65
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = 0.12

    # 2. Transparent Acrylic (Top Window & Screen Glass)
    mat_glass = bpy.data.materials.new("Nothing_Mat_ClearAcrylic")
    mat_glass.use_nodes = True
    bsdf = mat_glass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.98, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.05
        if 'Transmission Weight' in bsdf.inputs:
            bsdf.inputs['Transmission Weight'].default_value = 0.98
        elif 'Transmission' in bsdf.inputs:
            bsdf.inputs['Transmission'].default_value = 0.98
        if 'IOR' in bsdf.inputs:
            bsdf.inputs['IOR'].default_value = 1.49

    # 3. Smoked Bezel Glass
    mat_bezel_glass = bpy.data.materials.new("Nothing_Mat_SmokedGlass")
    mat_bezel_glass.use_nodes = True
    bsdf = mat_bezel_glass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.1
        if 'Transmission Weight' in bsdf.inputs:
            bsdf.inputs['Transmission Weight'].default_value = 0.6
        elif 'Transmission' in bsdf.inputs:
            bsdf.inputs['Transmission'].default_value = 0.6

    # 4. Glyph LED White Emitter
    mat_glyph_white = bpy.data.materials.new("Nothing_Mat_GlyphWhite")
    mat_glyph_white.use_nodes = True
    bsdf = mat_glyph_white.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.3
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = (1.0, 1.0, 1.0, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 4.0

    # 5. Nothing Red Emitter & Accent (#D71921)
    mat_red = bpy.data.materials.new("Nothing_Mat_NothingRed")
    mat_red.use_nodes = True
    bsdf = mat_red.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.84, 0.08, 0.10, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.3
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = (0.84, 0.08, 0.10, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 5.0

    # 6. Screen Active Matrix Emission
    mat_screen = bpy.data.materials.new("Nothing_Mat_DisplayScreen")
    mat_screen.use_nodes = True
    bsdf = mat_screen.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.005, 0.005, 0.005, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.15

    # 7. Torx Screw Metal
    mat_metal = bpy.data.materials.new("Nothing_Mat_DarkSteel")
    mat_metal.use_nodes = True
    bsdf = mat_metal.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.1, 0.1, 0.12, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.25
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = 0.95

    return {
        'shell': mat_shell,
        'glass': mat_glass,
        'bezel_glass': mat_bezel_glass,
        'glyph_white': mat_glyph_white,
        'red': mat_red,
        'screen': mat_screen,
        'metal': mat_metal,
    }

def create_rounded_box(name, width, depth, height, radius, segments=8, col=None):
    """Creates a precision rounded box mesh with fillet corners."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    
    w2 = (width / 2.0) - radius
    h2 = (height / 2.0) - radius
    d2 = depth / 2.0
    
    points = []
    # Top-right
    for i in range(segments + 1):
        angle = (math.pi / 2.0) * (i / segments)
        points.append(Vector((w2 + radius * math.cos(angle), h2 + radius * math.sin(angle), 0)))
    # Top-left
    for i in range(segments + 1):
        angle = (math.pi / 2.0) + (math.pi / 2.0) * (i / segments)
        points.append(Vector((-w2 + radius * math.cos(angle), h2 + radius * math.sin(angle), 0)))
    # Bottom-left
    for i in range(segments + 1):
        angle = math.pi + (math.pi / 2.0) * (i / segments)
        points.append(Vector((-w2 + radius * math.cos(angle), -h2 + radius * math.sin(angle), 0)))
    # Bottom-right
    for i in range(segments + 1):
        angle = (3 * math.pi / 2.0) + (math.pi / 2.0) * (i / segments)
        points.append(Vector((w2 + radius * math.cos(angle), -h2 + radius * math.sin(angle), 0)))
    
    front_verts = [bm.verts.new(Vector((p.x, -d2, p.y))) for p in points]
    back_verts = [bm.verts.new(Vector((p.x, d2, p.y))) for p in points]
    
    n = len(points)
    for i in range(n):
        next_i = (i + 1) % n
        bm.faces.new([front_verts[i], front_verts[next_i], back_verts[next_i], back_verts[i]])
    
    bm.faces.new(front_verts)
    bm.faces.new(list(reversed(back_verts)))
    
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    if col:
        col.objects.link(obj)
    else:
        bpy.context.scene.collection.objects.link(obj)
    return obj

def build_case():
    col = reset_scene()
    mats = create_materials()

    case_w = 0.126
    case_h = 0.080
    case_d = 0.054
    case_r = 0.010
    wall = 0.0025
    split_y = 0.012

    # 1. Main Outer Solid Body
    main_solid = create_rounded_box("Main_Solid", case_w, case_d, case_h, case_r, segments=12, col=col)
    
    mod_bev = main_solid.modifiers.new(type="BEVEL", name="Edge_Fillet")
    mod_bev.width = 0.0015
    mod_bev.segments = 3
    mod_bev.limit_method = 'ANGLE'
    mod_bev.angle_limit = math.radians(60)
    bpy.context.view_layer.objects.active = main_solid
    bpy.ops.object.modifier_apply(modifier="Edge_Fillet")

    # 2. Split into Front Chassis and Rear Lid
    rear_solid = main_solid.copy()
    rear_solid.data = main_solid.data.copy()
    rear_solid.name = "Pulse_Rear_Lid"
    col.objects.link(rear_solid)

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, split_y + 0.05, 0)
    )
    cut_rear = bpy.context.active_object
    cut_rear.scale = (case_w + 0.02, 0.10, case_h + 0.02)
    bpy.ops.object.transform_apply(scale=True)

    mod_c1 = main_solid.modifiers.new(type="BOOLEAN", name="Cut_To_Front")
    mod_c1.operation = 'DIFFERENCE'
    mod_c1.solver = 'EXACT'
    mod_c1.object = cut_rear
    bpy.context.view_layer.objects.active = main_solid
    bpy.ops.object.modifier_apply(modifier="Cut_To_Front")
    bpy.data.objects.remove(cut_rear, do_unlink=True)
    main_solid.name = "Pulse_Chassis_Front"

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, split_y - 0.05, 0)
    )
    cut_front = bpy.context.active_object
    cut_front.scale = (case_w + 0.02, 0.10, case_h + 0.02)
    bpy.ops.object.transform_apply(scale=True)

    mod_c2 = rear_solid.modifiers.new(type="BOOLEAN", name="Cut_To_Rear")
    mod_c2.operation = 'DIFFERENCE'
    mod_c2.solver = 'EXACT'
    mod_c2.object = cut_front
    bpy.context.view_layer.objects.active = rear_solid
    bpy.ops.object.modifier_apply(modifier="Cut_To_Rear")
    bpy.data.objects.remove(cut_front, do_unlink=True)

    # Hollow out Front Chassis
    inner_solid = create_rounded_box("Inner_Cutter", case_w - 2*wall, 0.060, case_h - 2*wall, case_r - wall, segments=12, col=col)
    inner_solid.location = (0, 0.005, 0)

    mod_hollow = main_solid.modifiers.new(type="BOOLEAN", name="Hollow_Front")
    mod_hollow.operation = 'DIFFERENCE'
    mod_hollow.solver = 'EXACT'
    mod_hollow.object = inner_solid
    bpy.context.view_layer.objects.active = main_solid
    bpy.ops.object.modifier_apply(modifier="Hollow_Front")

    mod_hollow_rear = rear_solid.modifiers.new(type="BOOLEAN", name="Hollow_Rear")
    mod_hollow_rear.operation = 'DIFFERENCE'
    mod_hollow_rear.solver = 'EXACT'
    mod_hollow_rear.object = inner_solid
    bpy.context.view_layer.objects.active = rear_solid
    bpy.ops.object.modifier_apply(modifier="Hollow_Rear")
    bpy.data.objects.remove(inner_solid, do_unlink=True)

    # 3. Cut Front Display Window (Framing 4" TFT: 94mm x 60mm)
    win_w = 0.098
    win_h = 0.062
    win_r = 0.007
    disp_cutter = create_rounded_box("Disp_Cutter", win_w, 0.020, win_h, win_r, segments=10, col=col)
    disp_cutter.location = (-0.002, -(case_d / 2.0), -0.001)

    mod_win = main_solid.modifiers.new(type="BOOLEAN", name="Cut_Display_Window")
    mod_win.operation = 'DIFFERENCE'
    mod_win.solver = 'EXACT'
    mod_win.object = disp_cutter
    bpy.context.view_layer.objects.active = main_solid
    bpy.ops.object.modifier_apply(modifier="Cut_Display_Window")
    bpy.data.objects.remove(disp_cutter, do_unlink=True)

    # Front Glass Insert
    glass_obj = create_rounded_box("Pulse_Front_Glass", win_w - 0.0004, 0.0016, win_h - 0.0004, win_r, segments=10, col=col)
    glass_obj.location = (-0.002, -(case_d / 2.0) + 0.001, -0.001)
    glass_obj.data.materials.append(mats['bezel_glass'])

    # 4. Top Transparent Technical Window
    top_win_w = 0.046
    top_win_d = 0.026
    top_win_r = 0.005
    top_win_x = -0.016
    top_win_y = -0.004

    # Top cutter in X-Y plane
    top_cutter = create_rounded_box("Top_Win_Cutter", top_win_w, 0.020, top_win_d, top_win_r, segments=8, col=col)
    top_cutter.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.view_layer.objects.active = top_cutter
    bpy.ops.object.transform_apply(rotation=True)
    top_cutter.location = (top_win_x, top_win_y, case_h / 2.0)

    mod_top = main_solid.modifiers.new(type="BOOLEAN", name="Cut_Top_Window")
    mod_top.operation = 'DIFFERENCE'
    mod_top.solver = 'EXACT'
    mod_top.object = top_cutter
    bpy.context.view_layer.objects.active = main_solid
    bpy.ops.object.modifier_apply(modifier="Cut_Top_Window")
    bpy.data.objects.remove(top_cutter, do_unlink=True)

    # Clear Acrylic Top Window Pane
    top_glass = create_rounded_box("Pulse_Top_Window", top_win_w - 0.0004, 0.002, top_win_d - 0.0004, top_win_r, segments=8, col=col)
    top_glass.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.view_layer.objects.active = top_glass
    bpy.ops.object.transform_apply(rotation=True)
    top_glass.location = (top_win_x, top_win_y, (case_h / 2.0) - 0.001)
    top_glass.data.materials.append(mats['glass'])

    # 5. Top-Right Curved Shoulder Glyph Light Bar
    glyph_col = mats['glyph_white']
    red_col = mats['red']
    total_segments = 18
    for i in range(total_segments):
        t = i / float(total_segments - 1)
        if t < 0.5:
            frac = t / 0.5
            gx = 0.024 + frac * 0.028
            gy = -0.004
            gz = (case_h / 2.0)
            ang = 0
        else:
            frac = (t - 0.5) / 0.5
            theta = frac * (math.pi / 2.0)
            center_x = (case_w / 2.0) - case_r
            center_z = (case_h / 2.0) - case_r
            gx = center_x + case_r * math.sin(theta)
            gy = -0.004
            gz = center_z + case_r * math.cos(theta)
            ang = -theta

        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(gx, gy, gz)
        )
        dash = bpy.context.active_object
        dash.name = f"Glyph_Dash_{i+1}"
        dash.scale = (0.0014, 0.006, 0.0018)
        dash.rotation_euler = (0, ang, 0)
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        
        if i >= total_segments - 2:
            dash.data.materials.append(red_col)
        else:
            dash.data.materials.append(glyph_col)
            
        for c in dash.users_collection:
            c.objects.unlink(dash)
        col.objects.link(dash)

    # 6. Right Side Ventilation Slots
    slot_w = 0.018
    slot_h = 0.0022
    slot_r = slot_h / 2.0
    slot_x = case_w / 2.0
    
    for i in range(6):
        sz = -0.016 + i * 0.0055
        slot_cut = create_rounded_box(f"Vent_{i}", slot_w, 0.010, slot_h, slot_r, segments=6, col=col)
        slot_cut.rotation_euler = (0, 0, math.radians(90))
        bpy.context.view_layer.objects.active = slot_cut
        bpy.ops.object.transform_apply(rotation=True)
        slot_cut.location = (slot_x, 0.002, sz)

        mod_v = main_solid.modifiers.new(type="BOOLEAN", name=f"Vent_Cut_{i}")
        mod_v.operation = 'DIFFERENCE'
        mod_v.solver = 'EXACT'
        mod_v.object = slot_cut
        bpy.context.view_layer.objects.active = main_solid
        bpy.ops.object.modifier_apply(modifier=f"Vent_Cut_{i}")
        bpy.data.objects.remove(slot_cut, do_unlink=True)

    # 7. Side Torx Screws
    for idx, sz in enumerate([0.020, -0.024]):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.0022,
            depth=0.0015,
            location=(case_w / 2.0 - 0.0005, -0.010, sz)
        )
        screw = bpy.context.active_object
        screw.name = f"Torx_Screw_{idx+1}"
        screw.rotation_euler = (0, math.radians(90), 0)
        bpy.ops.object.transform_apply(rotation=True)
        screw.data.materials.append(mats['metal'])
        for c in screw.users_collection:
            c.objects.unlink(screw)
        col.objects.link(screw)

    # 8. Front Bottom-Left Red Dot Indicator
    red_led_x = -0.052
    red_led_y = -(case_d / 2.0)
    red_led_z = -0.028

    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.0014,
        depth=0.002,
        location=(red_led_x, red_led_y, red_led_z)
    )
    red_led = bpy.context.active_object
    red_led.name = "Pulse_Red_LED_Dot"
    red_led.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    red_led.data.materials.append(mats['red'])
    for c in red_led.users_collection:
        c.objects.unlink(red_led)
    col.objects.link(red_led)

    # 9. Rear Cable Exit
    cable_x = 0.042
    cable_y = case_d / 2.0
    cable_z = -0.022
    
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.0045,
        depth=0.010,
        location=(cable_x, cable_y, cable_z)
    )
    cable_cut = bpy.context.active_object
    cable_cut.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)

    mod_cab = rear_solid.modifiers.new(type="BOOLEAN", name="Cut_Cable")
    mod_cab.operation = 'DIFFERENCE'
    mod_cab.solver = 'EXACT'
    mod_cab.object = cable_cut
    bpy.context.view_layer.objects.active = rear_solid
    bpy.ops.object.modifier_apply(modifier="Cut_Cable")
    bpy.data.objects.remove(cable_cut, do_unlink=True)

    # 10. Bottom Rubber Feet
    foot_coords = [
        (-0.046, -0.015),
        (+0.046, -0.015),
        (-0.046, +0.015),
        (+0.046, +0.015),
    ]
    for idx, (fx, fy) in enumerate(foot_coords):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.0035,
            depth=0.0016,
            location=(fx, fy, -(case_h / 2.0) - 0.0006)
        )
        foot = bpy.context.active_object
        foot.name = f"Rubber_Foot_{idx+1}"
        foot.data.materials.append(mats['shell'])
        for c in foot.users_collection:
            c.objects.unlink(foot)
        col.objects.link(foot)

    # 11. Import 4" TFT STEP model inside the front housing
    tft_stl = "/tmp/tft.stl"
    if os.path.exists(tft_stl):
        bpy.ops.wm.stl_import(filepath=tft_stl)
        tft_obj = bpy.context.active_object
        tft_obj.name = "TFT_4Inch_Display_Assembly"
        tft_obj.scale = (0.001, 0.001, 0.001)
        bpy.ops.object.transform_apply(scale=True)
        # Position TFT accurately behind front glass
        tft_obj.location = (-0.054, -0.0175, 0.0308)
        tft_obj.data.materials.append(mats['screen'])
        for c in tft_obj.users_collection:
            c.objects.unlink(tft_obj)
        col.objects.link(tft_obj)

    # 12. Import Arduino Uno Base inside beneath top window
    uno_stl = "/home/mahdi/Downloads/case_base.stl"
    if os.path.exists(uno_stl):
        bpy.ops.wm.stl_import(filepath=uno_stl)
        uno_obj = bpy.context.active_object
        uno_obj.name = "Arduino_Uno_Internal_Mount"
        uno_obj.scale = (0.001, 0.001, 0.001)
        bpy.ops.object.transform_apply(scale=True)
        uno_obj.location = (-0.052, -0.006, -0.036)
        uno_obj.data.materials.append(mats['shell'])
        for c in uno_obj.users_collection:
            c.objects.unlink(uno_obj)
        col.objects.link(uno_obj)

    main_solid.data.materials.append(mats['shell'])
    rear_solid.data.materials.append(mats['shell'])

    print("Nothing Pulse v2 enclosure modeled successfully.")
    return main_solid, rear_solid

def setup_studio_and_render():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False

    cam_data = bpy.data.cameras.new("Hero_Camera")
    cam_data.lens = 65
    cam_obj = bpy.data.objects.new("Hero_Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = (0.175, -0.260, 0.135)
    cam_obj.rotation_euler = (math.radians(65), 0, math.radians(33))

    light_top = bpy.data.lights.new(name="Top_Key", type='AREA')
    light_top.energy = 90.0
    light_top.size = 0.4
    light_top.color = (1.0, 0.98, 0.95)
    l1 = bpy.data.objects.new("Top_Key", light_top)
    l1.location = (0.08, -0.10, 0.35)
    l1.rotation_euler = (math.radians(20), 0, 0)
    scene.collection.objects.link(l1)

    light_rim = bpy.data.lights.new(name="Rim_Light", type='AREA')
    light_rim.energy = 65.0
    light_rim.size = 0.3
    light_rim.color = (0.85, 0.92, 1.0)
    l2 = bpy.data.objects.new("Rim_Light", light_rim)
    l2.location = (0.30, 0.05, 0.15)
    l2.rotation_euler = (0, math.radians(70), math.radians(30))
    scene.collection.objects.link(l2)

    light_fill = bpy.data.lights.new(name="Front_Fill", type='AREA')
    light_fill.energy = 25.0
    light_fill.size = 0.5
    light_fill.color = (0.9, 0.95, 1.0)
    l3 = bpy.data.objects.new("Front_Fill", light_fill)
    l3.location = (-0.15, -0.30, 0.10)
    scene.collection.objects.link(l3)

    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 0, -0.041))
    floor = bpy.context.active_object
    floor.name = "Infinite_Black_Backdrop"
    mat_floor = bpy.data.materials.new("Studio_PureBlack")
    mat_floor.use_nodes = True
    bsdf = mat_floor.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.008, 0.008, 0.010, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.5
    floor.data.materials.append(mat_floor)

    render_hero = os.path.join(OUTPUT_DIR, "nothing_pulse_v2_hero.png")
    scene.render.filepath = render_hero
    bpy.ops.render.render(write_still=True)
    print(f"Rendered hero showcase: {render_hero}")

    cam_obj.location = (0.0, -0.08, 0.32)
    cam_obj.rotation_euler = (math.radians(25), 0, 0)
    render_top = os.path.join(OUTPUT_DIR, "nothing_pulse_v2_top_window.png")
    scene.render.filepath = render_top
    bpy.ops.render.render(write_still=True)
    print(f"Rendered top technical window view: {render_top}")

def export_assets(chassis, rear_lid):
    bpy.ops.object.select_all(action='DESELECT')
    chassis.select_set(True)
    bpy.context.view_layer.objects.active = chassis
    chassis_stl = os.path.join(OUTPUT_DIR, "Nothing_Pulse_Chassis.stl")
    bpy.ops.wm.stl_export(filepath=chassis_stl, export_selected_objects=True)
    print(f"Exported Chassis STL: {chassis_stl}")

    bpy.ops.object.select_all(action='DESELECT')
    rear_lid.select_set(True)
    bpy.context.view_layer.objects.active = rear_lid
    lid_stl = os.path.join(OUTPUT_DIR, "Nothing_Pulse_Rear_Lid.stl")
    bpy.ops.wm.stl_export(filepath=lid_stl, export_selected_objects=True)
    print(f"Exported Rear Lid STL: {lid_stl}")

    blend_path = os.path.join(OUTPUT_DIR, "Nothing_Pulse_v2.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved master blend file: {blend_path}")

if __name__ == "__main__":
    chassis, rear_lid = build_case()
    setup_studio_and_render()
    export_assets(chassis, rear_lid)
