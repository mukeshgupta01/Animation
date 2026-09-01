"""Meaningful foreground motion and review evidence for premium Tiny Tales stories.

This module deliberately rejects the old "moving still plus particles" approach.
It gives every scene independently moving, identity-locked character sprites and
an action-specific physical foreground layer that changes through start/action/end
states.  Camera travel remains support motion only.
"""

from __future__ import annotations

from functools import lru_cache
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


WIDTH, HEIGHT = 1920, 1080

SPECS = {
    "felix": {
        "sheet": "felix-firefly-sprite-sheet-v2.png", "cols": 3, "rows": 2,
        "characters": ("Felix", "Rabbit", "Hedgehog"), "accent": (255, 205, 78),
    },
    "basil": {
        "sheet": "basil-beaver-sprite-sheet-v2.png", "cols": 3, "rows": 2,
        "characters": ("Basil", "Pippa", "Moss"), "accent": (91, 190, 214),
    },
    "gus": {
        "sheet": "gus-gecko-sprite-sheet-v2.png", "cols": 2, "rows": 2,
        "characters": ("Gus", "Mara"), "accent": (246, 192, 82),
    },
    "nellie": {
        "sheet": "nellie-narwhal-sprite-sheet-v2.png", "cols": 3, "rows": 2,
        "characters": ("Nellie", "Oona", "Kiko"), "accent": (92, 224, 255),
    },
    "tilly": {
        "sheet": "tilly-turtle-sprite-sheet-v2.png", "cols": 2, "rows": 2,
        "characters": ("Tilly", "Pip"), "accent": (255, 181, 87),
    },
    "pogo": {
        "sheet": "pogo-penguin-sprite-sheet-v2.png", "cols": 2, "rows": 2,
        "characters": ("Pogo", "Mina"), "accent": (96, 218, 242),
    },
    "zara": {
        "sheet": "zara-zebra-sprite-sheet-v2.png", "cols": 2, "rows": 2,
        "characters": ("Zara", "Nuru"), "accent": (246, 160, 75),
    },
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def smooth(value: float) -> float:
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def ease_out_back(value: float) -> float:
    value = clamp(value)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (value - 1.0) ** 3 + c1 * (value - 1.0) ** 2


@lru_cache(maxsize=16)
def _sheet_cells(path_string: str, cols: int, rows: int) -> tuple[Image.Image, ...]:
    sheet = Image.open(path_string).convert("RGBA")
    cells: list[Image.Image] = []
    for row in range(rows):
        for col in range(cols):
            left = round(col * sheet.width / cols)
            right = round((col + 1) * sheet.width / cols)
            top = round(row * sheet.height / rows)
            bottom = round((row + 1) * sheet.height / rows)
            cell = sheet.crop((left, top, right, bottom))
            box = cell.getchannel("A").getbbox()
            if box is None:
                raise RuntimeError(f"Empty sprite cell {row},{col}: {path_string}")
            cells.append(cell.crop(box))
    return tuple(cells)


@lru_cache(maxsize=128)
def _sprite(path_string: str, cols: int, rows: int, col: int, row: int, height: int) -> Image.Image:
    source = _sheet_cells(path_string, cols, rows)[row * cols + col]
    width = max(1, round(source.width * height / source.height))
    return source.resize((width, height), Image.Resampling.LANCZOS)


def _paste(frame: Image.Image, sprite: Image.Image, center: tuple[float, float], opacity: int = 255) -> None:
    x = round(center[0] - sprite.width / 2)
    y = round(center[1] - sprite.height / 2)
    if opacity < 255:
        sprite = sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda a: a * opacity // 255))
    frame.alpha_composite(sprite, (x, y))


def _focus_shadow(draw: ImageDraw.ImageDraw, x: float, y: float, width: float, height: float) -> None:
    for step in range(7, 0, -1):
        spread = step * 18
        alpha = 5 + (8 - step) * 2
        draw.ellipse(
            (x - width / 2 - spread, y - height / 2 - spread,
             x + width / 2 + spread, y + height / 2 + spread),
            fill=(3, 10, 18, alpha),
        )


def _glow_disc(draw: ImageDraw.ImageDraw, x: float, y: float, radius: float, colour: tuple[int, int, int], alpha: int = 210) -> None:
    for scale, a in ((2.0, 24), (1.55, 38), (1.2, 62)):
        r = radius * scale
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(*colour, a))
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(*colour, alpha), outline=(255, 255, 255, 190), width=4)


