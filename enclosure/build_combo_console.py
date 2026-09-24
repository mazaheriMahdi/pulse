#!/usr/bin/env python3
"""
Open-Frame Arduino-Pi Combo Console (Refined CAD & Hero Renderer)
Strictly faithful to Nothing's design language and blueprint ACPC-001 / media_1790210937702.png

Features:
- Full procedural wedge chassis: 185 mm W x 95 mm D x 16 mm Front H / 65 mm Rear H (approx 23 deg incline)
- Diamond-cut silver CNC perimeter chamfer
- 4 flush M3 counterbored hex socket cap screws
- Left transparent inspection window with high-detail compute board (dual USB port, BGA processor chip, crystal, passives)
- Recessed 4.0" display window with anti-glare matte finish
- Pitch-perfect Nothing dot-matrix screen UI (37% / 54°C and 82% / 71°C)
- Razor-sharp transparent silkscreen decals (no grey artifacts)
- 20-segment curved L-shaped Glyph Matrix (Nothing Red accent on dash 6, glowing vertical bar)
- 5x5 circular perforated speaker grille + circular Nothing Red indicator LED
- Physical internal hardware (Arduino Uno R3, 4" TFT LCD, 8-wire SPI ribbon, 4-wire interconnect)
- 4 vibrant orange polymer isolation feet
- Right USB-C port with black braided cable
- Photorealistic studio lighting & wood desk rendered in Cycles OptiX GPU
"""

import os
import sys
import math
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "/home/mahdi/Programming/perfomance-monitor/enclosure"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. TEXTURE GENERATION
# ---------------------------------------------------------
def generate_screen_texture():
    tex_path = os.path.join(OUTPUT_DIR, "combo_screen_ui.png")
    w, h = 960, 640
    img = Image.new('RGB', (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 5x7 dot-matrix font definition (column bytes, row 0 is top bit 0)
    FONT_5X7 = {
        ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
        '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
        '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
        '2': [0x42, 0x61, 0x51, 0x49, 0x46],
        '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
        '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
        '5': [0x27, 0x45, 0x45, 0x45, 0x39],
        '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
        '7': [0x01, 0x71, 0x09, 0x05, 0x03],
        '8': [0x36, 0x49, 0x49, 0x49, 0x36],
        '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
        '%': [0x23, 0x13, 0x08, 0x64, 0x62],
        'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
        'deg': [0x02, 0x05, 0x02, 0x00, 0x00],  # Precise 3x3 circular degree symbol
    }

    def draw_dots(d, text_items, start_x, start_y, dot_size, pitch, color):
        cx = start_x
        for item in text_items:
            cols = FONT_5X7.get(item, FONT_5X7[' '])
            for col_idx, col_byte in enumerate(cols):
                x = cx + col_idx * pitch
                for row_idx in range(7):
                    if (col_byte >> row_idx) & 1:
                        y = start_y + row_idx * pitch
                        r = dot_size / 2.0
                        d.ellipse([x - r, y - r, x + r, y + r], fill=color)
            cx += (len(cols) + 1) * pitch

    # Top line large percentages: 37% and 82%
    draw_dots(draw, ['3', '7', '%'], 90, 160, 16.0, 23.0, (255, 255, 255))
    draw_dots(draw, ['8', '2', '%'], 540, 160, 16.0, 23.0, (255, 255, 255))

    # Bottom line temperatures aligned below percentages: 54°C and 71°C
    draw_dots(draw, ['5', '4', 'deg', 'C'], 130, 390, 8.5, 14.5, (230, 235, 245))
    draw_dots(draw, ['7', '1', 'deg', 'C'], 580, 390, 8.5, 14.5, (230, 235, 245))

    img.save(tex_path)
    return tex_path

def generate_bezel_texture():
    tex_path = os.path.join(OUTPUT_DIR, "combo_bezel_silkscreen.png")
    w, h = 1024, 256
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0)) # Fully transparent base
    draw = ImageDraw.Draw(img)

    font_path_reg = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf"
    font_path_bold = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf"

    font_small = ImageFont.truetype(font_path_reg, 24)
    font_labels = ImageFont.truetype(font_path_bold, 36)

    # Monospace caption text
    caption = "tiny white silkscreen text in Nothing's monospace style."
    draw.text((40, 42), caption, fill=(240, 245, 250, 255), font=font_small)

    # Function labels: CPU, GPU, GLYPH, USB
    draw.text((50, 140), 'CPU', fill=(240, 245, 250, 255), font=font_labels)
    draw.text((250, 140), 'GPU', fill=(240, 245, 250, 255), font=font_labels)
    draw.text((460, 140), 'GLYPH', fill=(240, 245, 250, 255), font=font_labels)
    draw.text((700, 140), 'USB', fill=(240, 245, 250, 255), font=font_labels)

    img.save(tex_path)
    return tex_path

# ---------------------------------------------------------
# 2. SCENE SETUP & MATERIALS
# ---------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001
    col = bpy.data.collections.new("Nothing_Combo_Console")
    scene.collection.children.link(col)
    return col

