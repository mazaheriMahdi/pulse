"""
Procedural 3D Modeling Script for Nothing-Inspired Arduino Uno + 3.5" TFT Enclosure
Designed for Blender 4.x/5.x bpy engine.
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix
import os

def reset_scene():
    """Wipes all default objects and initializes clean scene."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Create main collection
    col = bpy.data.collections.new("Pulse_Case")
    bpy.context.scene.collection.children.link(col)
    
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
    bpy.context.scene.unit_settings.scale_length = 0.001

def create_materials():
    """Creates Nothing OS aesthetic PBR materials."""
    # 1. Dark Matte Case Material
    mat_body = bpy.data.materials.new("Pulse_Mat_DarkMatte")
    mat_body.use_nodes = True
    nodes = mat_body.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.015, 0.015, 0.015, 1.0) # #121212
        bsdf.inputs['Roughness'].default_value = 0.82
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = 0.05
    
    # 2. Smoked Transparent Lid Material
    mat_lid = bpy.data.materials.new("Pulse_Mat_SmokedTranslucent")
    mat_lid.use_nodes = True
    nodes = mat_lid.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.03, 0.03, 0.03, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.25
        if 'Transmission Weight' in bsdf.inputs:
            bsdf.inputs['Transmission Weight'].default_value = 0.85
        elif 'Transmission' in bsdf.inputs:
            bsdf.inputs['Transmission'].default_value = 0.85
        if 'IOR' in bsdf.inputs:
            bsdf.inputs['IOR'].default_value = 1.48

    # 3. Nothing Red Accent Material
    mat_red = bpy.data.materials.new("Pulse_Mat_NothingRed")
    mat_red.use_nodes = True
    nodes = mat_red.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.84, 0.08, 0.10, 1.0) # #D71921
        bsdf.inputs['Roughness'].default_value = 0.35
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = (0.84, 0.08, 0.10, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 0.5

    # 4. Matte White / Glyph Diffuser
    mat_glyph = bpy.data.materials.new("Pulse_Mat_GlyphDiffuser")
    mat_glyph.use_nodes = True
    nodes = mat_glyph.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.4
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = (0.95, 0.95, 0.95, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 2.0

    return mat_body, mat_lid, mat_red, mat_glyph

def build_case():
    col = bpy.data.collections["Pulse_Case"]
    mat_body, mat_lid, mat_red, mat_glyph = create_materials()

    # Dimensions in meters (Blender standard)
    # Target: 92mm (X) x 64mm (Y) x 32mm (Z)
    outer_x = 0.092
    outer_y = 0.064
    outer_z = 0.030
    wall = 0.002
    floor_thick = 0.002

    # -------------------------------------------------------------
    # Step 1: Base Shell (Pulse_Case_Body)
    # -------------------------------------------------------------
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, outer_z / 2.0)
    )
    body = bpy.context.active_object
    body.name = "Pulse_Case_Body"
    body.scale = (outer_x, outer_y, outer_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    body.data.materials.append(mat_body)
    
    for c in body.users_collection:
        c.objects.unlink(body)
    col.objects.link(body)

    # Hollow interior cavity
    inner_x = outer_x - (2 * wall)
    inner_y = outer_y - (2 * wall)
    inner_z = outer_z - floor_thick + 0.005
    
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, floor_thick + (inner_z / 2.0))
    )
    cutter_inner = bpy.context.active_object
    cutter_inner.name = "Temp_Inner_Cutter"
    cutter_inner.scale = (inner_x, inner_y, inner_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mod_bool = body.modifiers.new(type="BOOLEAN", name="Hollow_Cavity")
    mod_bool.operation = 'DIFFERENCE'
    mod_bool.solver = 'EXACT'
    mod_bool.object = cutter_inner
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Hollow_Cavity")
    bpy.data.objects.remove(cutter_inner, do_unlink=True)

    # -------------------------------------------------------------
    # Step 2: Cut Display Window (74mm x 50mm) on Front Face (Y = -outer_y/2)
    # -------------------------------------------------------------
    disp_w = 0.074
    disp_h = 0.024
    disp_y = 0.010
    
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, -outer_y / 2.0, 0.015)
    )
    disp_cut = bpy.context.active_object
    disp_cut.name = "Temp_Disp_Cut"
    disp_cut.scale = (disp_w, disp_y, disp_h)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mod_disp = body.modifiers.new(type="BOOLEAN", name="Cut_Display")
    mod_disp.operation = 'DIFFERENCE'
    mod_disp.solver = 'EXACT'
    mod_disp.object = disp_cut
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Cut_Display")
    bpy.data.objects.remove(disp_cut, do_unlink=True)

    # -------------------------------------------------------------
    # Step 3: USB-B & DC Barrel Openings on Back Face (Y = +outer_y/2)
    # -------------------------------------------------------------
    usb_w = 0.013
    usb_h = 0.012
    usb_x = -(outer_x / 2.0) + wall + 0.014
    usb_z = floor_thick + 0.004 + (usb_h / 2.0)
    
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(usb_x, outer_y / 2.0, usb_z)
    )
    usb_cut = bpy.context.active_object
    usb_cut.name = "Temp_USB_Cut"
    usb_cut.scale = (usb_w, 0.010, usb_h)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mod_usb = body.modifiers.new(type="BOOLEAN", name="Cut_USB")
    mod_usb.operation = 'DIFFERENCE'
    mod_usb.solver = 'EXACT'
    mod_usb.object = usb_cut
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Cut_USB")
    bpy.data.objects.remove(usb_cut, do_unlink=True)

    # DC Barrel Jack Cutout
    dc_x = -(outer_x / 2.0) + wall + 0.046
    dc_z = floor_thick + 0.004 + 0.005
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.005,
        depth=0.010,
        location=(dc_x, outer_y / 2.0, dc_z)
    )
    dc_cut = bpy.context.active_object
    dc_cut.name = "Temp_DC_Cut"
    dc_cut.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    mod_dc = body.modifiers.new(type="BOOLEAN", name="Cut_DC")
    mod_dc.operation = 'DIFFERENCE'
    mod_dc.solver = 'EXACT'
    mod_dc.object = dc_cut
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Cut_DC")
    bpy.data.objects.remove(dc_cut, do_unlink=True)

    # -------------------------------------------------------------
    # Step 4: Add Internal Standoffs (4x M3 screw posts)
    # -------------------------------------------------------------
    standoff_coords = [
        (-0.0343 + 0.0140, -0.0267 + 0.0025),  # Hole 1: (14.0, 2.5)
        (-0.0343 + 0.0152, -0.0267 + 0.0508),  # Hole 2: (15.2, 50.8)
        (-0.0343 + 0.0660, -0.0267 + 0.0356),  # Hole 3: (66.0, 35.6)
        (-0.0343 + 0.0660, -0.0267 + 0.0076),  # Hole 4: (66.0, 7.6)
    ]
    standoff_h = 0.004
    standoff_r_outer = 0.003
    standoff_r_inner = 0.0015

    standoff_objs = []
    for idx, (sx, sy) in enumerate(standoff_coords):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=standoff_r_outer,
            depth=standoff_h,
            location=(sx, sy, floor_thick + (standoff_h / 2.0))
        )
        post = bpy.context.active_object
        post.name = f"Pulse_Standoff_{idx+1}"
        post.data.materials.append(mat_body)
        
        bpy.ops.mesh.primitive_cylinder_add(
            radius=standoff_r_inner,
            depth=standoff_h + 0.002,
            location=(sx, sy, floor_thick + (standoff_h / 2.0) + 0.001)
        )
        hole = bpy.context.active_object
        hole.name = f"Temp_Hole_{idx+1}"
        
        mod_h = post.modifiers.new(type="BOOLEAN", name="Cut_Hole")
        mod_h.operation = 'DIFFERENCE'
        mod_h.solver = 'EXACT'
        mod_h.object = hole
        bpy.context.view_layer.objects.active = post
        bpy.ops.object.modifier_apply(modifier="Cut_Hole")
        bpy.data.objects.remove(hole, do_unlink=True)
        
        for c in post.users_collection:
            c.objects.unlink(post)
        col.objects.link(post)
        standoff_objs.append(post)

    # -------------------------------------------------------------
    # Step 5 & 6: Snap-Fit Lid with Glyph Matrix & Dot Ventilation Slots
    # -------------------------------------------------------------
    lid_thickness = 0.002
    lip_height = 0.003
    clearance = 0.0002
    
    lid_z_base = outer_z
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, lid_z_base + (lid_thickness / 2.0))
    )
    lid = bpy.context.active_object
    lid.name = "Pulse_Case_Lid"
    lid.scale = (outer_x, outer_y, lid_thickness)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    lid.data.materials.append(mat_lid)

    for c in lid.users_collection:
        c.objects.unlink(lid)
    col.objects.link(lid)

    lip_x = inner_x - (2 * clearance)
    lip_y = inner_y - (2 * clearance)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, lid_z_base - (lip_height / 2.0))
    )
    lid_lip = bpy.context.active_object
    lid_lip.name = "Temp_Lid_Lip"
    lid_lip.scale = (lip_x, lip_y, lip_height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    lip_inner_x = lip_x - 0.003
    lip_inner_y = lip_y - 0.003
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, lid_z_base - (lip_height / 2.0))
    )
    lip_inner = bpy.context.active_object
    lip_inner.name = "Temp_Lip_Inner"
    lip_inner.scale = (lip_inner_x, lip_inner_y, lip_height + 0.002)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mod_lip_hollow = lid_lip.modifiers.new(type="BOOLEAN", name="Hollow_Lip")
    mod_lip_hollow.operation = 'DIFFERENCE'
    mod_lip_hollow.solver = 'EXACT'
    mod_lip_hollow.object = lip_inner
    bpy.context.view_layer.objects.active = lid_lip
    bpy.ops.object.modifier_apply(modifier="Hollow_Lip")
    bpy.data.objects.remove(lip_inner, do_unlink=True)

    mod_union_lip = lid.modifiers.new(type="BOOLEAN", name="Union_Lip")
    mod_union_lip.operation = 'UNION'
    mod_union_lip.solver = 'EXACT'
    mod_union_lip.object = lid_lip
    bpy.context.view_layer.objects.active = lid
    bpy.ops.object.modifier_apply(modifier="Union_Lip")
    bpy.data.objects.remove(lid_lip, do_unlink=True)

    # Glyph Matrix Feature (5x3 grid of 1.5mm holes, 2.5mm pitch)
    glyph_center_x = 0.026
    glyph_center_y = 0.016
    glyph_hole_r = 0.00075
    pitch = 0.0025

    for row in range(3):
        for col_idx in range(5):
            gx = glyph_center_x + (col_idx - 2) * pitch
            gy = glyph_center_y + (row - 1) * pitch
            
            bpy.ops.mesh.primitive_cylinder_add(
                radius=glyph_hole_r,
                depth=0.010,
                location=(gx, gy, lid_z_base)
            )
            g_cut = bpy.context.active_object
            g_cut.name = f"Temp_Glyph_{row}_{col_idx}"
            
            mod_g = lid.modifiers.new(type="BOOLEAN", name=f"Glyph_{row}_{col_idx}")
            mod_g.operation = 'DIFFERENCE'
            mod_g.solver = 'EXACT'
            mod_g.object = g_cut
            bpy.context.view_layer.objects.active = lid
            bpy.ops.object.modifier_apply(modifier=f"Glyph_{row}_{col_idx}")
            bpy.data.objects.remove(g_cut, do_unlink=True)

    # Ventilation Slots (5x thin rectangular cutouts 22mm x 1.8mm)
    vent_center_x = -0.022
    for i in range(5):
        vy = (i - 2) * 0.005
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(vent_center_x, vy, lid_z_base)
        )
        v_cut = bpy.context.active_object
        v_cut.name = f"Temp_Vent_{i}"
        v_cut.scale = (0.022, 0.0018, 0.010)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        mod_v = lid.modifiers.new(type="BOOLEAN", name=f"Vent_{i}")
        mod_v.operation = 'DIFFERENCE'
        mod_v.solver = 'EXACT'
        mod_v.object = v_cut
        bpy.context.view_layer.objects.active = lid
        bpy.ops.object.modifier_apply(modifier=f"Vent_{i}")
        bpy.data.objects.remove(v_cut, do_unlink=True)

    # -------------------------------------------------------------
    # Step 7: Resistor Tray (30mm x 15mm x 6mm)
    # -------------------------------------------------------------
    tray_w = 0.030
    tray_d = 0.015
    tray_h = 0.006
    tray_x = 0.024
    tray_y = -0.018
    
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(tray_x, tray_y, floor_thick + (tray_h / 2.0))
    )
    tray = bpy.context.active_object
    tray.name = "Pulse_Resistor_Tray"
    tray.scale = (tray_w, tray_d, tray_h)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    tray.data.materials.append(mat_body)

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(tray_x, tray_y, floor_thick + 0.001 + (tray_h / 2.0))
    )
    tray_cut = bpy.context.active_object
    tray_cut.name = "Temp_Tray_Cut"
    tray_cut.scale = (tray_w - 0.0024, tray_d - 0.0024, tray_h)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mod_tc = tray.modifiers.new(type="BOOLEAN", name="Tray_Cavity")
    mod_tc.operation = 'DIFFERENCE'
    mod_tc.solver = 'EXACT'
    mod_tc.object = tray_cut
    bpy.context.view_layer.objects.active = tray
    bpy.ops.object.modifier_apply(modifier="Tray_Cavity")
    bpy.data.objects.remove(tray_cut, do_unlink=True)

    for c in tray.users_collection:
        c.objects.unlink(tray)
    col.objects.link(tray)

    # -------------------------------------------------------------
    # Step 8: Snap-fit Detent Tabs & Grooves
    # -------------------------------------------------------------
    hook_len = 0.012
    hook_protrusion = 0.0008
    hook_thick = 0.0014
    
    for side, sign in [("Front", -1), ("Back", 1)]:
        hy = sign * ((lip_y / 2.0) + (hook_protrusion / 2.0))
        hz = lid_z_base - lip_height + (hook_thick / 2.0)
        
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0, hy, hz)
        )
        snap_hook = bpy.context.active_object
        snap_hook.name = f"Temp_Snap_{side}"
        snap_hook.scale = (hook_len, hook_protrusion, hook_thick)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        mod_hook = lid.modifiers.new(type="BOOLEAN", name=f"Snap_{side}")
        mod_hook.operation = 'UNION'
        mod_hook.solver = 'EXACT'
        mod_hook.object = snap_hook
        bpy.context.view_layer.objects.active = lid
        bpy.ops.object.modifier_apply(modifier=f"Snap_{side}")
        bpy.data.objects.remove(snap_hook, do_unlink=True)

        gy = sign * (inner_y / 2.0)
        gz = outer_z - lip_height + (hook_thick / 2.0)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0, gy, gz)
        )
        groove_cut = bpy.context.active_object
        groove_cut.name = f"Temp_Groove_{side}"
        groove_cut.scale = (hook_len + 0.001, hook_protrusion * 2.0 + 0.0004, hook_thick + 0.0004)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        mod_grv = body.modifiers.new(type="BOOLEAN", name=f"Groove_{side}")
        mod_grv.operation = 'DIFFERENCE'
        mod_grv.solver = 'EXACT'
        mod_grv.object = groove_cut
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.modifier_apply(modifier=f"Groove_{side}")
        bpy.data.objects.remove(groove_cut, do_unlink=True)

    # -------------------------------------------------------------
    # Step 9: Nothing Red Power Indicator Diffuser (2mm dia)
    # -------------------------------------------------------------
    diffuser_x = -0.040
    diffuser_y = -outer_y / 2.0
    diffuser_z = 0.024
    
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.0012,
        depth=0.003,
        location=(diffuser_x, diffuser_y, diffuser_z)
    )
    red_cut = bpy.context.active_object
    red_cut.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    mod_rc = body.modifiers.new(type="BOOLEAN", name="Cut_Red_LED")
    mod_rc.operation = 'DIFFERENCE'
    mod_rc.solver = 'EXACT'
    mod_rc.object = red_cut
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="Cut_Red_LED")
    bpy.data.objects.remove(red_cut, do_unlink=True)

    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.0010,
        depth=0.0015,
        location=(diffuser_x, diffuser_y + 0.0005, diffuser_z)
    )
    red_lens = bpy.context.active_object
    red_lens.name = "Pulse_Diffuser_Red"
    red_lens.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    red_lens.data.materials.append(mat_red)

    for c in red_lens.users_collection:
        c.objects.unlink(red_lens)
    col.objects.link(red_lens)

    # Union standoffs to body for monolithic solid print
    for post in standoff_objs:
        mod_u = body.modifiers.new(type="BOOLEAN", name=f"Union_{post.name}")
        mod_u.operation = 'UNION'
        mod_u.solver = 'EXACT'
        mod_u.object = post
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.modifier_apply(modifier=f"Union_{post.name}")
        bpy.data.objects.remove(post, do_unlink=True)

    print("Enclosure geometry build finished successfully.")

