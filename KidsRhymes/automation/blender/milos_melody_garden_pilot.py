"""Build and render the reusable Milo's Melody Garden Blender pilot.

Run with Blender 5.2.1 LTS:
  blender.exe --background --python automation/blender/milos_melody_garden_pilot.py

The script intentionally creates the scene from named, modular primitives so
the character, garden stage, drums, blooms, lights and camera can be extended
into a full Tiny Tales episode without relying on a one-off generated model.
"""

from __future__ import annotations

import math
from pathlib import Path
import random
import struct
import wave

import bpy
from mathutils import Vector


PROJECT = Path(__file__).resolve().parents[2]
ITEM_ID = "milos-melody-garden-blender-pilot-01"
WORK = PROJECT / "automation" / "production-work" / ITEM_ID
FRAMES = WORK / "frames"
BLEND = WORK / "milos-melody-garden-pilot.blend"
AUDIO = WORK / "milos-melody-garden-pilot.wav"
FPS = 24
FRAME_END = 144
HIT_FRAMES = (48, 72, 96)


def reset_scene() -> bpy.types.Scene:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = FRAME_END
    scene.render.fps = FPS
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(FRAMES / "frame_")
    scene.render.use_file_extension = True
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 32
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.012, 0.02, 0.065)
    return scene