def create_materials(screen_tex, silkscreen_tex):
    # 1. Dark Charcoal Matte Anodized Aluminum
    mat_body = bpy.data.materials.new("Combo_Mat_DarkCharcoal")
    mat_body.use_nodes = True
    b = mat_body.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.018, 0.019, 0.022, 1.0)
        b.inputs['Roughness'].default_value = 0.38
        if 'Metallic' in b.inputs:
            b.inputs['Metallic'].default_value = 0.85

    # 2. Diamond-Cut Silver CNC Chamfer Edge
    mat_cnc = bpy.data.materials.new("Combo_Mat_CNC_Silver")
    mat_cnc.use_nodes = True
    b = mat_cnc.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.84, 0.86, 0.88, 1.0)
        b.inputs['Roughness'].default_value = 0.14
        if 'Metallic' in b.inputs:
            b.inputs['Metallic'].default_value = 0.98

    # 3. Flawless Transparent Silkscreen Decal
    mat_silkscreen = bpy.data.materials.new("Combo_Mat_Silkscreen_Decal")
    mat_silkscreen.use_nodes = True
    tree = mat_silkscreen.node_tree
    tree.nodes.clear()
    out = tree.nodes.new(type='ShaderNodeOutputMaterial')
    transp = tree.nodes.new(type='ShaderNodeBsdfTransparent')
    bsdf = tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.95, 0.96, 0.98, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.25
    if 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = (0.95, 0.96, 0.98, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 0.8

    mix = tree.nodes.new(type='ShaderNodeMixShader')
    coord = tree.nodes.new(type='ShaderNodeTexCoord')
    tex_silk = tree.nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(silkscreen_tex):
        tex_silk.image = bpy.data.images.load(silkscreen_tex)

    tree.links.new(coord.outputs['UV'], tex_silk.inputs['Vector'])
    tree.links.new(tex_silk.outputs['Alpha'], mix.inputs['Fac'])
    tree.links.new(transp.outputs['BSDF'], mix.inputs[1])
    tree.links.new(bsdf.outputs['BSDF'], mix.inputs[2])
    tree.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    mat_silkscreen.blend_method = 'BLEND'

    # 4. Display Screen with Anti-Glare Matte Surface & Emissive Dot-Matrix UI
    mat_screen = bpy.data.materials.new("Combo_Mat_Screen")
    mat_screen.use_nodes = True
    tree = mat_screen.node_tree
    tree.nodes.clear()
    out = tree.nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.003, 0.003, 0.004, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.22 # Matte anti-glare finish prevents sharp horizon lines
    bsdf.inputs['IOR'].default_value = 1.45
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.35

    coord = tree.nodes.new(type='ShaderNodeTexCoord')
    tex_screen = tree.nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(screen_tex):
        tex_screen.image = bpy.data.images.load(screen_tex)
    tree.links.new(coord.outputs['UV'], tex_screen.inputs['Vector'])
    tree.links.new(tex_screen.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 18.0
    tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    # 5. Clear Inspection Window Glass / Polycarbonate
    mat_glass = bpy.data.materials.new("Combo_Mat_InspectionGlass")
    mat_glass.use_nodes = True
    b = mat_glass.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.98, 0.99, 1.0, 1.0)
        b.inputs['Roughness'].default_value = 0.03
        b.inputs['IOR'].default_value = 1.49
        if 'Transmission Weight' in b.inputs:
            b.inputs['Transmission Weight'].default_value = 0.98
        elif 'Transmission' in b.inputs:
            b.inputs['Transmission'].default_value = 0.98

    # 6. Green Circuit Board Material
    mat_pcb = bpy.data.materials.new("Combo_Mat_GreenPCB")
    mat_pcb.use_nodes = True
    b = mat_pcb.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.015, 0.075, 0.030, 1.0)
        b.inputs['Roughness'].default_value = 0.28

    # 7. SMT Metal / Solder Contacts
    mat_metal = bpy.data.materials.new("Combo_Mat_SMT_Metal")
    mat_metal.use_nodes = True
    b = mat_metal.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.86, 0.88, 0.90, 1.0)
        b.inputs['Roughness'].default_value = 0.15
        if 'Metallic' in b.inputs:
            b.inputs['Metallic'].default_value = 0.98

    # 8. Gunmetal Fasteners
    mat_bolt = bpy.data.materials.new("Combo_Mat_Gunmetal_Bolt")
    mat_bolt.use_nodes = True
    b = mat_bolt.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.035, 0.036, 0.040, 1.0)
        b.inputs['Roughness'].default_value = 0.25
        if 'Metallic' in b.inputs:
            b.inputs['Metallic'].default_value = 0.95

    # 9. Black IC Package
    mat_ic = bpy.data.materials.new("Combo_Mat_IC_Epoxy")
    mat_ic.use_nodes = True
    b = mat_ic.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.008, 0.008, 0.010, 1.0)
        b.inputs['Roughness'].default_value = 0.40

    # 10. Glyph Lit White LED
    mat_glyph_lit = bpy.data.materials.new("Combo_Mat_GlyphLit")
    mat_glyph_lit.use_nodes = True
    b = mat_glyph_lit.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        b.inputs['Roughness'].default_value = 0.12
        if 'Emission Color' in b.inputs:
            b.inputs['Emission Color'].default_value = (1.0, 1.0, 1.0, 1.0)
            b.inputs['Emission Strength'].default_value = 26.0

    # 11. Nothing Red Accent & LED (#D71921)
    mat_red = bpy.data.materials.new("Combo_Mat_NothingRed")
    mat_red.use_nodes = True
    b = mat_red.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.84, 0.08, 0.12, 1.0)
        b.inputs['Roughness'].default_value = 0.12
        if 'Emission Color' in b.inputs:
            b.inputs['Emission Color'].default_value = (0.84, 0.08, 0.12, 1.0)
            b.inputs['Emission Strength'].default_value = 32.0

    # 12. Glyph Inactive Segment (Dark Matte Graphite)
    mat_glyph_off = bpy.data.materials.new("Combo_Mat_GlyphOff")
    mat_glyph_off.use_nodes = True
    b = mat_glyph_off.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.022, 0.023, 0.025, 1.0)
        b.inputs['Roughness'].default_value = 0.35

    # 13. Vibrant Orange Polymer Feet (#EA480D)
    mat_orange = bpy.data.materials.new("Combo_Mat_OrangeFoot")
    mat_orange.use_nodes = True
    b = mat_orange.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.92, 0.28, 0.05, 1.0)
        b.inputs['Roughness'].default_value = 0.40

    # 14. Braided Nylon Black Cable
    mat_cable = bpy.data.materials.new("Combo_Mat_BraidedCable")
    mat_cable.use_nodes = True
    b = mat_cable.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = (0.012, 0.012, 0.014, 1.0)
        b.inputs['Roughness'].default_value = 0.60

    # 15. Wire colors
    wire_colors = {
        'red': (0.85, 0.05, 0.05, 1.0),
        'black': (0.02, 0.02, 0.02, 1.0),
        'blue': (0.05, 0.20, 0.85, 1.0),
        'yellow': (0.85, 0.75, 0.05, 1.0),
        'green': (0.05, 0.65, 0.15, 1.0),
        'white': (0.90, 0.90, 0.90, 1.0)
    }
    mat_wires = {}
    for name, col_val in wire_colors.items():
        m = bpy.data.materials.new(f"Mat_Wire_{name}")
        m.use_nodes = True
        bs = m.node_tree.nodes.get("Principled BSDF")
        if bs:
            bs.inputs['Base Color'].default_value = col_val
            bs.inputs['Roughness'].default_value = 0.30
        mat_wires[name] = m

    return {
        'body': mat_body,
        'cnc': mat_cnc,
        'silkscreen': mat_silkscreen,
        'screen': mat_screen,
        'glass': mat_glass,
        'pcb': mat_pcb,
        'metal': mat_metal,
        'bolt': mat_bolt,
        'ic': mat_ic,
        'glyph_lit': mat_glyph_lit,
        'glyph_off': mat_glyph_off,
        'red': mat_red,
        'orange': mat_orange,
        'cable': mat_cable,
        'wires': mat_wires,
    }

