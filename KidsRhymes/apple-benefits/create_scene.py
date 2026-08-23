from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
FPS = CONFIG["fps"]


def frame(seconds: float) -> int:
    return round(seconds * FPS) + 1


def material(name: str, colour: tuple[float, float, float, float], metallic: float = 0.0, roughness: float = 0.48):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = colour
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def smooth(obj) -> None:
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def sphere(name, location, scale, mat, parent=None, segments=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=max(12, segments // 2), location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    smooth(obj)
    if parent:
        obj.parent = parent
    return obj


def cube(name, location, scale, mat, bevel=0.15, parent=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel_mod = obj.modifiers.new("Soft edges", "BEVEL")
    bevel_mod.width = bevel
    bevel_mod.segments = 3
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def cylinder_between(name, start, end, radius, mat, parent=None):
    start_v, end_v = Vector(start), Vector(end)
    delta = end_v - start_v
    middle = (start_v + end_v) / 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=delta.length, location=middle)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    obj.data.materials.append(mat)
    smooth(obj)
    if parent:
        obj.parent = parent
    return obj


def text_object(name, body, location, size, mat, align="CENTER", parent=None, extrude=0.018):
    bpy.ops.object.text_add(location=location, rotation=(math.radians(90), 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = align
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = extrude
    obj.data.bevel_depth = 0.008
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj


def appear(obj, start_s: float, end_s: float, scale=(1, 1, 1)):
    obj.scale = (0.001, 0.001, 0.001)
    obj.keyframe_insert("scale", frame=max(1, frame(start_s) - 4))
    obj.scale = scale
    obj.keyframe_insert("scale", frame=frame(start_s))
    obj.keyframe_insert("scale", frame=frame(end_s) - 4)
    obj.scale = (0.001, 0.001, 0.001)
    obj.keyframe_insert("scale", frame=frame(end_s))


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.materials, bpy.data.curves, bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def build_scene(preview: bool) -> None:
    clear_scene()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH" if preview else "BLENDER_EEVEE"
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = frame(CONFIG["duration_seconds"]) - 1
    scene.render.resolution_x = CONFIG["preview_width"] if preview else CONFIG["width"]
    scene.render.resolution_y = CONFIG["preview_height"] if preview else CONFIG["height"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(ROOT / "output" / "frames" / "frame-")
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.resolution_percentage = 100
    scene.render.engine = "BLENDER_WORKBENCH" if preview else "BLENDER_EEVEE"
    if preview:
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "MATERIAL"
        scene.display.shading.show_shadows = True
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "WORLD"
    scene.render.image_settings.compression = 55
    scene.world.color = (0.24, 0.48, 0.8)
    scene.view_settings.look = "AgX - Medium High Contrast"

    red = material("Apple red", (0.72, 0.018, 0.025, 1), roughness=0.34)
    red_light = material("Apple highlight", (1.0, 0.055, 0.06, 1), roughness=0.3)
    green = material("Leaf green", (0.08, 0.48, 0.08, 1))
    green_light = material("Grass", (0.16, 0.62, 0.16, 1))
    brown = material("Stem brown", (0.22, 0.075, 0.025, 1))
    white = material("Eye white", (1, 0.97, 0.88, 1), roughness=0.25)
    black = material("Pupil", (0.006, 0.008, 0.014, 1), roughness=0.2)
    pink = material("Cheeks", (1, 0.22, 0.34, 1), roughness=0.5)
    cream = material("Warm cream", (1.0, 0.79, 0.36, 1))
    blue = material("Sky blue", (0.19, 0.67, 0.96, 1))
    navy = material("Text navy", (0.018, 0.08, 0.18, 1), roughness=0.35)
    orange = material("Orange", (1.0, 0.29, 0.025, 1))
    purple = material("Purple", (0.47, 0.12, 0.77, 1))

    # Sunny orchard set.
    cube("Ground", (0, 2.5, -1.05), (12, 10, 0.35), green_light, bevel=0.3)
    sphere("HillLeft", (-7, 5, 0.4), (6, 3, 2.2), green, segments=24)
    sphere("HillRight", (7, 6, 0.1), (7, 3, 2.0), green, segments=24)
    sphere("Sun", (-6.2, 5.8, 6.8), (1.0, 0.35, 1.0), cream, segments=24)
    for x, z, s in [(-5.2, 5.5, 0.7), (-4.4, 5.8, 0.9), (4.6, 6.0, 0.75), (5.5, 5.7, 1.0)]:
        sphere("Cloud", (x, 4.8, z), (s * 1.5, 0.35, s), white, segments=20)
    for x in (-6.4, 5.8):
        cylinder_between("Tree trunk", (x, 3.3, -0.8), (x, 3.3, 2.3), 0.42, brown)
        for dx, dz in [(-0.8, 0), (0, 0.55), (0.9, 0.05)]:
            sphere("Tree crown", (x + dx, 3.3, 2.4 + dz), (1.25, 0.7, 1.25), green, segments=20)
    # Soft stage behind captions.
    cube("Caption board", (-3.35, 1.5, 2.1), (2.55, 0.16, 2.25), cream, bevel=0.35)

    # Pip is assembled under a single animated root.
    root = bpy.data.objects.new("Pip_Apple_Root", None)
    bpy.context.collection.objects.link(root)
    root.location = (1.65, 0, 0)
    for dx, dz, scale in [(-0.42, 0.05, (1.05, 0.78, 1.35)), (0.42, 0.05, (1.05, 0.78, 1.35)), (0, -0.26, (1.15, 0.8, 1.18))]:
        sphere("AppleBody", (dx, 0, 1.55 + dz), scale, red, root)
    sphere("AppleShine", (-0.55, -0.72, 2.15), (0.18, 0.06, 0.42), red_light, root, 20)
    cylinder_between("Stem", (0, 0, 2.75), (0.12, 0, 3.48), 0.12, brown, root)
    leaf = sphere("Leaf", (0.48, -0.02, 3.35), (0.58, 0.12, 0.25), green, root, 24)
    leaf.rotation_euler.y = math.radians(-18)

    # Face projects toward the camera at negative Y.
    for x in (-0.43, 0.43):
        sphere("Eye", (x, -0.79, 1.95), (0.34, 0.13, 0.46), white, root, 24)
        pupil = sphere("Pupil", (x, -0.91, 1.94), (0.14, 0.07, 0.23), black, root, 20)
        pupil.location.z += 0.02
    sphere("Cheek", (-0.82, -0.78, 1.42), (0.22, 0.045, 0.13), pink, root, 20)
    sphere("Cheek", (0.82, -0.78, 1.42), (0.22, 0.045, 0.13), pink, root, 20)
    mouth = sphere("Talking mouth", (0, -0.86, 1.35), (0.38, 0.07, 0.16), black, root, 24)
    tongue = sphere("Tongue", (0, -0.925, 1.30), (0.22, 0.035, 0.07), pink, root, 20)

    # Arms, mitten hands and feet.
    cylinder_between("ArmLeft", (-0.85, 0, 1.7), (-1.62, -0.02, 1.95), 0.09, red, root)
    left_hand = sphere("HandLeft", (-1.73, -0.02, 2.03), (0.19, 0.14, 0.22), red_light, root, 18)
    cylinder_between("ArmRight", (0.85, 0, 1.7), (1.58, -0.02, 2.2), 0.09, red, root)
    right_hand = sphere("HandRight", (1.68, -0.02, 2.31), (0.19, 0.14, 0.22), red_light, root, 18)
    for x in (-0.48, 0.48):
        cylinder_between("Leg", (x, 0, 0.62), (x, 0, -0.28), 0.10, brown, root)
        sphere("Shoe", (x, -0.14, -0.42), (0.35, 0.48, 0.18), navy, root, 20)

    # Gentle continual bounce and friendly turns.
    for sec, z, rot in [(0, -3.8, -0.2), (2.2, 0, 0.08), (4, 0.12, -0.04), (8, 0, 0.04),
                        (12, 0.14, -0.05), (18, 0, 0.04), (26, 0.13, -0.03), (33, 0, 0.05),
                        (41, 0.12, -0.04), (49, 0, 0.07), (52, 0.1, 0)]:
        root.location.z = z
        root.rotation_euler[2] = rot
        root.keyframe_insert("location", frame=frame(sec))
        root.keyframe_insert("rotation_euler", frame=frame(sec))

    # Talking mouth pulses during narration, resting during pauses.
    speech_ranges = [(3, 9.4), (10, 17.3), (18, 25.2), (26, 32.3), (33, 40.3), (41, 48.3), (49, 51.2)]
    for start, end in speech_ranges:
        current = start
        while current < end:
            mouth.scale.z = 0.55
            mouth.keyframe_insert("scale", frame=frame(current))
            mouth.scale.z = 1.45
            mouth.keyframe_insert("scale", frame=frame(min(current + 0.13, end)))
            current += 0.28

    # Blinks give Pip life without needing a facial rig.
    eye_objects = [obj for obj in root.children if obj.name.startswith("Eye")]
    for eye in eye_objects:
        original = eye.scale.copy()
        for sec in (6.2, 15.1, 23.4, 31.1, 39.2, 47.0, 50.5):
            eye.scale = original
            eye.keyframe_insert("scale", frame=frame(sec - 0.08))
            eye.scale.z = original.z * 0.08
            eye.keyframe_insert("scale", frame=frame(sec))
            eye.scale = original
            eye.keyframe_insert("scale", frame=frame(sec + 0.1))

    # Caption cards and simple 3D teaching symbols.
    captions = [
        (3, 10, "MEET PIP!", cream),
        (10, 18, "FIBRE\nHELPS YOUR\nTUMMY", green),
        (18, 26, "A LITTLE\nVITAMIN C", orange),
        (26, 33, "JUICY + CRUNCHY", blue),
        (33, 41, "EAT A RAINBOW", purple),
        (41, 49, "WASH + PREPARE\nWITH A GROWN-UP", green),
        (49, 52, "CRUNCH, SMILE,\nAND ENJOY!", orange),
    ]
    for index, (start, end, words, colour) in enumerate(captions):
        caption_size = 0.36 if len(words) > 22 else 0.45
        card = cube(f"Card{index}", (-3.35, -0.12, 2.1), (2.25, 0.08, 1.33), white, bevel=0.25)
        label = text_object(f"Caption{index}", words, (-3.35, -0.24, 2.12), caption_size, navy)
        accent = sphere(f"Accent{index}", (-3.35, -0.26, 0.98), (1.4, 0.045, 0.08), colour, segments=20)
        appear(card, start, end)
        appear(label, start + 0.12, end - 0.05)
        appear(accent, start + 0.22, end - 0.08)

    # Fruit-colour dots appear for the variety scene.
    for index, (x, colour) in enumerate([(-4.75, red), (-4.05, orange), (-3.35, cream), (-2.65, green), (-1.95, purple)]):
        dot = sphere(f"FruitColour{index}", (x, -0.34, 0.75), (0.24, 0.07, 0.24), colour, segments=18)
        appear(dot, 34 + index * 0.25, 40.6)

    # Prepared apple slices reinforce the safety line without showing a knife.
    plate = sphere("Serving plate", (-0.42, -0.38, -0.62), (1.05, 0.15, 0.24), white, segments=24)
    appear(plate, 41.2, 48.8)
    for index, x in enumerate((-0.9, -0.42, 0.06)):
        peel = sphere(f"Slice peel {index}", (x, -0.58, -0.35), (0.32, 0.07, 0.50), red, segments=20)
        flesh = sphere(f"Slice flesh {index}", (x, -0.65, -0.34), (0.25, 0.04, 0.42), cream, segments=20)
        peel.rotation_euler.y = math.radians((index - 1) * 14)
        flesh.rotation_euler.y = peel.rotation_euler.y
        appear(peel, 41.35 + index * 0.12, 48.7)
        appear(flesh, 41.38 + index * 0.12, 48.7)

    # Camera and lights.
    bpy.ops.object.camera_add(location=(0, -14.7, 4.25))
    camera = bpy.context.object
    camera.name = "Main Camera"
    camera.data.lens = 52
    look_at(camera, (0, 0, 1.55))
    scene.camera = camera
    for sec, x, y, z, lens in [(0, 0, -15.8, 4.6, 54), (3, 0, -14.7, 4.25, 52),
                                (10, -0.25, -14.1, 4.1, 53), (33, 0, -14.8, 4.3, 51),
                                (49, 0.1, -14.1, 4.15, 53), (52, 0, -15.1, 4.4, 52)]:
        camera.location = (x, y, z)
        look_at(camera, (0, 0, 1.55))
        camera.data.lens = lens
        camera.keyframe_insert("location", frame=frame(sec))
        camera.keyframe_insert("rotation_euler", frame=frame(sec))
        camera.data.keyframe_insert("lens", frame=frame(sec))

    bpy.ops.object.light_add(type="AREA", location=(-4, -5, 8))
    key = bpy.context.object
    key.name = "Warm key"
    key.data.energy = 1150
    key.data.shape = "DISK"
    key.data.size = 5
    look_at(key, (0, 0, 1.5))
    bpy.ops.object.light_add(type="AREA", location=(5, -2, 5))
    fill = bpy.context.object
    fill.name = "Cool fill"
    fill.data.energy = 850
    fill.data.color = (0.55, 0.72, 1.0)
    fill.data.size = 4
    look_at(fill, (1, 0, 1.5))
    bpy.ops.object.light_add(type="POINT", location=(0, 3, 6))
    bpy.context.object.data.energy = 500

    (ROOT / "output" / "frames").mkdir(parents=True, exist_ok=True)
    blend_path = ROOT / "output" / ("pip-apple-preview.blend" if preview else "pip-apple.blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"Saved {blend_path}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality", choices=("preview", "final"), default="preview")
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(args)


if __name__ == "__main__":
    options = parse_args()
    build_scene(preview=options.quality == "preview")
