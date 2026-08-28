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
import sys
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
FRAME_END = 192
HIT_FRAMES = (72, 104, 136)


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
    scene.render.image_settings.color_mode = "RGBA"
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


def cube(name: str, location, scale, mat, parent=None, rotation=(0, 0, 0), bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.location = location
    obj.scale = scale
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Soft bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
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
        "grass_dark": material("TT_GRASS_DARK", (0.035, 0.18, 0.13, 1), roughness=0.82),
        "leaf_mint": material("TT_LEAF_MINT", (0.12, 0.58, 0.40, 1), roughness=0.72),
        "leaf_plum": material("TT_LEAF_PLUM", (0.30, 0.09, 0.35, 1), roughness=0.72),
        "orange": material("MILO_ORANGE", (0.78, 0.20, 0.075, 1), roughness=0.62),
        "cream": material("MILO_CREAM", (1.0, 0.76, 0.43, 1), roughness=0.7),
        "dark": material("MILO_DARK", (0.055, 0.035, 0.075, 1), roughness=0.6),
        "white": material("EYE_WHITE", (0.98, 0.98, 0.92, 1), roughness=0.45),
        "wood": material("DRUM_WOOD", (0.32, 0.10, 0.055, 1), roughness=0.72),
        "wood_light": material("CARVED_WOOD_LIGHT", (0.66, 0.27, 0.08, 1), roughness=0.64),
        "brass": material("INSTRUMENT_BRASS", (0.74, 0.31, 0.045, 1), roughness=0.24, metallic=0.72),
        "navy": material("MILO_VEST_NAVY", (0.025, 0.09, 0.25, 1), roughness=0.5),
        "aqua": material("MILO_SCARF_AQUA", (0.02, 0.64, 0.68, 1), roughness=0.48),
        "coral": material("FLOWER_CORAL", (0.96, 0.18, 0.22, 1), roughness=0.5),
        "stone": material("GARDEN_STONE", (0.24, 0.29, 0.42, 1), roughness=0.86),
        "water": material("POND_WATER", (0.015, 0.22, 0.34, 1), roughness=0.16, metallic=0.16,
                           emission=(0.01, 0.17, 0.28, 1), emission_strength=0.25),
        "sky_navy": material("SKY_NIGHT_NAVY", (0.006, 0.012, 0.055, 1), roughness=0.92,
                              emission=(0.008, 0.018, 0.09, 1), emission_strength=0.35),
        "sky_violet": material("DISTANT_HILL_VIOLET", (0.08, 0.035, 0.18, 1), roughness=0.88),
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
    # A physical night-sky cyclorama removes the empty black void and remains
    # controllable when this world expands into additional episode zones.
    sky = cube("NIGHT_SKY_BACKDROP", (0, 5.15, 4.1), (8.8, 0.12, 4.8), mats["sky_navy"], bevel=0.5)
    for i, (x, z, scale) in enumerate(((-5.3, 2.15, 2.3), (-2.8, 2.42, 2.65),
                                       (0.2, 2.15, 2.45), (3.0, 2.48, 2.75), (5.5, 2.10, 2.25))):
        uv_sphere(f"DISTANT_HILL_{i+1}", (x, 4.72, z), (scale, 0.42, scale * 0.72), mats["sky_violet"])
    for i, (x, z, scale) in enumerate(((-5.8, 5.85, 0.055), (-4.8, 4.55, 0.038),
                                        (-3.0, 6.15, 0.045), (-1.8, 5.05, 0.038),
                                        (-0.4, 6.42, 0.052), (1.2, 5.60, 0.035),
                                        (2.5, 6.35, 0.050), (4.0, 5.12, 0.038),
                                        (5.6, 6.0, 0.055))):
        uv_sphere(f"STAR_{i+1}", (x, 4.45, z), (scale, 0.025, scale), mats["moon"], segments=16, rings=10)
    # Layered, asymmetrical terrain replaces the flat prototype disc and gives
    # the camera true foreground, midground and background depth.
    stage = cylinder("GARDEN_STAGE", (0.2, 0.45, 0.06), 5.35, 0.42, mats["grass"], vertices=96)
    stage.scale.y = 0.72
    trim = cylinder("GARDEN_STAGE_TRIM", (0.2, 0.48, -0.14), 5.5, 0.24, mats["grass_dark"], vertices=96)
    trim.scale.y = 0.73
    rug = cylinder("MUSIC_STAGE_RUG", (0.05, -0.72, 0.285), 2.65, 0.045, mats["navy"], vertices=96)
    rug.scale.y = 0.60
    rug_inlay = torus("MUSIC_STAGE_RUG_INLAY", (0.05, -0.72, 0.315), 2.20, 0.035, mats["brass"])
    rug_inlay.scale.y = 0.60
    for i, (x, y, sx, sy) in enumerate(((-3.5, 1.2, 2.0, 1.05), (3.55, 1.55, 2.2, 1.1),
                                         (-0.3, 2.85, 2.65, 0.8))):
        island = uv_sphere(f"TERRAIN_MOUND_{i+1}", (x, y, 0.12), (sx, sy, 0.42),
                           mats["grass_dark" if i < 2 else "grass"])
        island.rotation_euler.z = (-0.16, 0.14, -0.04)[i]

    # A reflective crescent pond, stone rim and curved path establish a world
    # beyond the performance platform.
    pond = uv_sphere("MOONLIT_POND", (-3.45, 0.55, 0.24), (1.45, 0.70, 0.055), mats["water"])
    pond.rotation_euler.z = -0.18
    for i, angle in enumerate((-2.55, -2.1, -1.62, -1.16, -0.66, -0.20, 0.28)):
        x = -3.45 + math.cos(angle) * 1.55
        y = 0.55 + math.sin(angle) * 0.78
        uv_sphere(f"POND_ROCK_{i+1}", (x, y, 0.27), (0.30, 0.21, 0.14), mats["stone"])
    for i, (x, y, scale, angle) in enumerate(((-3.95, -1.45, 0.62, -0.18), (-3.00, -1.22, 0.54, 0.1),
                                                (-2.15, -0.94, 0.47, 0.22), (-1.38, -0.66, 0.40, 0.28))):
        stone = uv_sphere(f"PATH_STONE_{i+1}", (x, y, 0.30), (scale, scale * 0.60, 0.12), mats["cream"])
        stone.rotation_euler.z = angle

    # An illuminated carved-wood music arch makes the stage feel designed.
    for side in (-1, 1):
        cylinder(f"ARCH_POST_{'L' if side < 0 else 'R'}", (side * 2.55, 1.48, 1.72),
                 0.17, 3.05, mats["wood_light"], rotation=(0.04 * side, 0, 0))
        torus(f"ARCH_COLLAR_{'L' if side < 0 else 'R'}", (side * 2.55, 1.48, 0.45),
              0.23, 0.045, mats["brass"], rotation=(math.radians(90), 0, 0))
    arch_top = torus("MUSIC_ARCH_TOP", (0, 1.48, 3.10), 2.58, 0.16, mats["wood_light"],
                     rotation=(math.radians(90), 0, 0))
    arch_top.scale.z = 0.62
    # Leaf garland, jewel lights and layered foliage add a crafted storybook finish.
    for i in range(15):
        angle = math.pi * (i / 14)
        x = math.cos(angle) * 2.60
        z = 2.98 + math.sin(angle) * 1.36
        leaf = uv_sphere(f"ARCH_LEAF_{i+1}", (x, 1.34, z), (0.22, 0.09, 0.36),
                         mats["leaf_mint" if i % 2 else "leaf_plum"], segments=20, rings=12)
        leaf.rotation_euler.y = angle - math.pi / 2
        if i % 2 == 0:
            uv_sphere(f"ARCH_LIGHT_{i+1}", (x, 1.16, z - 0.12), (0.075, 0.075, 0.075), mats["yellow"], segments=16, rings=10)

    # Each tree uses several overlapping crowns instead of one primitive ball.
    trees = []
    tree_specs = ((-5.0, 2.2, 2.25, "teal"), (-3.75, 3.0, 2.8, "lavender"),
                  (3.85, 3.05, 2.85, "teal"), (5.05, 1.95, 2.30, "lavender"))
    for i, (x, y, h, tint) in enumerate(tree_specs):
        trunk = cylinder(f"TREE_TRUNK_{i+1}", (x, y, h * 0.45), 0.20, h * 0.92, mats["wood"])
        trunk.rotation_euler.y = 0.06 * (-1 if i % 2 else 1)
        crown_root = empty(f"TREE_CROWN_CTRL_{i+1}", (x, y, h))
        for j, (ox, oz, scale) in enumerate(((-0.38, 0.02, 0.72), (0.34, 0.14, 0.78),
                                             (0.0, 0.55, 0.68), (0.02, -0.38, 0.66))):
            uv_sphere(f"TREE_CROWN_{i+1}_{j+1}", (ox, 0, oz), (scale, 0.52, scale * 0.88),
                      mats[tint if j % 2 == 0 else ("leaf_plum" if tint == "teal" else "leaf_mint")], crown_root)
        trees.append(crown_root)
    for i, crown in enumerate(trees):
        key(crown, 1, "rotation_euler", Vector((0, 0, math.radians(-1.5))))
        key(crown, 96, "rotation_euler", Vector((0, 0, math.radians(1.8))))
        key(crown, 192, "rotation_euler", Vector((0, 0, math.radians(-1.5))))
        set_interp(crown)

    # Foreground foliage deliberately crosses the frame edge for parallax and
    # gives the polished image a photographed, dimensional composition.
    for side in (-1, 1):
        for i in range(5):
            x = side * (4.25 + i * 0.22)
            y = -2.28 + i * 0.10
            leaf = uv_sphere(f"FOREGROUND_LEAF_{side}_{i}", (x, y, 0.52 + i * 0.19),
                             (0.30, 0.14, 0.62), mats["leaf_plum" if i % 2 else "leaf_mint"])
            leaf.rotation_euler.y = side * math.radians(18 + i * 7)
        uv_sphere(f"FOREGROUND_FLOWER_{side}", (side * 4.38, -2.18, 1.22),
                  (0.42, 0.18, 0.42), mats["coral"])
    uv_sphere("MOON", (-4.0, 4.6, 5.1), (0.82, 0.30, 0.82), mats["moon"])


def build_milo(mats):
    root = empty("MILO_CTRL", (0.75, 0.45, 0.34))
    body = uv_sphere("MILO_BODY", (0, 0, 1.28), (0.72, 0.52, 0.94), mats["orange"], root)
    uv_sphere("MILO_BELLY", (0, -0.48, 1.22), (0.43, 0.13, 0.56), mats["cream"], root)
    # Tailored stage costume gives Milo a specific identity rather than the
    # undressed primitive look of the blocking pass.
    for side in (-1, 1):
        vest = uv_sphere(f"MILO_VEST_PANEL_{'L' if side < 0 else 'R'}",
                         (side * 0.31, -0.47, 1.32), (0.29, 0.10, 0.66), mats["navy"], root)
        vest.rotation_euler.z = side * math.radians(7)
    torus("MILO_SCARF_COLLAR", (0, -0.02, 1.93), 0.42, 0.105, mats["aqua"], root)
    scarf_tail = cube("MILO_SCARF_TAIL", (0.38, -0.53, 1.63), (0.13, 0.055, 0.40), mats["aqua"], root,
                      rotation=(math.radians(-6), math.radians(8), math.radians(-18)), bevel=0.12)
    for side in (-1, 1):
        uv_sphere(f"MILO_VEST_BUTTON_{'L' if side < 0 else 'R'}", (side * 0.17, -0.615, 1.20),
                  (0.07, 0.035, 0.07), mats["brass"], root, segments=20, rings=12)
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
    # Eyebrows, cheek highlights, a small smile and hair tuft make the face
    # readable in close frames and support emotional performance later.
    for side in (-1, 1):
        brow = cylinder(f"MILO_BROW_{'L' if side < 0 else 'R'}", (side * 0.25, -0.61, 0.31),
                        0.025, 0.23, mats["dark"], head_ctrl,
                        rotation=(0, math.radians(90), side * math.radians(8)), vertices=16)
        uv_sphere(f"MILO_CHEEK_{'L' if side < 0 else 'R'}", (side * 0.37, -0.59, -0.13),
                  (0.10, 0.025, 0.065), mats["pink"], head_ctrl, segments=20, rings=12)
    uv_sphere("MILO_SMILE", (0, -0.675, -0.24), (0.13, 0.035, 0.085), mats["dark"], head_ctrl, segments=24, rings=14)
    uv_sphere("MILO_TONGUE", (0, -0.708, -0.275), (0.065, 0.018, 0.035), mats["pink"], head_ctrl, segments=20, rings=12)
    for i, (x, rot) in enumerate(((-0.13, -18), (0.0, 0), (0.13, 18))):
        tuft = uv_sphere(f"MILO_HAIR_TUFT_{i+1}", (x, 0.02, 0.59), (0.12, 0.09, 0.25), mats["orange"], head_ctrl)
        tuft.rotation_euler.y = math.radians(rot)
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
        uv_sphere(f"MILO_GLOVE_{label}", (side * 0.08, -0.11, -0.64), (0.20, 0.18, 0.20), mats["cream"], ctrl)
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
    notes = []
    spec = (
        ("BLUE", -1.45, "blue"),
        ("GOLD", 0.0, "gold"),
        ("PINK", 1.45, "pink"),
    )
    for index, (label, x, colour) in enumerate(spec):
        root = empty(f"DRUM_{label}", (x, -1.05, 0.33))
        cone(f"DRUM_{label}_BASE", (0, 0, 0.48), 0.56, 0.42, 0.88, mats["wood"], root)
        # Alternating carved staves and metallic collars make these read as
        # crafted instruments rather than three cones with spheres on top.
        for stave in range(8):
            angle = stave * math.tau / 8
            slat = cylinder(f"DRUM_{label}_STAVE_{stave+1}",
                            (math.cos(angle) * 0.47, math.sin(angle) * 0.36, 0.49),
                            0.035, 0.72, mats["wood_light"], root, vertices=12)
            slat.rotation_euler.z = angle
        cap = uv_sphere(f"DRUM_{label}_CAP", (0, 0, 0.94), (0.68, 0.54, 0.30), mats[colour], root)
        torus(f"DRUM_{label}_RIM", (0, 0, 0.88), 0.56, 0.060, mats["brass"], root,
              rotation=(0, 0, 0))
        torus(f"DRUM_{label}_LOWER_COLLAR", (0, 0, 0.24), 0.45, 0.045, mats["brass"], root)
        for spot in range(5):
            angle = spot * math.tau / 5 + index * 0.35
            uv_sphere(f"DRUM_{label}_CAP_SPOT_{spot+1}",
                      (math.cos(angle) * 0.38, math.sin(angle) * 0.27 - 0.34, 1.08),
                      (0.085, 0.035, 0.045), mats["cream"], root, segments=16, rings=10)
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
        for side in (-1, 1):
            leaf = uv_sphere(f"FLOWER_{label}_LEAF_{'L' if side < 0 else 'R'}",
                             (side * 0.19, 0, -0.42), (0.18, 0.07, 0.34), mats["leaf_mint"], bloom)
            leaf.rotation_euler.y = side * math.radians(34)
        bloom.scale = (0.06, 0.06, 0.06)
        flowers.append(bloom)
        note = empty(f"MUSIC_NOTE_{label}_CTRL", (x + (-0.25, 0.0, 0.25)[index], -0.76, 1.52))
        uv_sphere(f"MUSIC_NOTE_{label}_HEAD", (0, 0, 0), (0.13, 0.07, 0.11), mats[colour], note, segments=20, rings=12)
        cylinder(f"MUSIC_NOTE_{label}_STEM", (0.10, 0, 0.28), 0.035, 0.58, mats[colour], note, vertices=16)
        note.scale = (0.001, 0.001, 0.001)
        notes.append(note)
    return drums, flowers, notes


def build_fireflies(mats):
    fireflies = []
    positions = ((-2.6, 0.2, 2.2), (-1.8, 1.1, 2.9), (2.6, 0.4, 2.5), (3.2, 1.2, 3.2), (0.2, 2.2, 3.4))
    for i, position in enumerate(positions):
        fly = uv_sphere(f"FIREFLY_{i+1}", position, (0.075, 0.075, 0.075), mats["yellow"], segments=16, rings=10)
        fly.keyframe_insert("location", frame=1)
        fly.location.x += 0.18 * (-1 if i % 2 else 1)
        fly.location.z += 0.16 + 0.04 * i
        fly.keyframe_insert("location", frame=96)
        fly.location.x -= 0.08 * (-1 if i % 2 else 1)
        fly.location.z -= 0.10
        fly.keyframe_insert("location", frame=192)
        set_interp(fly)
        fireflies.append(fly)
    return fireflies


def animate(scene, milo, head, arms, tail, drums, flowers, notes):
    # Establish -> curious breath -> three clear impacts -> delighted resolve.
    for frame, z, sx, sz in ((1, 0.34, 1.0, 1.0), (34, 0.30, 1.025, 0.97),
                              (52, 0.42, 0.985, 1.035), (64, 0.34, 1.0, 1.0),
                              (192, 0.34, 1.0, 1.0)):
        key(milo, frame, "location", Vector((0.75, 0.45, z)))
        key(milo, frame, "scale", Vector((sx, sx, sz)))
    for frame, pitch, roll in ((1, -2, -7), (36, -5, 6), (65, 1, -5),
                               (92, -2, 2), (124, -2, -2), (164, -5, 0), (192, 0, 0)):
        key(head, frame, "rotation_euler", Vector((math.radians(pitch), 0, math.radians(roll))))

    # Drum contacts use the nearest readable hand. Each performance phrase has
    # anticipation, impact, squash, follow-through, bloom and a rising note.
    hit_specs = ((72, "L", 0), (104, "R", 1), (136, "R", 2))
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
        note = notes[drum_index]
        start = Vector(note.location)
        key(note, hit - 1, "scale", Vector((0.001, 0.001, 0.001)))
        key(note, hit + 3, "scale", Vector((1.0, 1.0, 1.0)))
        key(note, hit + 3, "location", start)
        key(note, hit + 14, "location", start + Vector((0.10 * (-1 if drum_index == 0 else 1), 0, 0.72)))
        key(note, hit + 20, "scale", Vector((0.001, 0.001, 0.001)))
        # A tiny body compression/rebound connects Milo physically to the hit.
        key(milo, hit - 3, "scale", Vector((1.0, 1.0, 1.0)))
        key(milo, hit + 2, "scale", Vector((1.025, 1.025, 0.965)))
        key(milo, hit + 8, "scale", Vector((0.99, 0.99, 1.025)))
        key(milo, hit + 14, "scale", Vector((1.0, 1.0, 1.0)))
    # Ensure each bloom remains open after its own settle.
    for bloom in flowers:
        key(bloom, 192, "scale", Vector((1, 1, 1)))
    # Tail follows the body with slower overlapping action.
    key(tail, 1, "rotation_euler", Vector((0, math.radians(-4), math.radians(-8))))
    key(tail, 54, "rotation_euler", Vector((0, math.radians(6), math.radians(10))))
    key(tail, 102, "rotation_euler", Vector((0, math.radians(-5), math.radians(-11))))
    key(tail, 148, "rotation_euler", Vector((0, math.radians(6), math.radians(12))))
    key(tail, 192, "rotation_euler", Vector((0, 0, math.radians(4))))
    # Final pose: both sticks raised after the third flower has settled.
    for label, arm in arms.items():
        direction = -1 if label == "L" else 1
        key(arm, 154, "rotation_euler", Vector((math.radians(-18), 0, 0)))
        key(arm, 170, "rotation_euler", Vector((math.radians(-72), math.radians(direction * 14), math.radians(direction * 18))))
        key(arm, 192, "rotation_euler", Vector((math.radians(-66), math.radians(direction * 10), math.radians(direction * 14))))
    for obj in (milo, head, arms["L"], arms["R"], tail, *(d[1] for d in drums), *flowers, *notes):
        set_interp(obj)


def build_camera_and_lights(scene):
    target = empty("CAMERA_TARGET", (0.10, 0.25, 1.62))
    bpy.ops.object.camera_add(location=(-0.45, -13.35, 5.70))
    camera = bpy.context.object
    camera.name = "TT_CAMERA"
    camera.data.lens = 49
    camera.data.sensor_width = 36
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = target
    camera.data.dof.aperture_fstop = 3.6
    look_at(camera, target.location)
    camera.keyframe_insert("location", frame=1)
    camera.keyframe_insert("rotation_euler", frame=1)
    camera.location = (0.0, -10.85, 4.82)
    look_at(camera, target.location)
    camera.keyframe_insert("location", frame=192)
    camera.keyframe_insert("rotation_euler", frame=192)
    set_interp(camera)
    scene.camera = camera
    scene.world.use_nodes = True
    world_bg = scene.world.node_tree.nodes.get("Background")
    world_bg.inputs["Color"].default_value = (0.008, 0.012, 0.045, 1)
    world_bg.inputs["Strength"].default_value = 0.18
    # Warm key, cool fill and magenta rim separate Milo from the garden while
    # leaving enough darkness for the practical arch lights to sparkle.
    for name, kind, location, energy, color, size in (
        ("KEY_WARM", "AREA", (-4.0, -5.0, 7.2), 1180, (1.0, 0.46, 0.20), 5.0),
        ("FILL_COOL", "AREA", (4.8, -2.0, 5.3), 920, (0.16, 0.46, 1.0), 4.0),
        ("RIM_MOON", "AREA", (-1.5, 4.2, 6.3), 1080, (0.48, 0.58, 1.0), 3.0),
        ("RIM_MAGENTA", "AREA", (4.0, 2.8, 4.2), 640, (1.0, 0.12, 0.38), 2.5),
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
    # The active instrument casts a short, colored light pulse on each hit.
    for index, (x, hit, color) in enumerate(((-1.45, 72, (0.05, 0.28, 1.0)),
                                              (0.0, 104, (1.0, 0.36, 0.04)),
                                              (1.45, 136, (1.0, 0.04, 0.36)))):
        data = bpy.data.lights.new(f"DRUM_PULSE_{index+1}", "POINT")
        data.color = color
        data.shadow_soft_size = 1.15
        data.energy = 0
        data.keyframe_insert("energy", frame=1)
        data.keyframe_insert("energy", frame=hit - 2)
        data.energy = 520
        data.keyframe_insert("energy", frame=hit + 1)
        data.energy = 80
        data.keyframe_insert("energy", frame=hit + 12)
        data.energy = 30
        data.keyframe_insert("energy", frame=192)
        light = bpy.data.objects.new(f"DRUM_PULSE_{index+1}", data)
        bpy.context.collection.objects.link(light)
        light.location = (x, -0.82, 1.55)
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
        for onset, freq in ((6.15, 659.25), (6.43, 783.99), (6.74, 987.77), (7.08, 1046.50)):
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
    drums, flowers, notes = build_drums_and_flowers(mats)
    build_fireflies(mats)
    animate(scene, milo, head, arms, tail, drums, flowers, notes)
    build_camera_and_lights(scene)
    setup_compositor(scene)
    write_audio()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    if "--build-only" not in sys.argv:
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