def material(name: str, color: tuple[float, float, float, float], roughness: float = 0.55,
             metallic: float = 0.0, emission: tuple[float, float, float, float] | None = None,
             emission_strength: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = roughness
    principled.inputs["Metallic"].default_value = metallic
    if emission:
        principled.inputs["Emission Color"].default_value = emission
        principled.inputs["Emission Strength"].default_value = emission_strength
    return mat


def empty(name: str, location=(0, 0, 0), parent=None) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.empty_display_type = "CIRCLE"
    obj.empty_display_size = 0.22
    obj.location = location
    if parent:
        obj.parent = parent
    return obj


def smooth_object(obj: bpy.types.Object) -> bpy.types.Object:
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj


def uv_sphere(name: str, location, scale, mat, parent=None, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.location = location
    obj.scale = scale
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return smooth_object(obj)


def cylinder(name: str, location, radius, depth, mat, parent=None, rotation=(0, 0, 0), vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return smooth_object(obj)


def cone(name: str, location, radius1, radius2, depth, mat, parent=None, rotation=(0, 0, 0), vertices=32):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return smooth_object(obj)


def torus(name: str, location, major_radius, minor_radius, mat, parent=None, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius,
                                    major_segments=36, minor_segments=12, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return smooth_object(obj)


def set_interp(obj: bpy.types.Object, mode="BEZIER") -> None:
    if not obj.animation_data or not obj.animation_data.action:
        return
    # Blender 5.2 stores newly keyed curves in layered Action channel bags.
    # The default interpolation is already Bezier there; older APIs expose
    # fcurves directly and can receive the explicit auto-clamped handles.
    curves = getattr(obj.animation_data.action, "fcurves", None)
    if curves is None:
        return
    for curve in curves:
        for point in curve.keyframe_points:
            point.interpolation = mode
            if mode == "BEZIER":
                point.handle_left_type = "AUTO_CLAMPED"
                point.handle_right_type = "AUTO_CLAMPED"


def key(obj: bpy.types.Object, frame: int, path: str, value) -> None:
    setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def build_materials() -> dict[str, bpy.types.Material]:
    return {
        "grass": material("TT_GRASS", (0.13, 0.48, 0.23, 1)),
        "grass_light": material("TT_GRASS_LIGHT", (0.28, 0.72, 0.35, 1)),
        "orange": material("MILO_ORANGE", (0.78, 0.20, 0.075, 1), roughness=0.62),
        "cream": material("MILO_CREAM", (1.0, 0.76, 0.43, 1), roughness=0.7),
        "dark": material("MILO_DARK", (0.055, 0.035, 0.075, 1), roughness=0.6),
        "white": material("EYE_WHITE", (0.98, 0.98, 0.92, 1), roughness=0.45),
        "wood": material("DRUM_WOOD", (0.32, 0.10, 0.055, 1), roughness=0.72),
        "blue": material("GLOW_BLUE", (0.05, 0.32, 0.78, 1), roughness=0.32,
                         emission=(0.03, 0.24, 1.0, 1), emission_strength=1.5),
        "gold": material("GLOW_GOLD", (0.95, 0.48, 0.04, 1), roughness=0.34,
                         emission=(1.0, 0.32, 0.02, 1), emission_strength=1.4),
        "pink": material("GLOW_PINK", (0.93, 0.12, 0.46, 1), roughness=0.34,
                         emission=(1.0, 0.03, 0.28, 1), emission_strength=1.45),
        "yellow": material("FIREFLY_GLOW", (1.0, 0.7, 0.08, 1), roughness=0.25,
                           emission=(1.0, 0.42, 0.02, 1), emission_strength=5.0),
        "lavender": material("BG_LAVENDER", (0.31, 0.20, 0.52, 1), roughness=0.75),
        "teal": material("BG_TEAL", (0.03, 0.42, 0.43, 1), roughness=0.7),
        "moon": material("MOON_GLOW", (0.9, 0.86, 0.65, 1), roughness=0.6,
                         emission=(1.0, 0.76, 0.3, 1), emission_strength=2.2),
    }


def build_stage(mats):
    cylinder("GARDEN_STAGE", (0, 0.35, 0.12), 4.6, 0.38, mats["grass"], vertices=64)
    cylinder("GARDEN_STAGE_TRIM", (0, 0.35, -0.02), 4.75, 0.18, mats["grass_light"], vertices=64)
    # Curved stepping stones establish a readable path into the music garden.
    for i, (x, y, scale) in enumerate(((-3.4, -1.2, 0.55), (-2.5, -0.9, 0.48), (-1.7, -0.72, 0.42))):
        uv_sphere(f"PATH_STONE_{i+1}", (x, y, 0.32), (scale, scale * 0.65, 0.12), mats["cream"])
    # Rounded background trees stay static; only leaf clusters receive a tiny sway.
    trees = []
    for i, (x, y, h, tint) in enumerate(((-4.2, 1.9, 2.2, "lavender"), (-2.9, 2.7, 2.6, "teal"),
                                          (3.3, 2.5, 2.5, "lavender"), (4.3, 1.6, 2.0, "teal"))):
        cylinder(f"TREE_TRUNK_{i+1}", (x, y, h * 0.45), 0.18, h * 0.9, mats["wood"])
        crown = uv_sphere(f"TREE_CROWN_{i+1}", (x, y, h), (0.82, 0.58, 0.9), mats[tint])
        trees.append(crown)
    for i, crown in enumerate(trees):
        crown.rotation_euler = (0, 0, -0.035)
        crown.keyframe_insert("rotation_euler", frame=1)
        crown.rotation_euler = (0, 0, 0.04)
        crown.keyframe_insert("rotation_euler", frame=72)
        crown.rotation_euler = (0, 0, -0.035)
        crown.keyframe_insert("rotation_euler", frame=144)
        set_interp(crown)
    uv_sphere("MOON", (-3.6, 4.4, 4.7), (0.72, 0.24, 0.72), mats["moon"])


def build_milo(mats):
    root = empty("MILO_CTRL", (0.75, 0.45, 0.34))
    body = uv_sphere("MILO_BODY", (0, 0, 1.28), (0.72, 0.52, 0.94), mats["orange"], root)
    uv_sphere("MILO_BELLY", (0, -0.48, 1.22), (0.43, 0.13, 0.56), mats["cream"], root)
    head_ctrl = empty("MILO_HEAD_CTRL", (0, 0, 2.25), root)
    uv_sphere("MILO_HEAD", (0, 0, 0), (0.67, 0.58, 0.61), mats["orange"], head_ctrl)
    for side in (-1, 1):
        uv_sphere(f"MILO_EAR_{'L' if side < 0 else 'R'}", (side * 0.47, 0.02, 0.45),
                  (0.25, 0.18, 0.31), mats["dark"], head_ctrl)
        uv_sphere(f"MILO_EAR_INNER_{'L' if side < 0 else 'R'}", (side * 0.47, -0.13, 0.45),
                  (0.14, 0.06, 0.18), mats["pink"], head_ctrl)
        uv_sphere(f"MILO_EYE_PATCH_{'L' if side < 0 else 'R'}", (side * 0.25, -0.51, 0.08),
                  (0.22, 0.08, 0.25), mats["cream"], head_ctrl)
        uv_sphere(f"MILO_EYE_{'L' if side < 0 else 'R'}", (side * 0.25, -0.575, 0.11),
                  (0.095, 0.055, 0.12), mats["dark"], head_ctrl)
        uv_sphere(f"MILO_EYE_GLINT_{'L' if side < 0 else 'R'}", (side * 0.225, -0.63, 0.16),
                  (0.025, 0.018, 0.028), mats["white"], head_ctrl, segments=20, rings=12)
    uv_sphere("MILO_MUZZLE", (0, -0.53, -0.15), (0.29, 0.12, 0.20), mats["cream"], head_ctrl)
    uv_sphere("MILO_NOSE", (0, -0.66, -0.09), (0.09, 0.06, 0.065), mats["dark"], head_ctrl)
    # Legs provide planted contact and can become full IK limbs in the episode extension.
    for side in (-1, 1):
        leg = empty(f"MILO_LEG_CTRL_{'L' if side < 0 else 'R'}", (side * 0.31, 0, 0.67), root)
        uv_sphere(f"MILO_LEG_{'L' if side < 0 else 'R'}", (0, 0, -0.18), (0.23, 0.26, 0.45), mats["dark"], leg)
        uv_sphere(f"MILO_FOOT_{'L' if side < 0 else 'R'}", (0, -0.22, -0.52), (0.28, 0.42, 0.16), mats["dark"], leg)
    arms = {}
    for side, label in ((-1, "L"), (1, "R")):
        ctrl = empty(f"MILO_ARM_CTRL_{label}", (side * 0.54, -0.05, 1.70), root)
        uv_sphere(f"MILO_ARM_{label}", (side * 0.09, -0.02, -0.34), (0.19, 0.19, 0.46), mats["dark"], ctrl)
        stick = cylinder(f"MILO_STICK_{label}", (side * 0.12, -0.20, -0.78), 0.055, 0.9,
                         mats["cream"], ctrl, rotation=(math.radians(12), 0, math.radians(-side * 8)), vertices=20)
        uv_sphere(f"MILO_STICK_TIP_{label}", (side * 0.12, -0.28, -1.19), (0.11, 0.11, 0.13), mats["pink"], ctrl)
        arms[label] = ctrl
    # A segmented striped tail gives readable secondary follow-through.
    tail_ctrl = empty("MILO_TAIL_CTRL", (0.62, 0.20, 1.02), root)
    for i in range(6):
        angle = math.radians(20 + i * 9)
        x = 0.23 + i * 0.25
        z = 0.03 + math.sin(angle) * i * 0.08
        uv_sphere(f"MILO_TAIL_SEG_{i+1}", (x, 0.15, z), (0.31 - i * 0.018, 0.24, 0.27),
                  mats["orange" if i % 2 == 0 else "dark"], tail_ctrl)
    return root, head_ctrl, arms, tail_ctrl


def build_drums_and_flowers(mats):
    drums = []
    flowers = []
    spec = (
        ("BLUE", -1.45, "blue"),
        ("GOLD", 0.0, "gold"),
        ("PINK", 1.45, "pink"),
    )
    for index, (label, x, colour) in enumerate(spec):
        root = empty(f"DRUM_{label}", (x, -1.05, 0.33))
        cone(f"DRUM_{label}_BASE", (0, 0, 0.48), 0.56, 0.42, 0.88, mats["wood"], root)
        cap = uv_sphere(f"DRUM_{label}_CAP", (0, 0, 0.94), (0.68, 0.54, 0.30), mats[colour], root)
        torus(f"DRUM_{label}_RIM", (0, 0, 0.88), 0.55, 0.055, mats["cream"], root,
              rotation=(0, 0, 0))
        drums.append((root, cap, mats[colour]))
        # Fan the blooms slightly wider than the drums so every payoff remains
        # readable around Milo's silhouette, especially the pink flower beside
        # the striped tail.
        flower_x = x + (-0.45, 0.0, 0.75)[index]
        flower_root = empty(f"FLOWER_{label}", (flower_x, 0.92, 0.34))
        cylinder(f"FLOWER_{label}_STEM", (0, 0, 0.42), 0.055, 0.84, mats["grass_light"], flower_root, vertices=20)
        bloom = empty(f"FLOWER_{label}_BLOOM_CTRL", (0, -0.01, 0.91), flower_root)
        for petal in range(6):
            angle = petal * math.tau / 6
            uv_sphere(f"FLOWER_{label}_PETAL_{petal+1}",
                      (math.cos(angle) * 0.25, 0, math.sin(angle) * 0.25),
                      (0.22, 0.11, 0.32), mats[colour], bloom).rotation_euler[1] = angle
        uv_sphere(f"FLOWER_{label}_CENTRE", (0, -0.08, 0), (0.18, 0.10, 0.18), mats["yellow"], bloom)
        bloom.scale = (0.06, 0.06, 0.06)
        flowers.append(bloom)
    return drums, flowers


def build_fireflies(mats):
    fireflies = []
    positions = ((-2.6, 0.2, 2.2), (-1.8, 1.1, 2.9), (2.6, 0.4, 2.5), (3.2, 1.2, 3.2), (0.2, 2.2, 3.4))
    for i, position in enumerate(positions):
        fly = uv_sphere(f"FIREFLY_{i+1}", position, (0.075, 0.075, 0.075), mats["yellow"], segments=16, rings=10)
        fly.keyframe_insert("location", frame=1)
        fly.location.x += 0.18 * (-1 if i % 2 else 1)
        fly.location.z += 0.16 + 0.04 * i
        fly.keyframe_insert("location", frame=72)
        fly.location.x -= 0.08 * (-1 if i % 2 else 1)
        fly.location.z -= 0.10
        fly.keyframe_insert("location", frame=144)
        set_interp(fly)
        fireflies.append(fly)
    return fireflies


def animate(scene, milo, head, arms, tail, drums, flowers):
    # Establish -> anticipation -> three clear impacts -> final welcoming pose.
    key(milo, 1, "location", Vector((0.75, 0.45, 0.34)))
    key(milo, 18, "location", Vector((0.75, 0.45, 0.27)))
    key(milo, 30, "location", Vector((0.75, 0.45, 0.46)))
    key(milo, 42, "location", Vector((0.75, 0.45, 0.34)))
    key(milo, 144, "location", Vector((0.75, 0.45, 0.34)))
    key(head, 1, "rotation_euler", Vector((0, 0, math.radians(-4))))
    key(head, 30, "rotation_euler", Vector((math.radians(-4), 0, math.radians(5))))
    key(head, 112, "rotation_euler", Vector((math.radians(-2), 0, math.radians(-4))))
    key(head, 144, "rotation_euler", Vector((0, 0, 0)))
    # Body squash and stretch are restrained to preserve character volume.
    key(milo, 1, "scale", Vector((1, 1, 1)))
    key(milo, 18, "scale", Vector((1.04, 1.04, 0.94)))
    key(milo, 30, "scale", Vector((0.97, 0.97, 1.06)))
    key(milo, 42, "scale", Vector((1, 1, 1)))
    key(milo, 144, "scale", Vector((1, 1, 1)))

    # Drum contacts use the nearest readable hand and a short anticipation.
    # The right hand carries through from the centre drum to the pink drum,
    # creating a clear left-to-right musical phrase.
    hit_specs = ((48, "L", 0), (72, "R", 1), (96, "R", 2))
    for hit, hand, drum_index in hit_specs:
        arm = arms[hand]
        direction = -1 if hand == "L" else 1
        key(arm, hit - 12, "rotation_euler", Vector((math.radians(-18), math.radians(direction * -18), math.radians(direction * 8))))
        key(arm, hit - 5, "rotation_euler", Vector((math.radians(-34), math.radians(direction * -34), math.radians(direction * 16))))
        key(arm, hit, "rotation_euler", Vector((math.radians(18), math.radians(direction * 22), math.radians(direction * -10))))
        key(arm, hit + 7, "rotation_euler", Vector((math.radians(-10), math.radians(direction * -8), 0)))
        key(arm, hit + 15, "rotation_euler", Vector((math.radians(-16), 0, 0)))
        cap = drums[drum_index][1]
        key(cap, hit - 1, "scale", Vector((0.68, 0.54, 0.30)))
        key(cap, hit + 2, "scale", Vector((0.74, 0.59, 0.22)))
        key(cap, hit + 8, "scale", Vector((0.66, 0.52, 0.33)))
        key(cap, hit + 14, "scale", Vector((0.68, 0.54, 0.30)))
        bloom = flowers[drum_index]
        key(bloom, 1, "scale", Vector((0.06, 0.06, 0.06)))
        key(bloom, hit + 1, "scale", Vector((0.06, 0.06, 0.06)))
        key(bloom, hit + 9, "scale", Vector((1.16, 1.16, 1.16)))
        key(bloom, hit + 18, "scale", Vector((1, 1, 1)))
    # Ensure each bloom remains open after its own settle.
    for bloom in flowers:
        key(bloom, 144, "scale", Vector((1, 1, 1)))
    # Tail follows the body with slower overlapping action.
    key(tail, 1, "rotation_euler", Vector((0, math.radians(-4), math.radians(-8))))
    key(tail, 38, "rotation_euler", Vector((0, math.radians(6), math.radians(10))))
    key(tail, 82, "rotation_euler", Vector((0, math.radians(-5), math.radians(-11))))
    key(tail, 116, "rotation_euler", Vector((0, math.radians(6), math.radians(12))))
    key(tail, 144, "rotation_euler", Vector((0, 0, math.radians(4))))
    # Final pose: both sticks raised after the third flower has settled.
    for label, arm in arms.items():
        direction = -1 if label == "L" else 1
        key(arm, 112, "rotation_euler", Vector((math.radians(-18), 0, 0)))
        key(arm, 124, "rotation_euler", Vector((math.radians(-72), math.radians(direction * 14), math.radians(direction * 18))))
        key(arm, 144, "rotation_euler", Vector((math.radians(-66), math.radians(direction * 10), math.radians(direction * 14))))
    for obj in (milo, head, arms["L"], arms["R"], tail, *(d[1] for d in drums), *flowers):
        set_interp(obj)


def build_camera_and_lights(scene):
    target = empty("CAMERA_TARGET", (0.15, 0.15, 1.52))
    bpy.ops.object.camera_add(location=(0.0, -12.1, 5.25))
    camera = bpy.context.object
    camera.name = "TT_CAMERA"
    camera.data.lens = 52
    camera.data.sensor_width = 36
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = target
    camera.data.dof.aperture_fstop = 5.6
    look_at(camera, target.location)
    camera.keyframe_insert("location", frame=1)
    camera.location = (0.0, -10.75, 4.9)
    look_at(camera, target.location)
    camera.keyframe_insert("location", frame=144)
    camera.keyframe_insert("rotation_euler", frame=1)
    camera.keyframe_insert("rotation_euler", frame=144)
    set_interp(camera)
    scene.camera = camera
    # Warm key, cool fill and soft rim separate Milo from the twilight world.
    for name, kind, location, energy, color, size in (
        ("KEY_WARM", "AREA", (-4.0, -5.0, 7.0), 1050, (1.0, 0.54, 0.28), 5.0),
        ("FILL_COOL", "AREA", (4.5, -2.0, 5.0), 800, (0.22, 0.48, 1.0), 4.0),
        ("RIM_MOON", "AREA", (-1.5, 4.0, 6.0), 900, (0.55, 0.64, 1.0), 3.0),
    ):
        data = bpy.data.lights.new(name, kind)
        data.energy = energy
        data.color = color
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = location
        look_at(light, Vector((0, 0, 1.2)))
    return camera, target


def setup_compositor(scene):
    scene.use_nodes = True
    if not hasattr(scene, "node_tree"):
        # Blender 5.2 moved compositor editing to its new node-group API.
        # The scene remains valid without a post glow because all hero props
        # use emissive physically lit materials; keep this optional rather
        # than depending on a deprecated compositor interface.
        return
    nodes = scene.node_tree.nodes
    links = scene.node_tree.links
    nodes.clear()
    render_layers = nodes.new("CompositorNodeRLayers")
    glare = nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 1.0
    glare.size = 6
    composite = nodes.new("CompositorNodeComposite")
    links.new(render_layers.outputs["Image"], glare.inputs["Image"])
    links.new(glare.outputs["Image"], composite.inputs["Image"])


def write_audio():
    rate = 48000
    duration = FRAME_END / FPS
    rng = random.Random(52021)
    hits = [frame / FPS for frame in HIT_FRAMES]
    notes = (261.63, 329.63, 392.0, 523.25)
    frames = bytearray()
    for n in range(round(duration * rate)):
        t = n / rate
        beat = 60 / 108
        phase = t % beat
        note = notes[int(t / beat) % len(notes)]
        pluck = math.sin(math.tau * note * t) * math.exp(-5.4 * phase) * 0.035
        pad = (math.sin(math.tau * 130.81 * t) + math.sin(math.tau * 196.0 * t)) * 0.008
        value = pluck + pad + rng.uniform(-0.0006, 0.0006)
        for index, hit in enumerate(hits):
            age = t - hit
            if 0 <= age < 0.42:
                fundamental = (126, 164, 208)[index]
                value += math.sin(math.tau * fundamental * age) * math.exp(-12 * age) * 0.25
                value += math.sin(math.tau * fundamental * 2.35 * age) * math.exp(-18 * age) * 0.10
                value += rng.uniform(-1, 1) * math.exp(-32 * age) * 0.07
        # Bright resolving chime after the final bloom.
        for onset, freq in ((4.38, 659.25), (4.62, 783.99), (4.88, 987.77)):
            age = t - onset
            if 0 <= age < 0.7:
                value += math.sin(math.tau * freq * age) * math.exp(-5.5 * age) * 0.065
        sample = int(max(-1.0, min(1.0, value)) * 30000)
        frames.extend(struct.pack("<hh", sample, sample))
    AUDIO.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(AUDIO), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(frames)


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    scene = reset_scene()
    mats = build_materials()
    build_stage(mats)
    milo, head, arms, tail = build_milo(mats)
    drums, flowers = build_drums_and_flowers(mats)
    build_fireflies(mats)
    animate(scene, milo, head, arms, tail, drums, flowers)
    build_camera_and_lights(scene)
    setup_compositor(scene)
    write_audio()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