# ---------------------------------------------------------
# 3. GEOMETRY PROCEDURAL FUNCTIONS
# ---------------------------------------------------------
def create_wedge_solid(name, width, depth, front_h, rear_h, col, mat):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    w2 = width / 2.0
    d2 = depth / 2.0

    profile = [
        Vector((-d2, 0.0)),
        Vector((+d2, 0.0)),
        Vector((+d2, rear_h)),
        Vector((-d2, front_h)),
    ]

    verts_left = [bm.verts.new(Vector((-w2, p.x, p.y))) for p in profile]
    verts_right = [bm.verts.new(Vector((+w2, p.x, p.y))) for p in profile]

    bm.faces.new([verts_left[0], verts_left[1], verts_left[2], verts_left[3]])
    bm.faces.new([verts_right[3], verts_right[2], verts_right[1], verts_right[0]])
    bm.faces.new([verts_left[0], verts_right[0], verts_right[1], verts_left[1]])
    bm.faces.new([verts_left[1], verts_right[1], verts_right[2], verts_left[2]])
    bm.faces.new([verts_left[2], verts_right[2], verts_right[3], verts_left[3]])
    bm.faces.new([verts_left[3], verts_right[3], verts_right[0], verts_left[0]])

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj

def create_m3_screw(name, location, rotation_euler, col, mat_bolt):
    # M3 socket head screw sitting recessed inside counterbore
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.0028,
        depth=0.0022,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rotation_euler
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    obj.data.materials.append(mat_bolt)

    # Cut hexagonal Allen socket inside screw head
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.0014,
        depth=0.0014,
        vertices=6,
        location=location
    )
    hex_cut = bpy.context.active_object
    hex_cut.rotation_euler = rotation_euler
    bpy.ops.object.transform_apply(scale=True, rotation=True)

    mod_hex = obj.modifiers.new(type="BOOLEAN", name="Hex_Socket")
    mod_hex.operation = 'DIFFERENCE'
    mod_hex.solver = 'EXACT'
    mod_hex.object = hex_cut
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Hex_Socket")
    bpy.data.objects.remove(hex_cut, do_unlink=True)
    col.objects.link(obj)
    return obj

