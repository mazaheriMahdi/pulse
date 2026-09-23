import bpy
import math
import os

output_dir = "/home/mahdi/Programming/perfomance-monitor/enclosure"
blend_path = os.path.join(output_dir, "Pulse_Case.blend")
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 1280
scene.render.resolution_y = 800

cam = scene.camera

# Render 1: Front Isometric (already saved as preview)

# Render 2: Back View (USB & DC Jack)
cam.location = (-0.16, 0.16, 0.14)
cam.rotation_euler = (math.radians(55), 0, math.radians(-135))
scene.render.filepath = os.path.join(output_dir, "pulse_case_back_ports.png")
bpy.ops.render.render(write_still=True)

# Render 3: Exploded Top View showing internal Uno mounting & Lid
lid = bpy.data.objects.get("Pulse_Case_Lid")
if lid:
    lid.location.z += 0.025 # Lift lid 25mm for exploded view

cam.location = (0.14, -0.14, 0.18)
cam.rotation_euler = (math.radians(45), 0, math.radians(45))
scene.render.filepath = os.path.join(output_dir, "pulse_case_exploded.png")
bpy.ops.render.render(write_still=True)
print("Multiview renders finished.")