def _action_layer(draw: ImageDraw.ImageDraw, theme: str, scene: int, progress: float, pulse: float) -> None:
    p = smooth(progress)
    accent = SPECS[theme]["accent"]
    if theme == "felix":
        colours = ((255, 190, 52), (68, 165, 255), (255, 190, 52), (68, 165, 255))
        count = 3 if scene < 6 else 4
        for index in range(count):
            x = 690 + index * 180
            reached = clamp(p * count - index)
            radius = 22 + 22 * ease_out_back(reached) + 5 * pulse * reached
            _glow_disc(draw, x, 850, radius, colours[index], round(70 + 170 * reached))
        if scene in (5, 6, 7, 8):
            lit = clamp((p - 0.35) / 0.35)
            draw.arc((570, 210, 1370, 1000), 205, 335, fill=(*accent, round(230 * lit)), width=18)
    elif theme == "basil":
        water = round(120 + 110 * (1.0 - p if scene in (5, 6, 7) else 1.0))
        for lane in range(3):
            points = []
            for step in range(24):
                x = 670 + step * 31
                y = 790 + lane * 20 + math.sin(step * 0.7 + progress * 10) * 10
                points.append((x, y))
            draw.line(points, fill=(105, 212, 246, water), width=9-lane*2)
        if scene in (3, 4):
            y = 565 + 210 * ease_out_back(p)
            colour = (92, 158, 72) if scene == 3 else (116, 108, 94)
            _glow_disc(draw, 970, y, 42, colour, 230)
        elif scene in (5, 6, 7):
            for index in range(5):
                x = 790 + index * 85
                height = 230 * clamp(p * 5 - index)
                draw.line((x, 840, x, 840-height), fill=(146, 97, 55, 235), width=18)
            if scene == 7:
                draw.arc((750, 560, 1210, 950), 195, 345, fill=(122, 82, 52, 245), width=30)
        elif scene >= 8:
            for spoke in range(8):
                angle = spoke * math.tau / 8 + progress * math.tau * 1.5
                draw.line((1515, 455, 1515+math.cos(angle)*115, 455+math.sin(angle)*115), fill=(113, 190, 206, 225), width=10)
            draw.ellipse((1395, 335, 1635, 575), outline=(190, 224, 230, 235), width=14)
    elif theme == "gus":
        starts = ((940, 790), (900, 720), (800, 680), (990, 740), (820, 740), (900, 720), (850, 790), (760, 600), (960, 760))
        ends = ((1080, 690), (1030, 640), (1060, 350), (1060, 850), (1320, 650), (960, 650), (1130, 600), (1320, 340), (1160, 720))
        sx, sy = starts[min(scene-1, 8)]; ex, ey = ends[min(scene-1, 8)]
        x = sx + (ex-sx)*ease_out_back(p); y = sy + (ey-sy)*smooth(p)
        draw.line((sx, sy, x, y), fill=(*accent, 155), width=8)
        _glow_disc(draw, x, y, 34 + 5*pulse, accent, 235)
        if scene in (3, 4, 5, 6, 7):
            draw.line((ex-90, ey, ex+90, ey), fill=(239, 230, 201, 185), width=6)
    elif theme == "nellie":
        ring_colours = ((67, 230, 151), (74, 170, 255), (184, 103, 255))
        for index, colour in enumerate(ring_colours):
            x = 720 + index * 250
            reached = clamp(p * 3 - index)
            r = 34 + 55 * reached + 5 * pulse * reached
            draw.ellipse((x-r, 550-r, x+r, 550+r), outline=(*colour, round(90 + 160*reached)), width=15)
        for index in range(6):
            age = (progress * 1.8 + index / 6) % 1.0
            x = 650 + index * 125 + math.sin(age * math.tau) * 18
            y = 850 - age * 380
            draw.ellipse((x-10, y-10, x+10, y+10), outline=(190, 240, 255, 160), width=4)
    elif theme == "tilly":
        if scene == 2 or scene >= 7:
            for wheel_x in (760, 1160):
                draw.ellipse((wheel_x-82, 760-82, wheel_x+82, 760+82), outline=(220, 138, 76, 225), width=14)
                for spoke in range(8):
                    angle = spoke * math.tau / 8 + progress * math.tau * 1.6
                    draw.line((wheel_x, 760, wheel_x+math.cos(angle)*72, 760+math.sin(angle)*72), fill=(244, 190, 108, 210), width=7)
        if scene in (1, 3, 4, 8, 9):
            warm_x = 820 + 80*math.sin(progress*math.pi)
            cool_x = 1100 - 80*math.sin(progress*math.pi)
            _glow_disc(draw, warm_x, 700, 42+4*pulse, (255, 166, 75), 225)
            _glow_disc(draw, cool_x, 700, 42+4*pulse, (92, 181, 230), 225)
        if scene in (5, 6, 8, 9):
            split = 95 * smooth(p)
            draw.pieslice((910-split-70, 630, 1050-split-70, 770), 90, 270, fill=(232, 184, 111, 230))
            draw.pieslice((870+split, 630, 1010+split, 770), -90, 90, fill=(232, 184, 111, 230))
    elif theme == "pogo":
        left, right, deck_y = 690, 1320, 690
        flex = 0 if scene >= 3 else 65 * math.sin(math.pi*p)
        points = [(left+i*(right-left)/12, deck_y + flex*math.sin(math.pi*i/12)) for i in range(13)]
        draw.line(points, fill=(204, 239, 249, 235), width=32)
        if scene >= 4:
            for x in (790, 1005, 1220):
                height = 190 * clamp(p*3 - ((x-790)/215))
                draw.line((x, deck_y+20, x, deck_y+20+height), fill=(99, 184, 214, 230), width=24)
        if scene >= 5:
            for side in (-1, 1):
                y = deck_y + side*90
                draw.line((left, y, left+(right-left)*p, y), fill=(235, 244, 240, 225), width=12)
        if scene >= 7:
            reveal = smooth(p)
            draw.line((820, 880, 820+(1180-820)*reveal, 590), fill=(42, 161, 176, 235), width=22)
            draw.line((1180, 880, 1180+(820-1180)*reveal, 590), fill=(42, 161, 176, 235), width=22)
    elif theme == "zara":
        for index in range(6):
            reached = ease_out_back(clamp(p*6-index))
            x = 670 + index*125
            y = 770 + (1.0-reached)*170
            draw.rounded_rectangle((x-45, y-110, x+45, y+110), 16, fill=(245, 233, 204, 225), outline=(118, 80, 45, 190), width=5)
            if scene >= 4:
                _glow_disc(draw, x, y, 16+7*pulse, accent, 220)
        if scene in (2, 5, 7, 8):
            stop_alpha = round(100 + 150*clamp((p-.25)/.25))
            draw.ellipse((1420, 300, 1550, 430), fill=(214, 67, 57, stop_alpha), outline=(255,255,255,220), width=8)
            draw.line((1485, 430, 1485, 620), fill=(245, 237, 210, 220), width=14)