# ---------------------------------------------------------
# 4. MAIN CONSOLE BUILDER
# ---------------------------------------------------------
def build_combo_console():
    col = reset_scene()

    # Generate display and silkscreen textures
    screen_tex = generate_screen_texture()
    silkscreen_tex = generate_bezel_texture()
    mats = create_materials(screen_tex, silkscreen_tex)

    # Blueprint ACPC-001 Specifications:
    case_w = 0.185       # 185 mm Width
    case_d = 0.095       # 95 mm Depth
    front_h = 0.016      # 16 mm Front Height
    rear_h = 0.065       # 65 mm Rear Height
    wall = 0.003         # 3.0 mm Wall thickness

    # Slope calculations
    hypot = math.sqrt(case_d**2 + (rear_h - front_h)**2)
    theta = math.atan2(rear_h - front_h, case_d)  # ~27.2 degrees
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    def to_world(x, y_along_incline, z_perp_offset):
        y_world = y_along_incline * cos_t - z_perp_offset * sin_t
        z_base_at_y = front_h + (y_along_incline + case_d / 2.0) * ((rear_h - front_h) / case_d)
        z_world = z_base_at_y + z_perp_offset * cos_t
        return Vector((x, y_world, z_world))

    rot_face_matrix = Matrix.Rotation(theta, 4, 'X')

    # 1. Main Wedge Chassis Body
    wedge = create_wedge_solid("Pulse_Combo_Chassis", case_w, case_d, front_h, rear_h, col, mats['body'])
    wedge.data.materials.append(mats['cnc'])

    # 2. Silver Diamond-Cut CNC Perimeter Bevel Chamfer
    mod_bev = wedge.modifiers.new(type="BEVEL", name="CNC_Silver_Chamfer")
    mod_bev.width = 0.0016
    mod_bev.segments = 2
    mod_bev.material = 1  # Assigns mats['cnc'] to chamfer faces automatically
    bpy.context.view_layer.objects.active = wedge
    bpy.ops.object.modifier_apply(modifier="CNC_Silver_Chamfer")

    # 3. Main 4.0" Display Aperture Cutout
    disp_w = 0.098
    disp_h = 0.058
    disp_center_x = 0.016
    screen_y_loc = 0.003

    pocket_pos = to_world(disp_center_x, screen_y_loc, -0.005)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=pocket_pos)
    disp_cut = bpy.context.active_object
    disp_cut.scale = (disp_w, disp_h, 0.016)
    disp_cut.rotation_euler = (theta, 0, 0)
    disp_cut.data.materials.append(mats['body'])
    bpy.ops.object.transform_apply(scale=True, rotation=True)

    mod_d = wedge.modifiers.new(type="BOOLEAN", name="Cut_Display_Window")
    mod_d.operation = 'DIFFERENCE'
    mod_d.solver = 'EXACT'
    mod_d.object = disp_cut
    bpy.context.view_layer.objects.active = wedge
    bpy.ops.object.modifier_apply(modifier="Cut_Display_Window")
    bpy.data.objects.remove(disp_cut, do_unlink=True)

    # 4. Display Glass Panel (Recessed 0.8mm inside the aperture)
    screen_pos = to_world(disp_center_x, screen_y_loc, -0.0008)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=screen_pos)
    screen_obj = bpy.context.active_object
    screen_obj.name = "Combo_Active_Screen"
    screen_obj.scale = (disp_w - 0.0004, disp_h - 0.0004, 1.0)
    screen_obj.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    screen_obj.data.materials.append(mats['screen'])
    col.objects.link(screen_obj)

    # 5. Left Transparent Inspection Window (Blueprint ACPC-001: 32 x 50 mm)
    win_w = 0.032
    win_h = 0.050
    win_center_x = -0.060

    win_cut_pos = to_world(win_center_x, screen_y_loc, -0.005)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=win_cut_pos)
    win_cut = bpy.context.active_object
    win_cut.scale = (win_w, win_h, 0.016)
    win_cut.rotation_euler = (theta, 0, 0)
    win_cut.data.materials.append(mats['body'])
    bpy.ops.object.transform_apply(scale=True, rotation=True)

    mod_w = wedge.modifiers.new(type="BOOLEAN", name="Cut_Inspection_Window")
    mod_w.operation = 'DIFFERENCE'
    mod_w.solver = 'EXACT'
    mod_w.object = win_cut
    bpy.context.view_layer.objects.active = wedge
    bpy.ops.object.modifier_apply(modifier="Cut_Inspection_Window")
    bpy.data.objects.remove(win_cut, do_unlink=True)

    # Transparent Polycarbonate Lens Panel
    lens_pos = to_world(win_center_x, screen_y_loc, -0.0006)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=lens_pos)
    win_lens = bpy.context.active_object
    win_lens.name = "Inspection_Window_Lens"
    win_lens.scale = (win_w - 0.0004, win_h - 0.0004, 0.0016)
    win_lens.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    win_lens.data.materials.append(mats['glass'])
    col.objects.link(win_lens)

    # 6. Detailed High-End Compute Board under Left Transparent Window
    pcb_pos = to_world(win_center_x, screen_y_loc, -0.0065)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=pcb_pos)
    sys_pcb = bpy.context.active_object
    sys_pcb.name = "System_Control_PCB"
    sys_pcb.scale = (0.029, 0.046, 0.0016)
    sys_pcb.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    sys_pcb.data.materials.append(mats['pcb'])
    col.objects.link(sys_pcb)

    # Dual USB-A Metal Jack at Top of Compute Board
    usb_conn_pos = to_world(win_center_x, screen_y_loc + 0.014, -0.0040)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=usb_conn_pos)
    usb_conn = bpy.context.active_object
    usb_conn.name = "PCB_Dual_USB_Jack"
    usb_conn.scale = (0.010, 0.012, 0.0045)
    usb_conn.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    usb_conn.data.materials.append(mats['metal'])
    col.objects.link(usb_conn)

    # Micro-USB Port on Left Edge of Compute Board
    m_usb_pos = to_world(win_center_x - 0.011, screen_y_loc - 0.003, -0.0045)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=m_usb_pos)
    m_usb = bpy.context.active_object
    m_usb.name = "PCB_MicroUSB_Port"
    m_usb.scale = (0.0035, 0.0075, 0.0022)
    m_usb.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    m_usb.data.materials.append(mats['metal'])
    col.objects.link(m_usb)

    # Processor SoC IC (Square package with silver corner dot and pins)
    ic_pos = to_world(win_center_x + 0.001, screen_y_loc - 0.003, -0.0048)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=ic_pos)
    ic_chip = bpy.context.active_object
    ic_chip.name = "PCB_Processor_SoC"
    ic_chip.scale = (0.010, 0.010, 0.0015)
    ic_chip.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    ic_chip.data.materials.append(mats['ic'])
    col.objects.link(ic_chip)

    # Crystal Oscillator (Silver metal can with rounded ends)
    xtal_pos = to_world(win_center_x + 0.007, screen_y_loc - 0.014, -0.0048)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=xtal_pos)
    xtal = bpy.context.active_object
    xtal.name = "PCB_Crystal_Oscillator"
    xtal.scale = (0.004, 0.007, 0.0022)
    xtal.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    xtal.data.materials.append(mats['metal'])
    col.objects.link(xtal)

    # SMT Ceramic Capacitor bank
    for ci in range(3):
        cap_pos = to_world(win_center_x - 0.004 + ci * 0.003, screen_y_loc - 0.014, -0.0050)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=cap_pos)
        cap_smd = bpy.context.active_object
        cap_smd.name = f"PCB_SMD_Cap_{ci+1}"
        cap_smd.scale = (0.0016, 0.0022, 0.0010)
        cap_smd.rotation_euler = (theta, 0, 0)
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        cap_smd.data.materials.append(mats['metal'])
        col.objects.link(cap_smd)

    # SMD Activity LED on System PCB (Realistic component glow)
    smd_pos = to_world(win_center_x - 0.008, screen_y_loc + 0.008, -0.0045)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=smd_pos)
    smd_led = bpy.context.active_object
    smd_led.name = "PCB_SMD_LED"
    smd_led.scale = (0.0016, 0.0022, 0.0010)
    smd_led.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    smd_led.data.materials.append(mats['glyph_lit'])
    col.objects.link(smd_led)

    # 7. Hollow Out Interior
    inner_w = case_w - (2 * wall)
    inner_d = case_d - (2 * wall)
    inner_front_h = front_h - wall
    inner_rear_h = rear_h - wall

    inner_wedge = create_wedge_solid("Inner_Cutter", inner_w, inner_d, inner_front_h, inner_rear_h, col, mats['body'])
    inner_wedge.location = (0, 0, wall)

    mod_hollow = wedge.modifiers.new(type="BOOLEAN", name="Hollow_Out")
    mod_hollow.operation = 'DIFFERENCE'
    mod_hollow.solver = 'EXACT'
    mod_hollow.object = inner_wedge
    bpy.context.view_layer.objects.active = wedge
    bpy.ops.object.modifier_apply(modifier="Hollow_Out")
    bpy.data.objects.remove(inner_wedge, do_unlink=True)

    # 8. Top-Right L-Shaped Curved Glyph Matrix (20 segmented dashes)
    # Replicating media_1790210937702.png:
    # 8 top horizontal dashes, 3 corner curve dashes, 9 vertical dashes going down
    glyph_corner_x = disp_center_x + (disp_w / 2.0) + 0.009
    glyph_corner_y = screen_y_loc + (disp_h / 2.0) + 0.010
    corner_r = 0.013

    dash_w = 0.0020
    dash_l = 0.0056
    dash_pitch = 0.0038

    dashes_coords = []
    # 8 top horizontal dashes (moving left from corner arc)
    for i in range(8):
        dx = glyph_corner_x - corner_r - (7 - i) * dash_pitch
        dy = glyph_corner_y
        dashes_coords.append((dx, dy, 0.0))

    # 3 radial dashes in the corner arc
    for i in range(3):
        angle = math.radians(22.5 + i * 22.5)
        dx = glyph_corner_x - corner_r + corner_r * math.sin(angle)
        dy = glyph_corner_y - corner_r + corner_r * math.cos(angle)
        dashes_coords.append((dx, dy, -angle))

    # 9 vertical right dashes (moving down along right edge of screen)
    for i in range(9):
        dx = glyph_corner_x
        dy = glyph_corner_y - corner_r - (i + 1) * dash_pitch
        dashes_coords.append((dx, dy, -math.radians(90)))

    for idx, (gx, gy, rot_z) in enumerate(dashes_coords):
        dash_pos = to_world(gx, gy, -0.0003)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=dash_pos)
        dash = bpy.context.active_object
        dash.name = f"Glyph_Dash_{idx+1}"
        dash.scale = (dash_w, dash_l, 0.0006)

        dash_rot_mat = rot_face_matrix @ Matrix.Rotation(rot_z, 4, 'Z')
        dash.rotation_euler = dash_rot_mat.to_euler()
        bpy.ops.object.transform_apply(scale=True, rotation=True)

        # Lighting pattern matching media_1790210937702.png:
        # Dashes 0..4: lit white
        # Dash 5: Nothing Red accent
        # Dashes 6..16: lit white (all around corner and down the vertical column)
        # Dashes 17..19: dark off graphite at bottom
        if 0 <= idx <= 4:
            dash.data.materials.append(mats['glyph_lit'])
        elif idx == 5:
            dash.data.materials.append(mats['red'])
        elif 6 <= idx <= 16:
            dash.data.materials.append(mats['glyph_lit'])
        else:
            dash.data.materials.append(mats['glyph_off'])
        col.objects.link(dash)

    # 9. Lower-Right Perforated Speaker Grille (5x5 circular perforation matrix)
    speaker_center_x = disp_center_x + (disp_w / 2.0) - 0.005
    speaker_y_loc = screen_y_loc - (disp_h / 2.0) - 0.010
    hole_pitch = 0.0030
    hole_radius = 0.00095

    for r in range(5):
        for c in range(5):
            hx = speaker_center_x + (c - 2) * hole_pitch
            hy = speaker_y_loc + (r - 2) * hole_pitch
            h_pos = to_world(hx, hy, -0.003)

            bpy.ops.mesh.primitive_cylinder_add(
                radius=hole_radius,
                depth=0.008,
                location=h_pos
            )
            h_cut = bpy.context.active_object
            h_cut.rotation_euler = (theta, 0, 0)
            h_cut.data.materials.append(mats['body'])
            bpy.ops.object.transform_apply(scale=True, rotation=True)

            mod_h = wedge.modifiers.new(type="BOOLEAN", name=f"Hole_{r}_{c}")
            mod_h.operation = 'DIFFERENCE'
            mod_h.solver = 'EXACT'
            mod_h.object = h_cut
            bpy.context.view_layer.objects.active = wedge
            bpy.ops.object.modifier_apply(modifier=f"Hole_{r}_{c}")
            bpy.data.objects.remove(h_cut, do_unlink=True)

    # Circular Power LED (Right next to speaker grille)
    led_pos = to_world(speaker_center_x + 0.013, speaker_y_loc + 0.002, -0.0002)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.0013, # 2.6mm diameter
        depth=0.0020,
        location=led_pos
    )
    led = bpy.context.active_object
    led.name = "Combo_Power_LED"
    led.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    led.data.materials.append(mats['red'])
    col.objects.link(led)

    # 10. Four M3 Flush Counterbored Screws on Bezel Corners
    # Matching media_1790210937702.png:
    # Counterbore holes cut into faceplate, M3 socket head sits flush/recessed inside!
    screw_margin_x = (case_w / 2.0) - 0.009
    screw_margin_y = (case_d / 2.0) - 0.009
    corner_coords = [
        (-screw_margin_x, -screw_margin_y * cos_t),
        (+screw_margin_x, -screw_margin_y * cos_t),
        (-screw_margin_x, +screw_margin_y * cos_t),
        (+screw_margin_x, +screw_margin_y * cos_t),
    ]

    for idx, (sx, sy) in enumerate(corner_coords):
        # Counterbore cylindrical pocket cut 2.4 mm deep into faceplate
        cut_pos = to_world(sx, sy, -0.0012)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.0034, # 6.8mm diameter counterbore
            depth=0.0028,
            location=cut_pos
        )
        s_cut = bpy.context.active_object
        s_cut.rotation_euler = (theta, 0, 0)
        s_cut.data.materials.append(mats['body'])
        bpy.ops.object.transform_apply(scale=True, rotation=True)

        mod_s = wedge.modifiers.new(type="BOOLEAN", name=f"Screw_Hole_{idx}")
        mod_s.operation = 'DIFFERENCE'
        mod_s.solver = 'EXACT'
        mod_s.object = s_cut
        bpy.context.view_layer.objects.active = wedge
        bpy.ops.object.modifier_apply(modifier=f"Screw_Hole_{idx}")
        bpy.data.objects.remove(s_cut, do_unlink=True)

        # M3 socket screw sitting recessed inside counterbore (0.3mm below front face)
        create_m3_screw(f"M3_Corner_Screw_{idx+1}", cut_pos, (theta, 0, 0), col, mats['bolt'])

    # 11. Front Silkscreen Decal Plate (Directly below screen)
    silk_y_loc = screen_y_loc - (disp_h / 2.0) - 0.010
    silk_pos = to_world(disp_center_x, silk_y_loc, 0.00015)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=silk_pos)
    silk_obj = bpy.context.active_object
    silk_obj.name = "Combo_Bezel_Silkscreen"
    silk_obj.scale = (0.098, 0.018, 1.0) # Matches display width
    silk_obj.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    silk_obj.data.materials.append(mats['silkscreen'])
    silk_obj.visible_shadow = False # Completely prevents shadow boundary artifact
    col.objects.link(silk_obj)

    # 12. Right-Side USB Port Cutout
    usb_x = case_w / 2.0
    usb_y = 0.016
    usb_z = 0.011

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(usb_x, usb_y, usb_z))
    usb_cut = bpy.context.active_object
    usb_cut.scale = (0.012, 0.014, 0.007)
    usb_cut.data.materials.append(mats['body'])
    bpy.ops.object.transform_apply(scale=True)

    mod_u = wedge.modifiers.new(type="BOOLEAN", name="Cut_USB_Port")
    mod_u.operation = 'DIFFERENCE'
    mod_u.solver = 'EXACT'
    mod_u.object = usb_cut
    bpy.context.view_layer.objects.active = wedge
    bpy.ops.object.modifier_apply(modifier="Cut_USB_Port")
    bpy.data.objects.remove(usb_cut, do_unlink=True)

    # USB Plug & Curved Braided Cable
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(usb_x + 0.009, usb_y, usb_z))
    plug = bpy.context.active_object
    plug.name = "USB_Plug_Overmold"
    plug.scale = (0.018, 0.011, 0.0065)
    bpy.ops.object.transform_apply(scale=True)
    plug.data.materials.append(mats['body'])
    col.objects.link(plug)

    curve_data = bpy.data.curves.new('Cable_Curve', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.0028
    curve_data.bevel_resolution = 4
    polyline = curve_data.splines.new('BEZIER')
    polyline.bezier_points.add(2)
    p0, p1, p2 = polyline.bezier_points
    p0.co = Vector((usb_x + 0.018, usb_y, usb_z))
    p0.handle_right = Vector((usb_x + 0.040, usb_y, usb_z))
    p0.handle_left = Vector((usb_x + 0.012, usb_y, usb_z))
    p1.co = Vector((usb_x + 0.055, usb_y + 0.025, 0.003))
    p1.handle_left = Vector((usb_x + 0.050, usb_y + 0.012, 0.006))
    p1.handle_right = Vector((usb_x + 0.058, usb_y + 0.045, 0.002))
    p2.co = Vector((usb_x + 0.038, usb_y + 0.080, 0.002))
    p2.handle_left = Vector((usb_x + 0.050, usb_y + 0.065, 0.002))
    p2.handle_right = Vector((usb_x + 0.022, usb_y + 0.095, 0.002))

    cable_obj = bpy.data.objects.new('Braided_Cable', curve_data)
    cable_obj.data.materials.append(mats['cable'])
    col.objects.link(cable_obj)

    # 13. 4 Vibrant Orange Polymer Isolation Feet (Blueprint ACPC-001)
    foot_margin_x = (case_w / 2.0) - 0.014
    foot_margin_y = (case_d / 2.0) - 0.012
    foot_coords = [
        (-foot_margin_x, -foot_margin_y),
        (+foot_margin_x, -foot_margin_y),
        (-foot_margin_x, +foot_margin_y),
        (+foot_margin_x, +foot_margin_y),
    ]
    for idx, (fx, fy) in enumerate(foot_coords):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.0070,
            depth=0.0035,
            location=(fx, fy, -0.0017)
        )
        foot = bpy.context.active_object
        foot.name = f"Isolation_Foot_{idx+1}"
        foot.data.materials.append(mats['orange'])
        col.objects.link(foot)

    # 14. PHYSICAL INTERNAL HARDWARE & WIRING HARNESS
    # A. Arduino Uno R3 on Base Floor
    uno_x = 0.015
    uno_y = -0.005
    uno_z = wall + 0.003
    uno_stl = "/home/mahdi/Downloads/case_base.stl"
    if os.path.exists(uno_stl):
        bpy.ops.wm.stl_import(filepath=uno_stl)
        uno_obj = bpy.context.active_object
        uno_obj.name = "Internal_Arduino_Uno_R3"
        uno_obj.scale = (0.001, 0.001, 0.001)
        bpy.ops.object.transform_apply(scale=True)
        uno_obj.location = (uno_x - 0.035, uno_y, uno_z)
        uno_obj.data.materials.append(mats['pcb'])
        col.objects.link(uno_obj)

    # B. 4" TFT Display Electronics Assembly
    tft_stl = "/tmp/tft.stl"
    if os.path.exists(tft_stl):
        bpy.ops.wm.stl_import(filepath=tft_stl)
        tft_obj = bpy.context.active_object
        tft_obj.name = "Internal_TFT_4Inch_PCB"
        tft_obj.scale = (0.001, 0.001, 0.001)
        bpy.ops.object.transform_apply(scale=True)
        tft_obj.rotation_euler = (theta, 0, 0)
        tft_obj.location = (disp_center_x - 0.054, screen_pos.y - 0.016 * cos_t, screen_pos.z - 0.016 * sin_t)
        tft_obj.data.materials.append(mats['pcb'])
        col.objects.link(tft_obj)

    # C. 8-Conductor Flexible SPI Ribbon Cable (Color-Coded Jumper Wires)
    wire_types = ['red', 'black', 'blue', 'yellow', 'green', 'white', 'yellow', 'blue']
    for i, w_color in enumerate(wire_types):
        c_curve = bpy.data.curves.new(f'SPI_Wire_{i+1}', type='CURVE')
        c_curve.dimensions = '3D'
        c_curve.bevel_depth = 0.0006
        c_curve.bevel_resolution = 3
        poly = c_curve.splines.new('BEZIER')
        poly.bezier_points.add(2)
        p0, p1, p2 = poly.bezier_points

        w_start_x = uno_x - 0.015 + i * 0.0014
        p0.co = Vector((w_start_x, uno_y + 0.015, uno_z + 0.010))
        p0.handle_right = Vector((w_start_x, uno_y + 0.010, uno_z + 0.018))
        p0.handle_left = Vector((w_start_x, uno_y + 0.018, uno_z + 0.008))

        p1.co = Vector((w_start_x - 0.008, screen_pos.y - 0.018, uno_z + 0.016))
        p1.handle_left = Vector((w_start_x - 0.008, uno_y + 0.005, uno_z + 0.018))
        p1.handle_right = Vector((w_start_x - 0.008, screen_pos.y - 0.012, uno_z + 0.018))

        p2.co = Vector((disp_center_x - 0.040 + i * 0.0014, screen_pos.y - 0.008, screen_pos.z - 0.008))
        p2.handle_left = Vector((disp_center_x - 0.040 + i * 0.0014, screen_pos.y - 0.014, screen_pos.z - 0.012))
        p2.handle_right = Vector((disp_center_x - 0.040 + i * 0.0014, screen_pos.y - 0.006, screen_pos.z - 0.008))

        wire_obj = bpy.data.objects.new(f'SPI_Wire_{i+1}', c_curve)
        wire_obj.data.materials.append(mats['wires'][w_color])
        col.objects.link(wire_obj)

    # D. 4-Wire Interconnect Cable between System Control PCB and Arduino
    sys_wire_colors = ['red', 'black', 'white', 'green']
    for i, w_color in enumerate(sys_wire_colors):
        c_curve = bpy.data.curves.new(f'Sys_Wire_{i+1}', type='CURVE')
        c_curve.dimensions = '3D'
        c_curve.bevel_depth = 0.0006
        c_curve.bevel_resolution = 3
        poly = c_curve.splines.new('BEZIER')
        poly.bezier_points.add(2)
        p0, p1, p2 = poly.bezier_points

        p0.co = Vector((win_center_x + 0.010, screen_y_loc - 0.015, pcb_pos.z + 0.001))
        p0.handle_right = Vector((win_center_x + 0.020, screen_y_loc - 0.020, uno_z + 0.006))
        p0.handle_left = Vector((win_center_x + 0.005, screen_y_loc - 0.010, pcb_pos.z + 0.001))

        p1.co = Vector((-0.025, -0.012, uno_z + 0.006))
        p1.handle_left = Vector((-0.035, -0.016, uno_z + 0.006))
        p1.handle_right = Vector((-0.015, -0.008, uno_z + 0.006))

        p2.co = Vector((uno_x - 0.025, uno_y - 0.015 + i * 0.0018, uno_z + 0.010))
        p2.handle_left = Vector((uno_x - 0.030, uno_y - 0.015 + i * 0.0018, uno_z + 0.008))
        p2.handle_right = Vector((uno_x - 0.020, uno_y - 0.015 + i * 0.0018, uno_z + 0.010))

        sys_wire_obj = bpy.data.objects.new(f'Sys_Wire_{i+1}', c_curve)
        sys_wire_obj.data.materials.append(mats['wires'][w_color])
        col.objects.link(sys_wire_obj)

    # 15. Detachable Bottom Service Base Plate
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, wall / 2.0))
    base_plate = bpy.context.active_object
    base_plate.name = "Pulse_Combo_Base_Plate"
    base_plate.scale = (case_w - 0.001, case_d - 0.001, wall)
    bpy.ops.object.transform_apply(scale=True)
    base_plate.data.materials.append(mats['body'])
    col.objects.link(base_plate)

    print("Open-Frame Arduino-Pi Combo Console constructed successfully.")
    return wedge, base_plate

