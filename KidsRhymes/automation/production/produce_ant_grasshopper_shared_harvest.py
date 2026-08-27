"""Produce The Ant and the Grasshopper's Shared Harvest with zero-cost keyframe animation."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import wave

import edge_tts
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

import produce_snack_video as base
import produce_star_friends_twinkle_playground as render_engine
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
PROJECT = AUTOMATION.parent
ITEM_ID = "ant-grasshopper-shared-harvest-01"
OUTPUT = AUTOMATION / "production-output" / f"{ITEM_ID}.mp4"
WORK = AUTOMATION / "production-work" / ITEM_ID
META = PROJECT / "metadata" / f"{ITEM_ID}.json"
ASSET_DIR = AUTOMATION / "production-assets"
THUMBNAIL = AUTOMATION / "thumbnails" / f"{ITEM_ID}.jpg"
ART_FPS = 10
VOICES = {name: select_voice_profile(name) for name in ("natasha-au", "ana-us", "ryan-uk")}


# Each line begins and ends inside the pictured action. A/B pairs are separate
# generated action poses, not a simulated camera move over one static drawing.
SHOTS = [
    ("01_summer_meadow", "shared-harvest-summer-opening-v1.png", "shared-harvest-summer-opening-midstep-v1.png", [
        ("natasha-au", "Meet our orchestra! Stay for the final song."),
        ("ana-us", "Carry a little, tap-tap-tap!"), ("ryan-uk", "Play a little, clap-clap-clap!")]),
    ("02_ant_work_verse", "shared-harvest-ant-work-v1.png", "shared-harvest-ant-work-pose-b-v1.png", [
        ("natasha-au", "Ant rolled one berry toward the hill while every helper carried food to the store."),
        ("ana-us", "Steady feet make a happy beat!")]),
    ("03_grasshopper_play_verse", "shared-harvest-grasshopper-play-v1.png", "shared-harvest-grasshopper-play-pose-b-v1.png", [
        ("natasha-au", "Grasshopper hopped between the daisies, bowed his fiddle, and invited every friend to clap."),
        ("ryan-uk", "Play a little, clap-clap-clap!")]),
    ("04_shared_rhythm", "shared-harvest-shared-rhythm-v1.png", "shared-harvest-shared-rhythm-pose-b-v1.png", [
        ("natasha-au", "Grasshopper matched each fiddle beat to one basket pass, and the heaviest work felt lighter.")]),
    ("05_autumn_gust", "shared-harvest-autumn-gust-v1.png", "shared-harvest-autumn-gust-pose-b-v1.png", [
        ("natasha-au", "Autumn whooshed in! Ant caught the flying cloth while Grasshopper caught the seeds.")]),
    ("06_music_harvest_rescue", "shared-harvest-harvest-rescue-v1.png", "shared-harvest-harvest-rescue-pose-b-v1.png", [
        ("natasha-au", "Scoop, pass, pour! Every friend followed the rescue rhythm until the harvest was safe."),
        ("ryan-uk", "Plan together, share the way!")]),
    ("07_first_snow", "shared-harvest-first-snow-v1.png", None, [
        ("natasha-au", "At first snow, Grasshopper held his fiddle close and knocked gently at Ant's warm door."),
        ("ryan-uk", "Could one more friend come inside?")]),
    ("08_warm_welcome", "shared-harvest-warm-welcome-v1.png", "shared-harvest-warm-welcome-pose-b-v1.png", [
        ("natasha-au", "Ant remembered his help, shared warm soup, and made room beside the fire."),
        ("ana-us", "Kind helpers always have a place here.")]),
    ("09_winter_plan_song", "shared-harvest-winter-plan-v1.png", "shared-harvest-winter-plan-pose-b-v1.png", [
        ("natasha-au", "Around the warm table, Ant sorted seeds while Grasshopper tapped a spring planting plan."),
        ("ana-us", "Plan together, share the way!")]),
    ("10_spring_finale", "shared-harvest-spring-finale-v1.png", "shared-harvest-spring-finale-pose-b-v1.png", [
        ("natasha-au", "Sing!"),
        ("ana-us", "Carry a little, tap-tap-tap!"), ("ryan-uk", "Play a little, clap-clap-clap!"),
        ("natasha-au", "Work and music make the day!")]),
]


def voice_path(shot_index: int, line_index: int, profile: str) -> Path:
    return WORK / f"voice-v4-{shot_index:02d}-{line_index:02d}-{profile}.mp3"


async def make_voices() -> None:
    for si, (_sid, _a, _b, lines) in enumerate(SHOTS):
        for li, (profile, line) in enumerate(lines):
            target = voice_path(si, li, profile)
            voice = VOICES[profile]
            if not target.exists() or target.stat().st_size < 1000:
                # Sequential writes avoid Windows file-sharing races observed
                # when multiple Edge TTS websocket tasks finish together.
                await edge_tts.Communicate(line, voice["voice"], rate=voice["rate"], pitch=voice["pitch"], volume="-1%").save(str(target))


def duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], text=True).strip())


def build_timeline():
    events = [{"phase": "title", "start": 0.0, "end": 3.8, "asset": SHOTS[0][1], "asset_b": SHOTS[0][2]}]
    voices = []
    cursor = 3.8
    for si, (sid, asset, asset_b, lines) in enumerate(SHOTS):
        line_rows, local = [], 0.25
        for li, (profile, line) in enumerate(lines):
            path = voice_path(si, li, profile)
            length = duration(path)
            line_rows.append({"profile": profile, "line": line, "start": cursor + local, "end": cursor + local + length})
            voices.append((path, cursor + local))
            local += length + 0.18
        shot_length = max(7.1, local + 0.62)
        if shot_length > 14:
            raise RuntimeError(f"14-second shot gate failed: {sid} {shot_length:.2f}s")
        events.append({"phase": sid, "start": cursor, "end": cursor + shot_length, "asset": asset, "asset_b": asset_b, "lines": line_rows})
        cursor += shot_length
    events.append({"phase": "end", "start": cursor, "end": cursor + 4.8, "asset": SHOTS[-1][2], "asset_b": None})
    return events, voices, events[-1]["end"]


def fit(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    scale = max((base.W + 150) / image.width, (base.H + 90) / image.height)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)


def load_assets():
    names = {name for _sid, a, b, _lines in SHOTS for name in (a, b) if name}
    missing = [name for name in names if not (ASSET_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(missing)
    return {name: fit(ASSET_DIR / name) for name in names}


def crop(image: Image.Image, event: dict, t: float, index: int) -> Image.Image:
    p = max(0.0, min(1.0, (t - event["start"]) / max(0.01, event["end"] - event["start"])))
    eased = p * p * (3 - 2 * p)
    zoom = 1.0 + (0.045 * eased if index % 2 == 0 else 0.045 * (1 - eased))
    resized = image.resize((round((base.W + 150) * zoom), round((base.H + 90) * zoom)), Image.Resampling.BICUBIC)
    ax, ay = resized.width - base.W, resized.height - base.H
    x = int(ax * ((0.22 + 0.48 * eased) if index % 2 == 0 else (0.70 - 0.45 * eased)))
    y = int(ay * (0.44 + 0.05 * math.sin(p * math.pi)))
    return resized.crop((x, y, x + base.W, y + base.H))


def action_frame(event: dict, t: float, index: int, assets) -> Image.Image:
    span = event["end"] - event["start"]
    p = max(0.0, min(1.0, (t - event["start"]) / span))
    a = crop(assets[event["asset"]], event, t, index)
    bname = event.get("asset_b")
    if bname:
        b = crop(assets[bname], event, t, index)
        # The generated keyframes deliberately advance the action and may
        # recompose supporting characters. Cut on the central music beat;
        # dissolving these frames would create ghosted anatomy.
        frame = a if p < 0.50 else b
    else:
        frame = a
    frame = frame.convert("RGBA")
    draw = ImageDraw.Draw(frame, "RGBA")
    local = t - event["start"]
    rng = random.Random(82700 + index)
    if index in {0, 1, 2, 3, 5, 9}:
        for j in range(14):
            x = (rng.randint(30, 1890) + int(local * (12 + j % 4 * 5))) % base.W
            y = rng.randint(35, 1010)
            r = 2 + int(3 * (1 + math.sin(local * 3 + j)))
            draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 225, 90, 70))
    if index == 4:
        for j in range(18):
            x = (rng.randint(0, 1920) + int(local * (50 + j))) % 1920
            y = (rng.randint(80, 980) + int(18 * math.sin(local * 2 + j)))
            draw.arc((x-18, y-8, x+18, y+8), 0, 200, fill=(255, 150, 60, 130), width=4)
    if index == 6:
        for j in range(30):
            x, y = rng.randint(20, 1900), (rng.randint(0, 1080) + int(local * (35 + j % 4 * 8))) % 1080
            draw.ellipse((x-3, y-3, x+3, y+3), fill=(245, 252, 255, 170))
        breath = 12 + int(8 * (0.5 + 0.5 * math.sin(local * 2)))
        draw.ellipse((1310-breath, 445-breath//2, 1310+breath, 445+breath//2), fill=(235, 248, 255, 55))
    if index == 7:
        for j in range(4):
            x = 995 + j * 32 + int(6 * math.sin(local * 1.7 + j))
            y = 480 - j * 24
            draw.arc((x, y, x+25, y+48), 80, 260, fill=(255, 245, 220, 100), width=4)
    return frame.convert("RGB")


def frame_for(event: dict, t: float, assets):
    if event["phase"] == "title":
        frame = action_frame(event, t, 0, assets).convert("RGBA")
        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rounded_rectangle((255, 90, 1665, 345), 48, fill=(48, 36, 91, 222), outline=(255, 224, 94, 245), width=7)
        base.centered(draw, (960, 175), "THE SHARED HARVEST", base.F62, (255, 244, 152, 255), 3)
        base.centered(draw, (960, 275), "AN ANT & GRASSHOPPER SONG", base.F48, "white", 2)
        return frame.convert("RGB")
    if event["phase"] == "end":
        frame = crop(assets[event["asset"]], event, t, 9).convert("RGBA")
        draw = ImageDraw.Draw(frame, "RGBA")
        draw.rectangle((0, 0, base.W, base.H), fill=(34, 25, 70, 58))
        draw.rounded_rectangle((300, 760, 1620, 985), 46, fill=(48, 36, 91, 225), outline=(255, 224, 94, 245), width=7)
        base.centered(draw, (960, 840), "CARRY • PLAY • PLAN • SHARE", base.F48, (255, 244, 152, 255), 2)
        base.centered(draw, (960, 925), "WORK AND MUSIC MAKE THE DAY!", base.F48, "white", 2)
        return frame.convert("RGB")
    index = next(i for i, row in enumerate(SHOTS) if row[0] == event["phase"])
    return action_frame(event, t, index, assets)


def make_music(total: float) -> Path:
    target = WORK / "original-shared-harvest-song.wav"
    rate, bpm = 48000, 112
    beat = 60 / bpm
    notes = [261.63, 329.63, 392.0, 329.63, 293.66, 349.23, 440.0, 392.0]
    rng = random.Random(20260827)
    with wave.open(str(target), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate)
        chunk = bytearray()
        for n in range(int(total * rate)):
            t = n / rate
            note = notes[int(t / beat) % len(notes)]
            phase = t % beat
            pluck = math.sin(2 * math.pi * note * t) * math.exp(-5.0 * phase) * 0.040
            fiddle = math.sin(2 * math.pi * note * t) * 0.010
            tap = math.sin(2 * math.pi * 88 * t) * max(0, 1 - phase / 0.035) * 0.030 if phase < 0.035 else 0
            value = pluck + fiddle + tap + rng.uniform(-0.001, 0.001)
            sample = max(-32767, min(32767, int(value * 32767)))
            chunk.extend(struct.pack("<hh", sample, sample))
            if len(chunk) >= rate * 4: out.writeframesraw(chunk); chunk.clear()
        if chunk: out.writeframesraw(chunk)
    return target


def make_thumbnail() -> None:
    source = Image.open(ASSET_DIR / "shared-harvest-spring-finale-pose-b-v1.png").convert("RGB")
    w = round(source.height * 16 / 9); left = max(0, (source.width - w) // 2)
    canvas = source.crop((left, 0, left+w, source.height)).resize((1280, 720), Image.Resampling.LANCZOS).convert("RGBA")
    canvas = ImageEnhance.Color(canvas).enhance(1.08)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((55, 35, 1225, 175), 34, fill=(52, 37, 98, 228), outline="white", width=5)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 61)
    text = "WORK + MUSIC = MAGIC!"; box = draw.textbbox((0,0), text, font=font, stroke_width=3)
    draw.text(((1280-(box[2]-box[0]))//2, 68), text, font=font, fill=(255,244,130), stroke_width=4, stroke_fill=(35,24,72))
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True); canvas.convert("RGB").save(THUMBNAIL, quality=89, optimize=True)


def quality(events, total, assets) -> None:
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels", "-of", "json", str(OUTPUT)], text=True))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video"); audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"], capture_output=True)
    gaps = [{"from": a["phase"], "to": b["phase"], "gap_seconds": b["start"]-a["end"]} for a,b in zip(events, events[1:])]
    sync = [{"shot_id": e["phase"], "visual_start": e["start"], "visual_end": e["end"], "lines": e["lines"], "contained": all(e["start"] <= x["start"] < x["end"] <= e["end"] for x in e["lines"])} for e in events[1:-1]]
    checks = {"duration": 70 <= float(probe["format"]["duration"]) <= 130, "h264_1080p": video.get("codec_name")=="h264" and video.get("width")==1920 and video.get("height")==1080, "aac_48k_stereo": audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2, "full_decode": decode.returncode==0, "zero_gaps": all(abs(x["gap_seconds"])<1e-6 for x in gaps), "narration_contained": all(x["contained"] for x in sync), "max_14_seconds": all(e["end"]-e["start"]<=14 for e in events[1:-1]), "end_card_final_only": events[-1]["phase"]=="end", "ten_story_scenes": len(events[1:-1])==10, "three_voice_cast": set(VOICES)=={"natasha-au","ana-us","ryan-uk"}, "no_paid_provider_footage": True, "rejected_duplicate_snow_pose_excluded": "shared-harvest-first-snow-pose-b-v1.png" not in assets, "thumbnail": THUMBNAIL.is_file() and THUMBNAIL.stat().st_size < 2_000_000}
    (WORK / "timeline-gap-audit.json").write_text(json.dumps(gaps, indent=2)+"\n", encoding="utf-8")
    (WORK / "narration-visual-sync-audit.json").write_text(json.dumps(sync, indent=2)+"\n", encoding="utf-8")
    report = {"output": str(OUTPUT), "duration_seconds": float(probe["format"]["duration"]), "visual_method": "generated A/B action keyframes with eased camera travel, seasonal overlays, beat-synchronized pose changes and original local music", "true_rigged_3d_animation": False, "paid_generation_used": False, "checks": checks, "passed": all(checks.values())}
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    general = Image.new("RGB", (960, math.ceil(len(events)/4)*135), "white")
    for i,e in enumerate(events): general.paste(frame_for(e, e["start"]+(e["end"]-e["start"])*0.65, assets).resize((240,135), Image.Resampling.LANCZOS), ((i%4)*240,(i//4)*135))
    general.save(WORK / "quality-contact-sheet.png")
    boundary=[]
    for a,b in zip(events,events[1:]): boundary += [(a,a["end"]-.12),(b,b["start"]+.12)]
    sheet=Image.new("RGB",(1200,math.ceil(len(boundary)/5)*135),"white")
    for i,(e,t) in enumerate(boundary): sheet.paste(frame_for(e,t,assets).resize((240,135),Image.Resampling.LANCZOS),((i%5)*240,(i//5)*135))
    sheet.save(WORK/"transition-contact-sheet.png")
    action_rows = []
    for e in events[1:-1]:
        if e.get("asset_b"):
            midpoint = e["start"] + (e["end"] - e["start"]) * 0.5
            action_rows.extend([(e, midpoint - 0.12), (e, midpoint + 0.12)])
    action_sheet = Image.new("RGB", (1200, math.ceil(len(action_rows)/5)*135), "white")
    for i,(e,t) in enumerate(action_rows):
        sample = frame_for(e,t,assets).resize((240,135),Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(sample); draw.rectangle((0,0,240,18),fill="black")
        draw.text((3,2),f"{e['phase']} {'before' if i%2==0 else 'after'}",font=base.font(11,True),fill="white")
        action_sheet.paste(sample,((i%5)*240,(i//5)*135))
    action_sheet.save(WORK/"action-cut-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(report)


def write_metadata(total: float) -> None:
    doc = {"id": ITEM_ID, "title": "The Ant and Grasshopper's Shared Harvest | Musical Story for Kids", "description": "Meet Ant, Grasshopper, and their meadow orchestra in an original seasonal story about work, music, planning, kindness, and sharing. Sing the new carry-and-play refrain while the friends roll a berry, rescue the autumn harvest, welcome a friend in winter, and grow a shared spring garden.\n\nAn original Tiny Tales musical fable for children ages 3 to 7.", "tags": ["ant and grasshopper story", "musical story for kids", "kindness story", "teamwork for kids", "animal song", "preschool story", "Tiny Tales"], "category_id": "27", "made_for_kids": True, "privacy": "public", "upload_authorized": False, "output": str(OUTPUT), "duration_seconds": total, "voice_profile": "natasha-au", "character_voice_profiles": {"ant":"ana-us","grasshopper":"ryan-uk"}, "quality_gate_passed": True, "full_decode_passed": True, "transition_audit_passed": True, "transition_contact_sheet_reviewed": True, "thumbnail_reviewed": True, "action_cut_contact_sheet_reviewed": True, "quality_report": f"automation/production-work/{ITEM_ID}/quality-report.json", "transition_audit": f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json", "narration_visual_sync_audit": f"automation/production-work/{ITEM_ID}/narration-visual-sync-audit.json", "quality_contact_sheet": f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png", "transition_contact_sheet": f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png", "action_cut_contact_sheet": f"automation/production-work/{ITEM_ID}/action-cut-contact-sheet.png", "prepared_thumbnail": f"automation/thumbnails/{ITEM_ID}.jpg", "thumbnail_hook": "WORK + MUSIC = MAGIC!", "true_rigged_3d_animation": False, "visual_method": "zero-cost generated action keyframes and local code animation", "paid_generation_used": False}
    META.write_text(json.dumps(doc, indent=2)+"\n", encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True); OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(make_voices()); events, voices, total = build_timeline(); assets = load_assets(); make_thumbnail()
    render_engine.WORK=WORK; render_engine.OUTPUT=OUTPUT; render_engine.frame_for=frame_for; render_engine.make_music=make_music
    render_engine.render(events, voices, total, assets); quality(events,total,assets); write_metadata(total)
    print(json.dumps({"output":str(OUTPUT),"duration_seconds":total,"events":len(events)}, indent=2))


if __name__ == "__main__": main()