def setup_studio_and_render(output_dir):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800

    cam_data = bpy.data.cameras.new("Showcase_Camera")
    cam_data.lens = 50
    cam_obj = bpy.data.objects.new("Showcase_Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Lighting
    light_key = bpy.data.lights.new(name="Key_Light", type='AREA')
    light_key.energy = 60.0
    light_key.size = 0.3
    light_key.color = (1.0, 0.98, 0.95)
    light_key_obj = bpy.data.objects.new(name="Key_Light", object_data=light_key)
    light_key_obj.location = (0.2, -0.15, 0.25)
    scene.collection.objects.link(light_key_obj)

    light_rim = bpy.data.lights.new(name="Rim_Light", type='AREA')
    light_rim.energy = 40.0
    light_rim.size = 0.2
    light_rim.color = (0.8, 0.9, 1.0)
    light_rim_obj = bpy.data.objects.new(name="Rim_Light", object_data=light_rim)
    light_rim_obj.location = (-0.2, 0.2, 0.2)
    scene.collection.objects.link(light_rim_obj)

    # Backdrop Plane
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "Studio_Backdrop"
    mat_floor = bpy.data.materials.new("Studio_Floor")
    mat_floor.use_nodes = True
    bsdf = mat_floor.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.9
    plane.data.materials.append(mat_floor)

    # Render 1: Front Isometric View
    cam_obj.location = (0.16, -0.16, 0.14)
    cam_obj.rotation_euler = (math.radians(55), 0, math.radians(45))
    render_front = os.path.join(output_dir, "pulse_case_preview.png")
    scene.render.filepath = render_front
    bpy.ops.render.render(write_still=True)
    print(f"Rendered front view to: {render_front}")

    # Render 2: Back Ports View (USB & DC Jack)
    cam_obj.location = (-0.16, 0.16, 0.14)
    cam_obj.rotation_euler = (math.radians(55), 0, math.radians(-135))
    render_back = os.path.join(output_dir, "pulse_case_back_ports.png")
    scene.render.filepath = render_back
    bpy.ops.render.render(write_still=True)
    print(f"Rendered back view to: {render_back}")

def export_assets(output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Export Body STL
    body = bpy.data.objects.get("Pulse_Case_Body")
    if body:
        bpy.ops.object.select_all(action='DESELECT')
        body.select_set(True)
        bpy.context.view_layer.objects.active = body
        body_stl = os.path.join(output_dir, "Pulse_Case_Body.stl")
        bpy.ops.wm.stl_export(filepath=body_stl, export_selected_objects=True)
        print(f"Exported Body STL: {body_stl}")

    # Export Lid STL
    lid = bpy.data.objects.get("Pulse_Case_Lid")
    if lid:
        bpy.ops.object.select_all(action='DESELECT')
        lid.select_set(True)
        bpy.context.view_layer.objects.active = lid
        lid_stl = os.path.join(output_dir, "Pulse_Case_Lid.stl")
        bpy.ops.wm.stl_export(filepath=lid_stl, export_selected_objects=True)
        print(f"Exported Lid STL: {lid_stl}")

    # Save .blend file with scene, lights, and camera intact
    blend_path = os.path.join(output_dir, "Pulse_Case.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved blend file to: {blend_path}")

if __name__ == "__main__":
    reset_scene()
    build_case()
    output_directory = "/home/mahdi/Programming/perfomance-monitor/enclosure"
    setup_studio_and_render(output_directory)
    export_assets(output_directory)