# ---------------------------------------------------------
# 5. STUDIO LIGHTING & CYCLES GPU RENDER
# ---------------------------------------------------------
def setup_studio_and_render():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'

    # Configure Cycles GPU compute preferences (OptiX strictly on RTX GPU, CPU disabled)
    try:
        cycles_pref = bpy.context.preferences.addons['cycles'].preferences
        cycles_pref.compute_device_type = 'OPTIX'
        cycles_pref.get_devices_for_type('OPTIX')
        for d in cycles_pref.devices:
            if d.type == 'CPU':
                d.use = False
            elif 'RTX' in d.name or d.type == 'OPTIX':
                d.use = True
            print(f"Cycles device: {d.name} ({d.type}) -> use={d.use}")
    except Exception as e:
        print(f"Error configuring OptiX GPU: {e}")

    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPTIX'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'

    if scene.world is None:
        scene.world = bpy.data.worlds.new("Combo_World")
    scene.world.use_nodes = True
    bg_node = scene.world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.010, 0.012, 0.016, 1.0)
        bg_node.inputs['Strength'].default_value = 0.4

    # Warm Natural Oak Wood Desk Surface (Exact match to media_1790210937702.png)
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, 0, -0.0035))
    desk = bpy.context.active_object
    desk.name = "Wooden_Desk"

    mat_desk = bpy.data.materials.new("Wood_Desk_Procedural")
    mat_desk.use_nodes = True
    d_tree = mat_desk.node_tree
    d_tree.nodes.clear()

    d_out = d_tree.nodes.new(type='ShaderNodeOutputMaterial')
    d_bsdf = d_tree.nodes.new(type='ShaderNodeBsdfPrincipled')

    d_coord = d_tree.nodes.new(type='ShaderNodeTexCoord')
    d_map = d_tree.nodes.new(type='ShaderNodeMapping')
    d_map.inputs['Scale'].default_value = (0.4, 0.15, 1.0)

    d_wave = d_tree.nodes.new(type='ShaderNodeTexWave')
    d_wave.wave_type = 'BANDS'
    d_wave.bands_direction = 'X'
    d_wave.inputs['Scale'].default_value = 0.8
    d_wave.inputs['Distortion'].default_value = 1.8
    d_wave.inputs['Detail'].default_value = 4.0

    d_ramp = d_tree.nodes.new(type='ShaderNodeValToRGB')
    d_ramp.color_ramp.elements[0].position = 0.10
    d_ramp.color_ramp.elements[0].color = (0.35, 0.22, 0.12, 1.0) # Warm oak tone
    d_ramp.color_ramp.elements[1].position = 0.85
    d_ramp.color_ramp.elements[1].color = (0.55, 0.38, 0.24, 1.0) # Golden wood highlight

    d_bump = d_tree.nodes.new(type='ShaderNodeBump')
    d_bump.inputs['Strength'].default_value = 0.05

    d_tree.links.new(d_coord.outputs['Object'], d_map.inputs['Vector'])
    d_tree.links.new(d_map.outputs['Vector'], d_wave.inputs['Vector'])
    d_tree.links.new(d_wave.outputs['Color'], d_ramp.inputs['Fac'])
    d_tree.links.new(d_ramp.outputs['Color'], d_bsdf.inputs['Base Color'])
    d_tree.links.new(d_wave.outputs['Color'], d_bump.inputs['Height'])
    d_tree.links.new(d_bump.outputs['Normal'], d_bsdf.inputs['Normal'])

    d_bsdf.inputs['Roughness'].default_value = 0.45
    d_tree.links.new(d_bsdf.outputs['BSDF'], d_out.inputs['Surface'])
    desk.data.materials.append(mat_desk)

    # Mechanical Keyboard in Left Foreground (Matching hero photo media_1790210937702.png)
    mat_kb = bpy.data.materials.new("Keyboard_Chassis_Mat")
    mat_kb.use_nodes = True
    b_kb = mat_kb.node_tree.nodes.get("Principled BSDF")
    if b_kb:
        b_kb.inputs['Base Color'].default_value = (0.010, 0.010, 0.012, 1.0)
        b_kb.inputs['Roughness'].default_value = 0.65

    mat_cap = bpy.data.materials.new("Keycap_Mat")
    mat_cap.use_nodes = True
    b_cap = mat_cap.node_tree.nodes.get("Principled BSDF")
    if b_cap:
        b_cap.inputs['Base Color'].default_value = (0.018, 0.019, 0.022, 1.0)
        b_cap.inputs['Roughness'].default_value = 0.45

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.145, -0.090, 0.006))
    kb = bpy.context.active_object
    kb.name = "Keyboard_Chassis"
    kb.scale = (0.090, 0.130, 0.014)
    kb.rotation_euler = (0, 0, math.radians(14))
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    kb.data.materials.append(mat_kb)

    # Keycaps
    kb_rot = math.radians(14)
    cos_kb = math.cos(kb_rot)
    sin_kb = math.sin(kb_rot)

    for row in range(3):
        for col_idx in range(4):
            kx_local = (col_idx - 1.5) * 0.018
            ky_local = (row - 1.0) * 0.018
            kx = -0.145 + kx_local * cos_kb - ky_local * sin_kb
            ky = -0.090 + kx_local * sin_kb + ky_local * cos_kb

            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(kx, ky, 0.016))
            cap = bpy.context.active_object
            cap.name = f"Keycap_{row}_{col_idx}"
            cap.scale = (0.016, 0.016, 0.007)
            cap.rotation_euler = (0, 0, kb_rot)
            bpy.ops.object.transform_apply(scale=True, rotation=True)
            cap.data.materials.append(mat_cap)

    # Camera matching exact perspective & framing of hero photo media_1790210937702.png
    cam_data = bpy.data.cameras.new("Reference_Match_Cam")
    cam_data.lens = 50
    cam_obj = bpy.data.objects.new("Reference_Match_Cam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = (-0.075, -0.315, 0.170)
    cam_obj.rotation_euler = (math.radians(63.5), 0, math.radians(-15.5))

    # Natural Window & Studio Lighting (Soft directional daylight from left)
    light_win = bpy.data.lights.new(name="Window_Soft_Light", type='AREA')
    light_win.energy = 5.2
    light_win.size = 1.4
    light_win.color = (0.95, 0.98, 1.0)
    l1 = bpy.data.objects.new("Window_Soft_Light", light_win)
    l1.location = (-0.55, -0.05, 0.40)
    l1.rotation_euler = (math.radians(50), math.radians(-18), math.radians(-65))
    scene.collection.objects.link(l1)

    light_room = bpy.data.lights.new(name="Warm_Ambient", type='AREA')
    light_room.energy = 1.8
    light_room.size = 1.0
    light_room.color = (1.0, 0.94, 0.88)
    l2 = bpy.data.objects.new("Warm_Ambient", light_room)
    l2.location = (0.40, -0.10, 0.22)
    scene.collection.objects.link(l2)

    light_rim = bpy.data.lights.new(name="Top_Rim", type='AREA')
    light_rim.energy = 3.4
    light_rim.size = 0.8
    light_rim.color = (1.0, 1.0, 1.0)
    l3 = bpy.data.objects.new("Top_Rim", light_rim)
    l3.location = (0.0, 0.25, 0.32)
    scene.collection.objects.link(l3)

    # Render Hero Showcase
    render_hero = os.path.join(OUTPUT_DIR, "nothing_pulse_combo_hero.png")
    scene.render.filepath = render_hero
    bpy.ops.render.render(write_still=True)
    print(f"Rendered Open-Frame Arduino-Pi Combo Hero Image: {render_hero}")

# ---------------------------------------------------------
# 6. STL & ASSET EXPORTS
# ---------------------------------------------------------
def export_assets(body, base_plate):
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    body_stl = os.path.join(OUTPUT_DIR, "Nothing_Pulse_Combo_Chassis.stl")
    bpy.ops.wm.stl_export(filepath=body_stl, export_selected_objects=True)
    print(f"Exported Combo Chassis STL: {body_stl}")

    bpy.ops.object.select_all(action='DESELECT')
    base_plate.select_set(True)
    bpy.context.view_layer.objects.active = base_plate
    plate_stl = os.path.join(OUTPUT_DIR, "Nothing_Pulse_Combo_Base.stl")
    bpy.ops.wm.stl_export(filepath=plate_stl, export_selected_objects=True)
    print(f"Exported Combo Base Plate STL: {plate_stl}")

    blend_path = os.path.join(OUTPUT_DIR, "Nothing_Pulse_Combo.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved blend file: {blend_path}")

if __name__ == "__main__":
    body, base_plate = build_combo_console()
    setup_studio_and_render()
    export_assets(body, base_plate)
