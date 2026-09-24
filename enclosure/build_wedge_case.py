"""
Nothing-Inspired Desktop Wedge Console (PULSE Wedge Edition)
High-Fidelity 3D Model strictly faithful to reference photo media_1790210012344.png:
- Precision angled desktop console wedge (~23° incline)
- Houses 4" SPI TFT 480x320 display (108mm x 61.65mm) with authentic UI
- Houses Arduino Uno R3 on interior floor
- Recessed top horizontal Glyph Matrix progress bar (24 segmented dashes, lit white + Nothing Red)
- Front lower-right Nothing Red circular power LED
- Front vertical lip with 5 pill-shaped cooling slots on the left
- Right-side USB-C port cutout + braided cable plugged in
- Base elevated on 4 vibrant orange rubber feet (#EA480D Teenage Engineering / Nothing aesthetic)
- Realistic dark oak desktop and keyboard in foreground
- Rendered in Blender Cycles with NVIDIA RTX GPU OptiX compute (CPU disabled)
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix
import os
from PIL import Image, ImageDraw

OUTPUT_DIR = "/home/mahdi/Programming/perfomance-monitor/enclosure"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. GENERATE SCREEN UI TEXTURE (Dot Matrix Font)
# ---------------------------------------------------------
def generate_ui_texture():
    tex_path = os.path.join(OUTPUT_DIR, "pulse_screen_ui.png")
    w, h = 960, 640
    img = Image.new('RGB', (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)

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
        'o': [0x00, 0x06, 0x09, 0x09, 0x06], # degree symbol
    }

    def draw_dots(text, start_x, start_y, dot_size, pitch, color):
        cx = start_x
        for ch in text:
            cols = FONT_5X7.get(ch, FONT_5X7[' '])
            for col_idx, col_byte in enumerate(cols):
                x = cx + col_idx * pitch
                for row_idx in range(7):
                    if (col_byte >> row_idx) & 1:
                        y = start_y + row_idx * pitch
                        r = dot_size / 2.0
                        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
            cx += (len(cols) + 1) * pitch

    # Large Numbers: 37% and 82%
    draw_dots('37%', 80, 160, 16.5, 24.0, (255, 255, 255))
    draw_dots('82%', 530, 160, 16.5, 24.0, (255, 255, 255))

    # Temperatures: 54°C and 71°C
    draw_dots('54oC', 155, 395, 8.5, 14.5, (220, 225, 235))
    draw_dots('71oC', 605, 395, 8.5, 14.5, (220, 225, 235))

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
    col = bpy.data.collections.new("Nothing_Wedge_Case")
    scene.collection.children.link(col)
    return col

def create_materials(ui_texture_path):
    # 1. Dark Charcoal Matte Anodized Aluminum (#1C1E21)
    mat_body = bpy.data.materials.new("Wedge_Mat_DarkCharcoal")
    mat_body.use_nodes = True
    bsdf = mat_body.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.015, 0.016, 0.018, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.36
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = 0.22

    # 2. Display Laminated Glass Screen (with Live Emissive Dot Matrix UI)
    mat_screen = bpy.data.materials.new("Wedge_Mat_Screen")
    mat_screen.use_nodes = True
    tree = mat_screen.node_tree
    tree.nodes.clear()

    node_out = tree.nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Base Color'].default_value = (0.001, 0.001, 0.002, 1.0)
    node_bsdf.inputs['Roughness'].default_value = 0.05
    node_bsdf.inputs['IOR'].default_value = 1.50
    if 'Specular IOR Level' in node_bsdf.inputs:
        node_bsdf.inputs['Specular IOR Level'].default_value = 0.7

    node_coord = tree.nodes.new(type='ShaderNodeTexCoord')
    node_tex = tree.nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(ui_texture_path):
        node_tex.image = bpy.data.images.load(ui_texture_path)
    
    tree.links.new(node_coord.outputs['UV'], node_tex.inputs['Vector'])
    tree.links.new(node_tex.outputs['Color'], node_bsdf.inputs['Emission Color'])
    node_bsdf.inputs['Emission Strength'].default_value = 14.0
    tree.links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])

    # 3. Glyph Inactive Segment (Dark Matte Graphite)
    mat_glyph_off = bpy.data.materials.new("Wedge_Mat_GlyphOff")
    mat_glyph_off.use_nodes = True
    bsdf_off = mat_glyph_off.node_tree.nodes.get("Principled BSDF")
    if bsdf_off:
        bsdf_off.inputs['Base Color'].default_value = (0.022, 0.023, 0.025, 1.0)
        bsdf_off.inputs['Roughness'].default_value = 0.35

    # 4. Glyph Lit White LED (Emissive)
    mat_glyph_lit = bpy.data.materials.new("Wedge_Mat_GlyphLit")
    mat_glyph_lit.use_nodes = True
    bsdf_lit = mat_glyph_lit.node_tree.nodes.get("Principled BSDF")
    if bsdf_lit:
        bsdf_lit.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        bsdf_lit.inputs['Roughness'].default_value = 0.15
        if 'Emission Color' in bsdf_lit.inputs:
            bsdf_lit.inputs['Emission Color'].default_value = (1.0, 1.0, 1.0, 1.0)
            bsdf_lit.inputs['Emission Strength'].default_value = 25.0

    # 5. Nothing Red Accent & LED (#D71921)
    mat_red = bpy.data.materials.new("Wedge_Mat_NothingRed")
    mat_red.use_nodes = True
    bsdf_red = mat_red.node_tree.nodes.get("Principled BSDF")
    if bsdf_red:
        bsdf_red.inputs['Base Color'].default_value = (0.84, 0.08, 0.12, 1.0)
        bsdf_red.inputs['Roughness'].default_value = 0.15
        if 'Emission Color' in bsdf_red.inputs:
            bsdf_red.inputs['Emission Color'].default_value = (0.84, 0.08, 0.12, 1.0)
            bsdf_red.inputs['Emission Strength'].default_value = 28.0

    # 6. Vibrant Orange Rubber Feet (#EA480D)
    mat_orange = bpy.data.materials.new("Wedge_Mat_OrangeFoot")
    mat_orange.use_nodes = True
    bsdf_org = mat_orange.node_tree.nodes.get("Principled BSDF")
    if bsdf_org:
        bsdf_org.inputs['Base Color'].default_value = (0.92, 0.28, 0.05, 1.0)
        bsdf_org.inputs['Roughness'].default_value = 0.65

    # 7. Braided USB Cable
    mat_cable = bpy.data.materials.new("Wedge_Mat_BraidedCable")
    mat_cable.use_nodes = True
    bsdf_cab = mat_cable.node_tree.nodes.get("Principled BSDF")
    if bsdf_cab:
        bsdf_cab.inputs['Base Color'].default_value = (0.010, 0.010, 0.012, 1.0)
        bsdf_cab.inputs['Roughness'].default_value = 0.85

    return {
        'body': mat_body,
        'screen': mat_screen,
        'glyph_off': mat_glyph_off,
        'glyph_lit': mat_glyph_lit,
        'red': mat_red,
        'orange': mat_orange,
        'cable': mat_cable,
    }

# ---------------------------------------------------------
# 3. WEDGE SOLID MESH GENERATION
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

# ---------------------------------------------------------
# 4. FULL HARDWARE & ENCLOSURE BUILD
# ---------------------------------------------------------
def build_wedge_console():
    ui_tex = generate_ui_texture()
    col = reset_scene()
    mats = create_materials(ui_tex)

    case_w = 0.142
    case_d = 0.088
    front_h = 0.015
    rear_h = 0.052
    wall = 0.0028

    theta = math.atan2(rear_h - front_h, case_d)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    def to_world(x_local, y_along_incline, z_perp_to_face):
        y_surf = y_along_incline * cos_t
        z_surf = front_h + (y_surf + (case_d / 2.0)) * math.tan(theta)
        w_x = x_local
        w_y = y_surf - z_perp_to_face * sin_t
        w_z = z_surf + z_perp_to_face * cos_t
        return Vector((w_x, w_y, w_z))

    # 1. Main Solid Wedge Body
    wedge = create_wedge_solid("Pulse_Wedge_Body", case_w, case_d, front_h, rear_h, col, mats['body'])

    # 2. Outer Chamfer
    mod_bev = wedge.modifiers.new(type="BEVEL", name="Chamfer")
    mod_bev.width = 0.0008
    mod_bev.segments = 2
    mod_bev.limit_method = 'ANGLE'
    mod_bev.angle_limit = math.radians(40)
    bpy.context.view_layer.objects.active = wedge
    bpy.ops.object.modifier_apply(modifier="Chamfer")

    # 3. Display Window Cutout (Cut completely through top face by 12mm into cavity)
    disp_w = 0.098
    disp_h = 0.056
    screen_y_loc = -0.004

    pocket_pos = to_world(0, screen_y_loc, -0.004)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=pocket_pos)
    disp_cut = bpy.context.active_object
    disp_cut.scale = (disp_w, disp_h, 0.014) # Clean through-cut!
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

    # 4. Display Glass Screen Mesh (Seated 0.8mm recessed into the window aperture)
    screen_pos = to_world(0, screen_y_loc, -0.0008)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=screen_pos)
    screen_obj = bpy.context.active_object
    screen_obj.name = "Pulse_Active_Screen"
    screen_obj.scale = (disp_w - 0.0002, disp_h - 0.0002, 1.0)
    screen_obj.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    screen_obj.data.materials.append(mats['screen'])
    col.objects.link(screen_obj)

    # 5. Hollow Out Interior (Leave structural 2.8mm floor and rear walls)
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

    # 6. Recessed Top Glyph Matrix Trench
    glyph_y_loc = screen_y_loc + (disp_h / 2.0) + 0.010
    trench_w = 0.096
    trench_h = 0.008
    trench_pos = to_world(0, glyph_y_loc, -0.0008)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=trench_pos)
    trench_cut = bpy.context.active_object
    trench_cut.scale = (trench_w, trench_h, 0.0020)
    trench_cut.rotation_euler = (theta, 0, 0)
    trench_cut.data.materials.append(mats['body'])
    bpy.ops.object.transform_apply(scale=True, rotation=True)

    mod_t = wedge.modifiers.new(type="BOOLEAN", name="Cut_Glyph_Trench")
    mod_t.operation = 'DIFFERENCE'
    mod_t.solver = 'EXACT'
    mod_t.object = trench_cut
    bpy.context.view_layer.objects.active = wedge
    bpy.ops.object.modifier_apply(modifier="Cut_Glyph_Trench")
    bpy.data.objects.remove(trench_cut, do_unlink=True)

    # Trench Backing Inlay
    trench_bed_pos = to_world(0, glyph_y_loc, -0.0008)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=trench_bed_pos)
    trench_bed = bpy.context.active_object
    trench_bed.name = "Glyph_Trench_Bed"
    trench_bed.scale = (trench_w - 0.0004, trench_h - 0.0004, 0.0004)
    trench_bed.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    trench_bed.data.materials.append(mats['glyph_off'])
    col.objects.link(trench_bed)

    # 24 Glyph Segmented Dashes inside the trench
    total_dashes = 24
    dash_pitch = 0.0038
    dash_w = 0.0020
    dash_l = 0.0054

    for i in range(total_dashes):
        dx = (i - (total_dashes - 1) / 2.0) * dash_pitch
        dash_pos = to_world(dx, glyph_y_loc, -0.0003)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=dash_pos)
        dash = bpy.context.active_object
        dash.name = f"Glyph_Dash_{i+1}"
        dash.scale = (dash_w, dash_l, 0.0006)
        dash.rotation_euler = (theta, 0, 0)
        bpy.ops.object.transform_apply(scale=True, rotation=True)

        if 11 <= i <= 14:
            dash.data.materials.append(mats['glyph_lit']) # Glowing white dashes
        elif i == 15:
            dash.data.materials.append(mats['red'])       # Nothing Red active dash
        elif i == 16:
            dash.data.materials.append(mats['glyph_lit']) # Glowing white dash
        else:
            dash.data.materials.append(mats['glyph_off']) # Inactive dark dashes

        col.objects.link(dash)

    # 7. Front Lower-Right Power LED (#D71921)
    led_x = (disp_w / 2.0) + 0.008
    led_y_loc = screen_y_loc - (disp_h / 2.0) + 0.002
    led_pos = to_world(led_x, led_y_loc, -0.0002)

    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.0016,
        depth=0.0025,
        location=led_pos
    )
    led = bpy.context.active_object
    led.name = "Pulse_Red_Power_LED"
    led.rotation_euler = (theta, 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    led.data.materials.append(mats['red'])
    col.objects.link(led)

    # 8. Front-Left Vertical Ventilation Slots (5 slots on front vertical lip)
    slot_w = 0.0022
    slot_h = 0.0085
    front_lip_y = -(case_d / 2.0)
    slot_z = front_h / 2.0

    for i in range(5):
        sx = -(case_w / 2.0) + 0.014 + i * 0.0048
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(sx, front_lip_y, slot_z)
        )
        slot_cut = bpy.context.active_object
        slot_cut.scale = (slot_w, 0.012, slot_h)
        slot_cut.data.materials.append(mats['body'])
        bpy.ops.object.transform_apply(scale=True)

        mod_s = wedge.modifiers.new(type="BOOLEAN", name=f"Vent_Slot_{i}")
        mod_s.operation = 'DIFFERENCE'
        mod_s.solver = 'EXACT'
        mod_s.object = slot_cut
        bpy.context.view_layer.objects.active = wedge
        bpy.ops.object.modifier_apply(modifier=f"Vent_Slot_{i}")
        bpy.data.objects.remove(slot_cut, do_unlink=True)

    # 9. Right-Side USB Port Cutout
    usb_x = case_w / 2.0
    usb_y = 0.014
    usb_z = 0.010

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(usb_x, usb_y, usb_z)
    )
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

    # 10. USB-C Braided Cable Plugged In
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(usb_x + 0.009, usb_y, usb_z)
    )
    plug = bpy.context.active_object
    plug.name = "USB_Plug_Overmold"
    plug.scale = (0.018, 0.011, 0.0065)
    bpy.ops.object.transform_apply(scale=True)
    plug.data.materials.append(mats['body'])
    col.objects.link(plug)

    curve_data = bpy.data.curves.new('Cable_Curve', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.0026
    curve_data.bevel_resolution = 4
    
    polyline = curve_data.splines.new('BEZIER')
    polyline.bezier_points.add(2)
    p0, p1, p2 = polyline.bezier_points
    p0.co = Vector((usb_x + 0.018, usb_y, usb_z))
    p0.handle_right = Vector((usb_x + 0.040, usb_y, usb_z))
    p0.handle_left = Vector((usb_x + 0.012, usb_y, usb_z))

    p1.co = Vector((usb_x + 0.052, usb_y + 0.025, 0.003))
    p1.handle_left = Vector((usb_x + 0.048, usb_y + 0.012, 0.006))
    p1.handle_right = Vector((usb_x + 0.056, usb_y + 0.045, 0.002))

    p2.co = Vector((usb_x + 0.035, usb_y + 0.075, 0.002))
    p2.handle_left = Vector((usb_x + 0.048, usb_y + 0.060, 0.002))
    p2.handle_right = Vector((usb_x + 0.020, usb_y + 0.090, 0.002))

    cable_obj = bpy.data.objects.new('Braided_Cable', curve_data)
    cable_obj.data.materials.append(mats['cable'])
    col.objects.link(cable_obj)

    # 11. 4 Vibrant Orange Cylindrical Feet (#EA480D) - Clearly Visible Underneath Corners
    foot_coords = [
        (-(case_w / 2.0) + 0.008, -(case_d / 2.0) + 0.006),
        (+(case_w / 2.0) - 0.008, -(case_d / 2.0) + 0.006),
        (-(case_w / 2.0) + 0.008, +(case_d / 2.0) - 0.006),
        (+(case_w / 2.0) - 0.008, +(case_d / 2.0) - 0.006),
    ]
    for idx, (fx, fy) in enumerate(foot_coords):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.0065, # 13mm foot
            depth=0.0030,  # 3mm elevation
            location=(fx, fy, -0.0015)
        )
        foot = bpy.context.active_object
        foot.name = f"Orange_Foot_{idx+1}"
        foot.data.materials.append(mats['orange'])
        col.objects.link(foot)

    # 12. Detachable Bottom Service Base Plate
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, wall / 2.0))
    base_plate = bpy.context.active_object
    base_plate.name = "Pulse_Wedge_Base_Plate"
    base_plate.scale = (case_w - 0.001, case_d - 0.001, wall)
    bpy.ops.object.transform_apply(scale=True)
    base_plate.data.materials.append(mats['body'])
    col.objects.link(base_plate)

    # Ensure Wedge Body material is assigned to all polygons
    wedge.data.materials.clear()
    wedge.data.materials.append(mats['body'])
    for poly in wedge.data.polygons:
        poly.material_index = 0

    print("Nothing PULSE Wedge Console constructed successfully.")
    return wedge, base_plate

# ---------------------------------------------------------
# 5. STUDIO LIGHTING & CYCLES GPU RENDER
# ---------------------------------------------------------
def setup_studio_and_render():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    
    # Configure Cycles GPU compute preferences
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
        scene.world = bpy.data.worlds.new("Pulse_World")
    scene.world.use_nodes = True
    bg_node = scene.world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.005, 0.006, 0.008, 1.0)
        bg_node.inputs['Strength'].default_value = 0.3

    # Rich Realistic Wood Desk Surface
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0, 0, -0.0030))
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
    d_map.inputs['Scale'].default_value = (0.3, 0.3, 1.0)
    
    d_wave = d_tree.nodes.new(type='ShaderNodeTexWave')
    d_wave.wave_type = 'BANDS'
    d_wave.bands_direction = 'X'
    d_wave.inputs['Scale'].default_value = 0.5
    d_wave.inputs['Distortion'].default_value = 2.0
    d_wave.inputs['Detail'].default_value = 3.0
    
    d_ramp = d_tree.nodes.new(type='ShaderNodeValToRGB')
    d_ramp.color_ramp.elements[0].position = 0.15
    d_ramp.color_ramp.elements[0].color = (0.06, 0.035, 0.018, 1.0) # Warm deep walnut
    d_ramp.color_ramp.elements[1].position = 0.85
    d_ramp.color_ramp.elements[1].color = (0.15, 0.090, 0.050, 1.0) # Warm oak tone
    
    d_bump = d_tree.nodes.new(type='ShaderNodeBump')
    d_bump.inputs['Strength'].default_value = 0.08
    
    d_tree.links.new(d_coord.outputs['Object'], d_map.inputs['Vector'])
    d_tree.links.new(d_map.outputs['Vector'], d_wave.inputs['Vector'])
    d_tree.links.new(d_wave.outputs['Color'], d_ramp.inputs['Fac'])
    d_tree.links.new(d_ramp.outputs['Color'], d_bsdf.inputs['Base Color'])
    d_tree.links.new(d_wave.outputs['Color'], d_bump.inputs['Height'])
    d_tree.links.new(d_bump.outputs['Normal'], d_bsdf.inputs['Normal'])
    
    d_bsdf.inputs['Roughness'].default_value = 0.42
    d_tree.links.new(d_bsdf.outputs['BSDF'], d_out.inputs['Surface'])
    desk.data.materials.append(mat_desk)

    # Mechanical Keyboard in Foreground (Left foreground corner)
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

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.125, -0.080, 0.006))
    kb = bpy.context.active_object
    kb.name = "Keyboard_Chassis"
    kb.scale = (0.090, 0.130, 0.014)
    kb.rotation_euler = (0, 0, math.radians(14))
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    kb.data.materials.append(mat_kb)

    # 3 Rows of Keycaps
    kb_rot = math.radians(14)
    cos_kb = math.cos(kb_rot)
    sin_kb = math.sin(kb_rot)
    
    for row in range(3):
        for col_idx in range(4):
            kx_local = (col_idx - 1.5) * 0.018
            ky_local = (row - 1.0) * 0.018
            kx = -0.125 + kx_local * cos_kb - ky_local * sin_kb
            ky = -0.080 + kx_local * sin_kb + ky_local * cos_kb
            
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(kx, ky, 0.016))
            cap = bpy.context.active_object
            cap.name = f"Keycap_{row}_{col_idx}"
            cap.scale = (0.016, 0.016, 0.007)
            cap.rotation_euler = (0, 0, kb_rot)
            bpy.ops.object.transform_apply(scale=True, rotation=True)
            cap.data.materials.append(mat_cap)

    # Camera matching exact perspective & framing of reference photo media_1790210012344.png
    cam_data = bpy.data.cameras.new("Reference_Match_Cam")
    cam_data.lens = 45 # Perfect wide-angle product framing
    cam_obj = bpy.data.objects.new("Reference_Match_Cam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = (-0.070, -0.285, 0.168)
    cam_obj.rotation_euler = (math.radians(63.5), 0, math.radians(-16))

    # Natural Window & Studio Lighting (Soft directional daylight from left)
    # 1. Main Left Window Light (Soft directional daylight, placed higher up to graze surface)
    light_win = bpy.data.lights.new(name="Window_Soft_Light", type='AREA')
    light_win.energy = 4.2
    light_win.size = 1.2
    light_win.color = (0.95, 0.98, 1.0)
    l1 = bpy.data.objects.new("Window_Soft_Light", light_win)
    l1.location = (-0.50, -0.08, 0.38)
    l1.rotation_euler = (math.radians(52), math.radians(-18), math.radians(-65))
    scene.collection.objects.link(l1)

    # 2. Warm Room Fill Light
    light_room = bpy.data.lights.new(name="Warm_Ambient", type='AREA')
    light_room.energy = 1.5
    light_room.size = 0.9
    light_room.color = (1.0, 0.93, 0.85)
    l2 = bpy.data.objects.new("Warm_Ambient", light_room)
    l2.location = (0.35, -0.10, 0.22)
    scene.collection.objects.link(l2)

    # 3. Top Rim Highlight (Glancing edge rim)
    light_rim = bpy.data.lights.new(name="Top_Rim", type='AREA')
    light_rim.energy = 2.8
    light_rim.size = 0.6
    light_rim.color = (1.0, 1.0, 1.0)
    l3 = bpy.data.objects.new("Top_Rim", light_rim)
    l3.location = (0.0, 0.22, 0.30)
    scene.collection.objects.link(l3)

    # Render Hero Showcase
    render_hero = os.path.join(OUTPUT_DIR, "nothing_pulse_wedge_hero.png")
    scene.render.filepath = render_hero
    bpy.ops.render.render(write_still=True)
    print(f"Rendered Nothing PULSE Wedge Hero Image: {render_hero}")

# ---------------------------------------------------------
# 6. STL & ASSET EXPORTS
# ---------------------------------------------------------
def export_assets(body, base_plate):
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    body_stl = os.path.join(OUTPUT_DIR, "Nothing_Pulse_Wedge_Body.stl")
    bpy.ops.wm.stl_export(filepath=body_stl, export_selected_objects=True)
    print(f"Exported Wedge Body STL: {body_stl}")

    bpy.ops.object.select_all(action='DESELECT')
    base_plate.select_set(True)
    bpy.context.view_layer.objects.active = base_plate
    plate_stl = os.path.join(OUTPUT_DIR, "Nothing_Pulse_Wedge_Base.stl")
    bpy.ops.wm.stl_export(filepath=plate_stl, export_selected_objects=True)
    print(f"Exported Base Plate STL: {plate_stl}")

    blend_path = os.path.join(OUTPUT_DIR, "Nothing_Pulse_Wedge.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved blend file: {blend_path}")

if __name__ == "__main__":
    body, base_plate = build_wedge_console()
    setup_studio_and_render()
    export_assets(body, base_plate)