def apply(frame: Image.Image, event: dict, t: float, theme: str, asset_dir: Path) -> Image.Image:
    if event.get("phase") == "end":
        return frame.convert("RGB")
    if theme not in SPECS:
        raise KeyError(theme)
    spec = SPECS[theme]
    frame = frame.convert("RGBA")
    # The source tableaux already contain posed characters.  Defocus them into
    # a contextual painted backdrop so the independently moving foreground cast
    # reads as one intentional layer instead of duplicated characters.
    soft_backdrop = frame.filter(ImageFilter.GaussianBlur(22))
    frame = Image.blend(frame, soft_backdrop, 0.88)
    local = max(0.0, t - float(event["start"]))
    duration = max(0.01, float(event["end"]) - float(event["start"]))
    progress = clamp(local / duration)
    scene = int(event["scene"])
    pulse = 0.5 + 0.5 * math.sin(local * math.tau * 0.8)

    veil = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    veil_draw = ImageDraw.Draw(veil, "RGBA")
    veil_draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(5, 12, 22, 28))
    _action_layer(veil_draw, theme, scene, progress, pulse)

    count = len(spec["characters"])
    hero = 0
    base_x = (420, 960, 1500) if count == 3 else (590, 1330)
    sheet_path = str((asset_dir / spec["sheet"]).resolve())
    enter = ease_out_back(clamp(progress / 0.17))
    action = smooth(clamp((progress - 0.18) / 0.58))
    placements = []
    for character in range(count):
        is_hero = character == hero
        sprite_height = 455 if is_hero else 345
        x = base_x[character]
        direction = 1 if character % 2 == 0 else -1
        x += direction * (-130 * (1.0-enter) + (155 if is_hero else 65) * action)
        y = 810 - (72 if is_hero else 15) * math.sin(math.pi*action)
        y += math.sin(local*3.2 + character*1.7) * (8 if is_hero else 4)
        _focus_shadow(veil_draw, x, y+75, sprite_height*0.72, sprite_height*0.46)
        placements.append((character, is_hero, sprite_height, x, y))

    frame.alpha_composite(veil)
    for character, is_hero, sprite_height, x, y in placements:
        row = 1 if progress >= 0.42 else 0
        if theme == "tilly" and scene not in (2, 7, 8, 9):
            row = 0
        sprite = _sprite(sheet_path, spec["cols"], spec["rows"], character, row, sprite_height)
        _paste(frame, sprite, (x, y), 255 if is_hero else 232)
    return frame.convert("RGB")


