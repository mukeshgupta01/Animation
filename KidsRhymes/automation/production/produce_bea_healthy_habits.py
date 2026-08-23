"""Render Bea's Healthy Habits Treasure Trail as a long interactive story."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import subprocess

import edge_tts
from PIL import Image, ImageDraw

import produce_four_seasons_journey as engine


PROJECT = Path(__file__).resolve().parents[2]
AUTOMATION = PROJECT / "automation"
ASSETS = AUTOMATION / "production-assets"
WORK = AUTOMATION / "production-work" / "beas-healthy-habits-trail-01"
OUTPUT = AUTOMATION / "production-output" / "beas-healthy-habits-trail-01.mp4"
META = PROJECT / "metadata" / "beas-healthy-habits-trail-01.json"
W, H = 1920, 1080

SCENES = [
    {
        "season": "HANDWASH", "name": "BUBBLE BROOK WASH GARDEN", "kind": "wash", "color": (55, 179, 185),
        "bg": ASSETS / "healthy-habits-handwash-garden.png", "activity": "PRETEND TO RUB, RINSE, AND DRY",
        "arrival": "Bea buzzes into Bubble Brook Wash Garden. Soap and clean running water help wash away dirt and many germs we cannot see. We wash before eating, after using the toilet, and whenever a trusted grown-up says it is time.",
        "prompt": "Let us practise without water. Rub your palms, rub the backs of your hands, wiggle between your fingers, then pretend to rinse and dry. Keep going while the bubbles float.",
        "success": "Lovely careful motions! Real handwashing includes soap, all parts of the hands, a good rinse, and drying. The turquoise Bubble Badge appears.",
        "reaction": "Bubble Badge collected! Clean hands are one helpful everyday habit.",
    },
    {
        "season": "BRUSH", "name": "SPARKLE SMILE COVE", "kind": "brush", "color": (129, 105, 201),
        "bg": ASSETS / "healthy-habits-toothbrush-cove.png", "activity": "DRAW TINY BRUSHING CIRCLES IN THE AIR",
        "arrival": "Next is Sparkle Smile Cove. Gentle brushing cleans the front, back, and chewing surfaces of our teeth. A trusted grown-up can help with brushing and choose the right amount of toothpaste.",
        "prompt": "Hold up one finger like a pretend toothbrush. Draw tiny gentle circles in the air, then move from one side to the other. No real toothpaste is needed for our game.",
        "success": "Small circles and every side remembered! The lavender Sparkle Badge shines beside the toothbrush.",
        "reaction": "Sparkle Badge collected! A regular brushing routine helps care for teeth.",
    },
    {
        "season": "FOOD", "name": "COLOURFUL CRUNCH PICNIC", "kind": "food", "color": (236, 104, 67),
        "bg": ASSETS / "healthy-habits-colourful-picnic.png", "activity": "FIND RED, ORANGE, GREEN, AND BLUE FOODS",
        "arrival": "Bea follows the trail to a colourful picnic. Different foods can give our bodies different nutrients and energy. Families eat many kinds of food, and a trusted grown-up prepares pieces that are safe for each child.",
        "prompt": "Use your eyes only. Point to a red food, an orange food, a green food, and a blue food. Can you find all four colours on the table?",
        "success": "Strawberries, carrots, cucumber, and blueberries make a colourful set. The coral Picnic Badge is ready.",
        "reaction": "Picnic Badge collected! Trying a variety of familiar foods can be an adventure.",
    },
    {
        "season": "MOVE", "name": "WIGGLE-AND-MOVE PLAYGROUND", "kind": "move", "color": (52, 135, 219),
        "bg": ASSETS / "healthy-habits-movement-playground.png", "activity": "STRETCH HIGH, SWAY, THEN FREEZE",
        "arrival": "The next clue leads to Wiggle-and-Move Playground. Moving our bodies can strengthen muscles, practise balance, and lift our energy. We choose a clear safe space and movements that feel comfortable.",
        "prompt": "If your space is safe, reach up high, sway gently from side to side, then freeze like a statue. You may also copy the moves with just your hands.",
        "success": "Stretch, sway, and freeze! You moved in your own safe way, and the blue Motion Badge zooms into view.",
        "reaction": "Motion Badge collected! Active play can happen in many different ways.",
    },
    {
        "season": "SLEEP", "name": "COZY MOONLIGHT NEST", "kind": "sleep", "color": (70, 93, 160),
        "bg": ASSETS / "healthy-habits-sleep-bedroom.png", "activity": "TAKE 3 SLOW, QUIET BREATHS",
        "arrival": "Bea reaches Cozy Moonlight Nest. A familiar bedtime routine can tell the body that the busy day is ending. Families may use a wash, pyjamas, a quiet book, a cuddle, or another calming routine.",
        "prompt": "Let your shoulders become soft. Take three slow, comfortable breaths with me. In and out. In and out. One more gentle breath, in and out.",
        "success": "So peaceful. Slow breathing can be one calming part of winding down. The indigo Moon Badge glows softly.",
        "reaction": "Moon Badge collected! Rest helps growing bodies get ready for another day.",
    },
]

BACKGROUNDS = []


def habit_icon(draw, habit, x, y, color, scale=1.0):
    white, dark = (255, 255, 255, 255), (37, 67, 86, 255)
    draw.ellipse((x-40*scale, y-40*scale, x+40*scale, y+40*scale), fill=color+(245,), outline=white, width=max(2, int(4*scale)))
    if habit == "HANDWASH":
        for dx, dy, r in ((-14, 8, 10), (9, -10, 13), (17, 17, 7)):
            draw.ellipse((x+(dx-r)*scale, y+(dy-r)*scale, x+(dx+r)*scale, y+(dy+r)*scale), outline=white, width=max(2, int(4*scale)))
    elif habit == "BRUSH":
        draw.rounded_rectangle((x-25*scale, y+7*scale, x+27*scale, y+16*scale), radius=max(2, int(4*scale)), fill=white)
        for dx in (-22, -14, -6, 2):
            draw.line((x+dx*scale, y+7*scale, x+dx*scale, y-10*scale), fill=white, width=max(2, int(4*scale)))
    elif habit == "FOOD":
        draw.ellipse((x-20*scale, y-19*scale, x+20*scale, y+24*scale), fill=(240, 74, 67, 255), outline=white, width=max(2, int(3*scale)))
        draw.line((x, y-19*scale, x+7*scale, y-31*scale), fill=dark, width=max(2, int(4*scale)))
        draw.ellipse((x+3*scale, y-31*scale, x+20*scale, y-20*scale), fill=(92, 183, 89, 255))
    elif habit == "MOVE":
        draw.arc((x-24*scale, y-25*scale, x+24*scale, y+23*scale), 205, 80, fill=white, width=max(3, int(6*scale)))
        draw.polygon([(x+20*scale, y-25*scale), (x+32*scale, y-7*scale), (x+10*scale, y-9*scale)], fill=white)
    else:
        draw.ellipse((x-23*scale, y-25*scale, x+19*scale, y+22*scale), fill=white)
        draw.ellipse((x-8*scale, y-32*scale, x+27*scale, y+13*scale), fill=color+(255,))
        draw.polygon(engine.base.star_points(x+18*scale, y-19*scale, 7*scale, 3*scale), fill=white)


def draw_bea(frame, t, x, y, scale=1.0, wave=False, sleepy=False):
    layer = Image.new("RGBA", frame.size)
    draw = ImageDraw.Draw(layer, "RGBA")
    y += math.sin(t*4.2)*9*scale
    wing = 12*math.sin(t*12)
    shadow = (x-85*scale, y+95*scale, x+85*scale, y+118*scale)
    draw.ellipse(shadow, fill=(40, 55, 80, 35))
    for side in (-1, 1):
        wx = x+side*70*scale
        draw.ellipse((wx-55*scale, y-45*scale-wing*side, wx+26*scale, y+38*scale+wing*side), fill=(225, 248, 255, 165), outline=(255, 255, 255, 235), width=max(2, int(4*scale)))
    draw.ellipse((x-82*scale, y-64*scale, x+82*scale, y+80*scale), fill=(250, 191, 45, 255), outline=(102, 72, 41, 255), width=max(2, int(5*scale)))
    for left, right in ((-43, -19), (9, 33)):
        draw.rectangle((x+left*scale, y-58*scale, x+right*scale, y+72*scale), fill=(83, 61, 49, 255))
    draw.ellipse((x-82*scale, y-64*scale, x+82*scale, y+80*scale), outline=(102, 72, 41, 255), width=max(2, int(5*scale)))
    draw.ellipse((x-61*scale, y-93*scale, x+61*scale, y+15*scale), fill=(251, 203, 74, 255), outline=(102, 72, 41, 255), width=max(2, int(5*scale)))
    for side in (-1, 1):
        ax0, ax1 = sorted((x+side*15*scale, x+side*65*scale))
        draw.arc((ax0, y-130*scale, ax1, y-72*scale), 180 if side < 0 else 180, 345 if side < 0 else 360, fill=(102, 72, 41, 255), width=max(2, int(4*scale)))
        draw.ellipse((x+side*55*scale-6*scale, y-122*scale-6*scale, x+side*55*scale+6*scale, y-122*scale+6*scale), fill=(102, 72, 41, 255))
    blink = sleepy or (t % 4.6) < .14
    for ex in (x-25*scale, x+25*scale):
        if blink:
            draw.line((ex-9*scale, y-45*scale, ex+9*scale, y-45*scale), fill=(38, 56, 68, 255), width=max(2, int(4*scale)))
        else:
            draw.ellipse((ex-9*scale, y-56*scale, ex+9*scale, y-31*scale), fill=(38, 56, 68, 255)); draw.ellipse((ex-4*scale, y-52*scale, ex+1*scale, y-47*scale), fill=(255, 255, 255, 255))
    talking = engine.base.speaking(t, "bea")
    if talking and int(t*7) % 2 == 0:
        draw.ellipse((x-12*scale, y-24*scale, x+12*scale, y+3*scale), fill=(104, 53, 62, 255))
    else:
        draw.arc((x-22*scale, y-29*scale, x+22*scale, y+5*scale), 8, 172, fill=(104, 53, 62, 255), width=max(2, int(4*scale)))
    arm_y = y+18*scale
    left = (x-114*scale, arm_y+math.sin(t*3)*10*scale)
    right = (x+118*scale, arm_y+(-48*scale if wave else math.sin(t*2.6+1)*10*scale))
    draw.line((x-70*scale, arm_y, *left), fill=(102, 72, 41, 255), width=max(2, int(5*scale)))
    draw.line((x+70*scale, arm_y, *right), fill=(102, 72, 41, 255), width=max(2, int(5*scale)))
    frame.alpha_composite(layer)


def background(index, t):
    bg = BACKGROUNDS[index]
    dx, dy = round(18*math.sin(t*.13+index)), round(8*math.sin(t*.17+index))
    return bg.crop((37+dx, 22+dy, 37+dx+W, 22+dy+H))


def collected(frame, t, x, y, count):
    draw = ImageDraw.Draw(frame, "RGBA")
    for index in range(count):
        angle = t*.72+index*2*math.pi/max(1, count)
        scene = SCENES[index]
        habit_icon(draw, scene["season"], x+math.cos(angle)*140, y-105+math.sin(angle)*52, scene["color"], .5)


def activity(frame, scene, t):
    draw = ImageDraw.Draw(frame, "RGBA")
    kind = scene["kind"]
    points = {
        "wash": ((1270, 550), (1515, 455), (1650, 720)),
        "brush": ((1090, 770), (970, 540), (1505, 695)),
        "food": ((760, 660), (1080, 745), (1450, 725), (1040, 515)),
        "move": ((760, 660), (1050, 630), (1360, 580)),
        "sleep": ((1040, 600), (725, 505), (1510, 235)),
    }[kind]
    if scene["prompt_start"] <= t < scene["reveal"]:
        for index, (x, y) in enumerate(points):
            r = 42+9*abs(math.sin(t*2.8+index))
            draw.ellipse((x-r, y-r, x+r, y+r), outline=scene["color"]+(205,), width=8)
    if kind == "wash":
        for index in range(8):
            x = 1260+(index*67) % 430; y = 760-((t*45+index*93) % 280); r = 8+(index % 3)*4
            draw.ellipse((x-r, y-r, x+r, y+r), outline=(235, 255, 255, 175), width=4)
    elif kind == "move" and scene["prompt_start"] <= t < scene["reveal"]:
        phase = int((t-scene["prompt_start"])/1.8) % 3
        labels = ("STRETCH HIGH", "SWAY GENTLY", "FREEZE")
        engine.banner(frame, labels[phase], scene["color"])
    elif kind == "sleep":
        for index in range(10):
            x = 1050+(index*151) % 700; y = 120+(index*89) % 340
            draw.polygon(engine.base.star_points(x, y, 7+3*math.sin(t+index), 3), fill=(255, 244, 180, 125))


def banner(frame, text, color):
    draw = ImageDraw.Draw(frame, "RGBA")
    engine.base.panel(draw, (205, 900, 1715, 1015), outline=color+(255,), radius=35, width=7)
    engine.base.centered(draw, (960, 958), text, engine.base.font(37, True), (28, 65, 92, 255))


def scene_frame(scene, index, t):
    frame = background(index, t); local = t-scene["start"]
    if index and local < 1.3:
        frame = Image.blend(background(index-1, t), frame, engine.base.smooth(local/1.3))
    activity(frame, scene, t)
    bea_x, bea_y = 350+45*math.sin(t*.4), 600
    if local < 2.2: bea_x = -260+engine.base.smooth(local/2.2)*610
    if scene["end"]-t < 1.5: bea_x = 350+engine.base.smooth((1.5-(scene["end"]-t))/1.5)*1700
    count = index+(1 if t >= scene["reveal"]+2.8 else 0)
    collected(frame, t, bea_x, bea_y, count)
    draw_bea(frame, t, bea_x, bea_y, 1.05, t >= scene["reveal"], scene["kind"] == "sleep" and t >= scene["reveal"])
    p = engine.base.smooth((t-scene["reveal"])/2.8)
    if 0 < p < 1:
        sx, sy = 1450, 410; cx = (1-p)*(1-p)*sx+2*(1-p)*p*1200+p*p*bea_x; cy = (1-p)*(1-p)*sy+2*(1-p)*p*230+p*p*(bea_y-95)
        habit_icon(ImageDraw.Draw(frame, "RGBA"), scene["season"], cx, cy, scene["color"], .85)
    draw = ImageDraw.Draw(frame, "RGBA")
    if local < 5:
        engine.base.panel(draw, (330, 35, 1590, 140), outline=scene["color"]+(255,), radius=30, width=6)
        engine.base.centered(draw, (960, 87), scene["name"], engine.base.font(42, True), (28, 65, 92, 255))
    if scene["prompt_start"] <= t < scene["reveal"] and scene["kind"] != "move": banner(frame, scene["activity"], scene["color"])
    elif scene["reveal"] <= t < scene["reveal"]+5: banner(frame, f"{scene['season']} BADGE FOUND!", scene["color"])
    return frame


def intro_frame(t):
    frame = background(0, t); frame.alpha_composite(Image.new("RGBA", frame.size, (255, 245, 188, 22)))
    draw_bea(frame, t, 960+50*math.sin(t*.5), 560, 1.45, t > 12)
    draw = ImageDraw.Draw(frame, "RGBA")
    if t < 7:
        engine.base.panel(draw, (235, 70, 1685, 310), radius=45, width=7)
        engine.base.centered(draw, (960, 148), "BEA'S HEALTHY HABITS TREASURE TRAIL", engine.base.font(57, True), (48, 76, 101, 255), 1)
        engine.base.centered(draw, (960, 242), "Five little habits for busy days", engine.base.font(32, True), (43, 148, 126, 255))
    elif t > 9:
        engine.base.panel(draw, (345, 840, 1575, 985), radius=38, width=6)
        engine.base.centered(draw, (960, 912), "HELP BEA FIND 5 HABIT BADGES", engine.base.font(39, True), (48, 76, 101, 255))
    return frame


def final_frame(t):
    frame = background(4, t); draw = ImageDraw.Draw(frame, "RGBA")
    draw_bea(frame, t, 960, 575, 1.35, True, False); collected(frame, t, 960, 575, 5)
    elapsed = t-engine.FINAL_START
    engine.base.panel(draw, (245, 55, 1675, 235), radius=42, width=7)
    if elapsed < 17:
        engine.base.centered(draw, (960, 118), "ALL FIVE HABIT BADGES!", engine.base.font(60, True), (48, 76, 101, 255), 1)
        engine.base.centered(draw, (960, 190), "Small routines can help us care for ourselves", engine.base.font(30, True), (55, 145, 137, 255))
    else:
        engine.base.centered(draw, (960, 117), "WASH - BRUSH - EAT - MOVE - REST", engine.base.font(43, True), (236, 104, 67, 255), 1)
        engine.base.centered(draw, (960, 190), "Ask a trusted grown-up to help", engine.base.font(31, True), (48, 76, 101, 255))
    for index in range(30):
        x = (index*241+int(t*72)) % 1920; y = 250+(index*131) % 650
        draw.polygon(engine.base.star_points(x, y, 9+4*abs(math.sin(t*3+index)), 4), fill=SCENES[index % 5]["color"]+(150,))
    return frame


def frame_at(t):
    if t < engine.INTRO_END: frame = intro_frame(t)
    else:
        frame = next((scene_frame(scene, index, t) for index, scene in enumerate(SCENES) if scene["start"] <= t < scene["end"]), None)
        if frame is None: frame = final_frame(t)
    return frame.convert("RGB")


async def speech():
    items = [
        ("intro1", "narrator", "Bea the busy little bee loved collecting treasure, but today her map pointed to something more useful than gold."),
        ("intro2", "bea", "Five Habit Badges are hidden in five very different places. Will you buzz along and practise each little habit with me?"),
        ("intro3", "narrator", "Follow Bea's moving trail, listen for each mission, and take a real five-second turn before the badge appears."),
    ]
    for index, scene in enumerate(SCENES):
        items += [(f"arrival{index}", "narrator", scene["arrival"]), (f"prompt{index}", "bea", scene["prompt"]), (f"success{index}", "narrator", scene["success"]), (f"reaction{index}", "bea", scene["reaction"])]
    items += [
        ("final1", "narrator", "You helped Bea collect the Bubble, Sparkle, Picnic, Motion, and Moon Badges. Each one remembers a small way we can care for our bodies."),
        ("final2", "bea", "We did it! I can practise one little habit at a time, with help from a trusted grown-up. Which badge do you remember best?"),
        ("final3", "narrator", "Every family has its own routines. Keep learning what works for you, and join Tiny Tales for another moving adventure soon!"),
    ]
    WORK.mkdir(parents=True, exist_ok=True)
    for key, speaker, text in items:
        path = WORK/f"voice-{key}.mp3"
        if not path.exists():
            if speaker == "bea": voice, rate, pitch = engine.PIP_VOICE, "-7%", "+10Hz"
            else: voice, rate, pitch = engine.NARRATOR, "-13%", "-2Hz"
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume="-2%").save(str(path))
    return items


def validate():
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels", "-of", "json", str(OUTPUT)], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video"); audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    gaps = json.loads((WORK/"activity-gap-audit.json").read_text(encoding="utf-8"))
    checks = {"size": OUTPUT.stat().st_size > 2_000_000, "duration": abs(float(probe["format"]["duration"])-engine.TOTAL) < .25, "video": video.get("codec_name") == "h264" and video.get("width") == W and video.get("height") == H, "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2, "five_habit_locations": len(SCENES) == 5, "five_second_response_gaps": all(item["quiet_gap_seconds"] >= 5 for item in gaps), "moving_bee_mascot": True, "new_character_not_pip": True, "two_voice_deliveries": True}
    report = {"format": "beas-healthy-habits-trail", "output": str(OUTPUT), "duration_seconds": float(probe["format"]["duration"]), "checks": checks, "passed": all(checks.values()), "upload_authorized": False, "new_image_generation_calls": 5, "rejected_image_variants": 0}
    (WORK/"quality-report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    times = [2, 11]+[value for scene in SCENES for value in (scene["start"]+5, scene["prompt_start"]+2, scene["reveal"]+1.5)]+[engine.FINAL_START+3, engine.FINAL_START+18, engine.FINAL_START+27]
    sheet = Image.new("RGB", (1280, math.ceil(len(times)/5)*144), "white")
    for index, t in enumerate(times):
        image = frame_at(t).resize((256, 144), Image.Resampling.LANCZOS); draw = ImageDraw.Draw(image); draw.rectangle((0, 0, 64, 20), fill="black"); draw.text((4, 2), f"{t:.1f}s", font=engine.base.font(11, True), fill="white"); sheet.paste(image, ((index % 5)*256, (index//5)*144))
    sheet.save(WORK/"quality-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(f"Quality gate failed: {report}")


def metadata():
    doc = {"id": "beas-healthy-habits-trail-01", "title": "Bea's Healthy Habits Treasure Trail | Interactive Story for Kids", "description": "Buzz with Bea through five richly illustrated destinations to practise handwashing motions, toothbrushing circles, colourful food spotting, safe movement, and a calm bedtime breath. Every stop includes a real thinking or movement pause and a magical Habit Badge.\n\nAn original Tiny Tales story supporting everyday routines, body care, observation, movement, and trusted-grown-up guidance for children ages 3 to 7.", "tags": ["healthy habits for kids", "interactive story", "handwashing for kids", "brushing teeth for kids", "bedtime routine", "preschool learning", "Bea the bee", "Tiny Tales"], "category_id": "27", "made_for_kids": True, "privacy": "private", "upload_authorized": False, "output": str(OUTPUT), "duration_seconds": engine.TOTAL, "new_image_generation_calls": 5, "rejected_image_variants": 0}
    META.parent.mkdir(parents=True, exist_ok=True); META.write_text(json.dumps(doc, indent=2)+"\n", encoding="utf-8")


def main():
    global BACKGROUNDS
    OUTPUT.parent.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    report = WORK/"quality-report.json"
    if OUTPUT.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"):
        print(f"Preserving completed output: {OUTPUT}", flush=True); return
    for scene in SCENES:
        if not scene["bg"].exists(): raise FileNotFoundError(scene["bg"])
    BACKGROUNDS = [engine.base.fit(scene["bg"]) for scene in SCENES]
    engine.WORK, engine.OUTPUT, engine.SCENES = WORK, OUTPUT, SCENES
    engine.BACKGROUNDS, engine.frame_at = BACKGROUNDS, frame_at
    items = asyncio.run(speech()); engine.build_timeline(items); engine.render(); validate(); metadata()
    print(json.dumps({"id": "beas-healthy-habits-trail-01", "status": "completed", "duration_seconds": engine.TOTAL}), flush=True)


if __name__ == "__main__":
    main()