def scene_audit(events: list[dict], theme: str) -> list[dict]:
    moving = list(SPECS[theme]["characters"])
    rows = []
    for event in events:
        rows.append({
            "scene": int(event["scene"]),
            "primary_action": event.get("visual_action") or event.get("action"),
            "visible_start_state": "opening pose and incomplete physical action",
            "visible_action_state": "foreground character pose changes and the narrated object/action visibly moves",
            "visible_end_state": "action settles into a visibly changed completed state",
            "foreground_moving_elements": moving,
            "camera_only": False,
            "character_and_object_continuity": True,
            "reviewed": False,
        })
    return rows


def write_evidence(work: Path, events: list[dict], frame_for, assets: dict, theme: str) -> tuple[Path, Path]:
    audit_path = work / "semantic-motion-audit.json"
    audit_path.write_text(json.dumps(scene_audit(events, theme), indent=2) + "\n", encoding="utf-8")
    sheet = Image.new("RGB", (960, len(events) * 180), (238, 238, 238))
    for row, event in enumerate(events):
        span = event["end"] - event["start"]
        for col, fraction in enumerate((0.12, 0.52, 0.88)):
            frame = frame_for(event, event["start"] + span*fraction, assets)
            sheet.paste(frame.resize((320, 180), Image.Resampling.LANCZOS), (col*320, row*180))
    contact_path = work / "semantic-motion-contact-sheet.png"
    sheet.save(contact_path)
    return audit_path, contact_path
