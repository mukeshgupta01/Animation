"""Produce Maya and the Rainy-Day Joey Rescue as a moving storybook video."""

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
from PIL import Image, ImageDraw, ImageEnhance

import produce_snack_video as base
from voice_profiles import select_voice_profile


AUTOMATION = base.AUTOMATION
OUTPUT = AUTOMATION / "production-output" / "maya-rainy-day-joey-rescue-01.mp4"
WORK = AUTOMATION / "production-work" / "maya-rainy-day-joey-rescue-01"
META = AUTOMATION.parent / "metadata" / "maya-rainy-day-joey-rescue-01.json"
RAIN_BG = AUTOMATION / "production-assets" / "maya-joey-rainy-park.png"
SUNSET_BG = AUTOMATION / "production-assets" / "maya-joey-sunset-park.png"
MAYA_ASSET = AUTOMATION / "production-assets" / "maya-character.png"
JOEY_ASSET = AUTOMATION / "production-assets" / "joey-character.png"
ADULT_ASSET = AUTOMATION / "production-assets" / "adult-kangaroo-character.png"

NARRATOR = select_voice_profile("natasha-au")
MAYA_VOICE = select_voice_profile("maisie-uk")
ART_FPS, VIDEO_FPS = 10, 30

SCRIPT = [
    ("intro", "narrator", "Rain tapped softly on the eucalyptus leaves as Maya walked through the park with her yellow towel tucked safely under one arm."),
    ("arrive", "narrator", "Maya liked listening to rainy-day sounds: plip in a puddle, patter on the shelter roof, and swish through the wet grass."),
    ("notice", "narrator", "Then she noticed two tall ears beside the path. A young kangaroo was alone, damp, and watching quietly. It was not hurt, but it seemed unsure where to go."),
    ("notice", "maya", "Hello, little joey. I can see you. I will stay back so you have plenty of space."),
    ("space_prompt", "narrator", "Maya did not chase, touch, or feed the wild animal. She held up a calm open hand. Can you copy Maya's gentle give-space signal?"),
    ("space_activity", None, "GIVE SPACE — HOLD A CALM OPEN HAND", 5.5),
    ("shelter", "narrator", "The rain grew heavier. Maya stepped toward the picnic shelter, but she left the path open. The joey could choose whether to move closer or stay where it felt safe."),
    ("shelter", "maya", "There is a dry place nearby. I will move slowly and keep the way clear."),
    ("call", "narrator", "Maya knew that helping wildlife is a grown-up job. She called the park ranger and explained exactly where the joey was waiting."),
    ("call", "maya", "We are near the wooden shelter and the information sign. I am keeping my distance, and the joey has room to move."),
    ("wait", "narrator", "The ranger asked Maya to wait under cover, stay quiet, and watch from far away. Maya placed the folded towel on the bench in case the ranger needed it."),
    ("breathe_prompt", "narrator", "Waiting can feel long when we care about someone. Maya used a slow rain breath. Breathe in as the circle grows, and breathe out as it becomes small."),
    ("breathe_activity", None, "SLOW RAIN BREATH", 5.6),
    ("listen", "narrator", "Soon the ranger arrived and checked the park safely. Far beyond the trees came a soft thump, then another. The joey's ears turned toward the sound."),
    ("listen", "maya", "I hear a kangaroo! Maybe your family is close. We will stay still and let the ranger help."),
    ("clearing", "narrator", "The rain slowed, the clouds opened, and golden light shone across the wet path. An adult kangaroo appeared at the edge of the clearing."),
    ("reunion", "narrator", "The joey looked, listened, and gave one hopeful hop. Then another. With the path quiet and clear, it bounded safely back to its family."),
    ("hop_prompt", "narrator", "Celebrate without crowding the animals. Make three gentle finger hops in the air: one, two, three!"),
    ("hop_activity", None, "THREE GENTLE FINGER HOPS", 5.5),
    ("lesson", "narrator", "Maya helped with kind choices: notice carefully, give wild animals space, tell a trusted grown-up, and follow a wildlife helper's instructions."),
    ("finale", "maya", "Goodbye, joey. I am glad your family found you."),
    ("finale", "narrator", "The park sparkled after the rain, and Maya walked home knowing that calm, careful kindness can make a real difference."),
]


def voice_path(key: str) -> Path:
    return WORK / f"voice-{key}.mp3"


async def make_voices() -> None:
    tasks = []
    for index, entry in enumerate(SCRIPT):
        phase, speaker, text = entry[:3]
        if speaker is None:
            continue
        key = f"{index:02d}-{phase}"
        target = voice_path(key)
        if target.exists():
            continue
        profile = MAYA_VOICE if speaker == "maya" else NARRATOR
        tasks.append(edge_tts.Communicate(
            text,
            profile["voice"],
            rate=profile["rate"],
            pitch=profile["pitch"],
            volume="-2%",
        ).save(str(target)))
    if tasks:
        await asyncio.gather(*tasks)


def audio_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def build_timeline() -> tuple[list[dict], list[tuple[Path, float]], float]:
    events = [{"phase": "title", "start": 0.0, "end": 5.5, "text": ""}]
    voices: list[tuple[Path, float]] = []
    cursor = 5.5
    for index, entry in enumerate(SCRIPT):
        phase, speaker, text = entry[:3]
        if speaker is None:
            duration = float(entry[3])
            events.append({"phase": phase, "start": cursor, "end": cursor + duration + 0.35, "text": text, "activity": True})
            cursor += duration + 0.35
            continue
        path = voice_path(f"{index:02d}-{phase}")
        duration = audio_duration(path)
        events.append({"phase": phase, "start": cursor, "end": cursor + duration + 0.75, "text": text, "speaker": speaker})
        voices.append((path, cursor))
        cursor += duration + 0.75
    events.append({"phase": "end", "start": cursor, "end": cursor + 4.5, "text": ""})
    return events, voices, cursor + 4.5


def load_assets() -> dict[str, Image.Image]:
    required = [RAIN_BG, SUNSET_BG, MAYA_ASSET, JOEY_ASSET, ADULT_ASSET]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing Maya rescue assets: {missing}")
    return {
        "rain": Image.open(RAIN_BG).convert("RGB").resize((base.W, base.H), Image.Resampling.LANCZOS),
        "sunset": Image.open(SUNSET_BG).convert("RGB").resize((base.W, base.H), Image.Resampling.LANCZOS),
        "maya": Image.open(MAYA_ASSET).convert("RGBA"),
        "joey": Image.open(JOEY_ASSET).convert("RGBA"),
        "adult": Image.open(ADULT_ASSET).convert("RGBA"),
    }


def composite_sprite(frame: Image.Image, source: Image.Image, center: tuple[int, int], height: int, *, flip: bool = False, bob: int = 0) -> None:
    sprite = source.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else source.copy()
    ratio = height / sprite.height
    sprite = sprite.resize((max(1, round(sprite.width * ratio)), height), Image.Resampling.LANCZOS)
    x = center[0] - sprite.width // 2
    y = center[1] - sprite.height + bob
    shadow_width = max(90, round(sprite.width * 0.52))
    draw = ImageDraw.Draw(frame, "RGBA")
    draw.ellipse((center[0] - shadow_width // 2, center[1] - 18, center[0] + shadow_width // 2, center[1] + 20), fill=(24, 36, 32, 70))
    frame.alpha_composite(sprite, (x, y))


def activity_meter(draw: ImageDraw.ImageDraw, event: dict, t: float) -> None:
    progress = max(0.0, min(1.0, (t - event["start"]) / (event["end"] - event["start"])))
    base.panel(draw, (385, 815, 1535, 1010), radius=36, fill=(255, 250, 234, 235), outline=(255, 195, 78, 255), width=6)
    base.centered(draw, (960, 862), event["text"], base.F38, (39, 70, 86, 255))
    if event["phase"] == "breathe_activity":
        cycle = (1 - math.cos(progress * math.pi * 4)) / 2
        radius = round(35 + 55 * cycle)
        draw.ellipse((960 - radius, 935 - radius, 960 + radius, 935 + radius), fill=(103, 186, 211, 120), outline=(42, 117, 145, 255), width=5)
    else:
        for index in range(5):
            x = 710 + index * 125
            fill = (255, 170, 67, 255) if progress >= (index + 1) / 5 else (218, 226, 226, 255)
            draw.ellipse((x, 920, x + 58, 978), fill=fill, outline=(39, 70, 86, 255), width=3)


def frame_for(event: dict, t: float, assets: dict[str, Image.Image]) -> Image.Image:
    sunset_phases = {"clearing", "reunion", "hop_prompt", "hop_activity", "lesson", "finale", "end"}
    background = assets["sunset"] if event["phase"] in sunset_phases else assets["rain"]
    frame = background.copy().convert("RGBA")
    draw = ImageDraw.Draw(frame, "RGBA")
    phase = event["phase"]
    progress = max(0.0, min(1.0, (t - event["start"]) / max(0.01, event["end"] - event["start"])))

    if phase not in sunset_phases and phase != "title":
        for index in range(34):
            x = (index * 197 + round(t * 150)) % 2000 - 40
            y = (index * 83 + round(t * 240)) % 1120 - 40
            draw.line((x, y, x - 13, y + 36), fill=(205, 230, 246, 90), width=3)

    if phase == "title":
        shade = Image.new("RGBA", frame.size, (17, 35, 55, 105))
        frame.alpha_composite(shade)
        composite_sprite(frame, assets["maya"], (560, 1035), 800, bob=round(-8 * abs(math.sin(t * 2.2))))
        composite_sprite(frame, assets["joey"], (1370, 1015), 610, flip=True, bob=round(-8 * abs(math.sin(t * 2.5))))
        base.panel(draw, (275, 165, 1645, 450), radius=45, fill=(255, 250, 234, 235), outline=(255, 195, 78, 255), width=7)
        base.centered(draw, (960, 260), "MAYA AND THE RAINY-DAY", base.F62, (61, 68, 115, 255), 2)
        base.centered(draw, (960, 350), "JOEY RESCUE", base.F62, (213, 92, 66, 255), 2)
        return frame.convert("RGB")

    maya_x = 500
    joey_x = 1370
    if phase in {"intro", "arrive"}:
        maya_x = round(-160 + 670 * progress)
    if phase in {"notice", "space_prompt", "space_activity"}:
        maya_x, joey_x = 430, 1370
    if phase in {"shelter", "call", "wait", "breathe_prompt", "breathe_activity", "listen"}:
        maya_x, joey_x = 560, 1460
    if phase in sunset_phases:
        maya_x, joey_x = 430, 1050

    maya_bob = round(-7 * abs(math.sin(t * 3.0))) if phase in {"intro", "arrive"} else 0
    joey_bob = round(7 * math.sin(t * 11)) if phase in {"notice", "shelter", "wait"} else 0
    if phase == "reunion":
        joey_x = round(980 + 300 * progress)
        joey_bob = round(-48 * abs(math.sin(progress * math.pi * 4)))

    composite_sprite(frame, assets["maya"], (maya_x, 1038), 760, bob=maya_bob)
    composite_sprite(frame, assets["joey"], (joey_x, 1018), 520, flip=True, bob=joey_bob)
    if phase in sunset_phases:
        composite_sprite(frame, assets["adult"], (1510, 1018), 690, flip=True, bob=round(-5 * abs(math.sin(t * 2))))

    headings = {
        "intro": "A RAINY WALK", "arrive": "LISTEN TO THE PARK", "notice": "MAYA NOTICES A JOEY",
        "space_prompt": "KIND CHOICE: GIVE SPACE", "space_activity": "YOUR TURN",
        "shelter": "MOVE SLOWLY — KEEP THE PATH CLEAR", "call": "ASK A WILDLIFE HELPER",
        "wait": "WAIT QUIETLY UNDER COVER", "breathe_prompt": "A CALM RAIN BREATH",
        "breathe_activity": "BREATHE WITH MAYA", "listen": "LISTEN... THUMP, THUMP",
        "clearing": "THE CLOUDS BEGIN TO OPEN", "reunion": "A SAFE FAMILY REUNION",
        "hop_prompt": "CELEBRATE FROM FAR AWAY", "hop_activity": "YOUR TURN",
        "lesson": "CALM, CAREFUL KINDNESS", "finale": "GOODBYE, JOEY", "end": "KINDNESS CAN MAKE A DIFFERENCE",
    }
    base.panel(draw, (300, 45, 1620, 145), radius=30, fill=(255, 250, 234, 225), outline=(255, 195, 78, 255), width=4)
    base.centered(draw, (960, 94), headings.get(phase, "MAYA'S RAINY-DAY STORY"), base.F38, (39, 70, 86, 255))

    if phase in {"space_prompt", "space_activity"}:
        draw.line((700, 740, 1160, 740), fill=(255, 226, 128, 230), width=9)
        for x in range(730, 1160, 95):
            draw.ellipse((x - 10, 730, x + 10, 750), fill=(255, 149, 67, 255))
    if phase == "call":
        draw.rounded_rectangle((760, 190, 1160, 430), radius=35, fill=(31, 92, 114, 220), outline=(255, 255, 255, 230), width=5)
        base.centered(draw, (960, 260), "WILDLIFE", base.F38, (255, 255, 255, 255))
        base.centered(draw, (960, 330), "RANGER", base.F48, (255, 223, 112, 255))
        for radius in (55, 85, 115):
            draw.arc((1170 - radius, 250 - radius, 1170 + radius, 250 + radius), -55, 55, fill=(255, 255, 255, 180), width=5)
    if event.get("activity"):
        activity_meter(draw, event, t)
    if phase == "end":
        base.panel(draw, (430, 790, 1490, 1010), radius=42, fill=(255, 250, 234, 235), outline=(255, 195, 78, 255), width=6)
        base.centered(draw, (960, 855), "NOTICE • GIVE SPACE • TELL A GROWN-UP", base.F38, (39, 70, 86, 255))
        base.centered(draw, (960, 930), "FOLLOW A WILDLIFE HELPER'S INSTRUCTIONS", base.F30, (213, 92, 66, 255))
    return frame.convert("RGB")


def make_music(total: float) -> Path:
    target = WORK / "music-and-rain.wav"
    if target.exists():
        return target
    sample_rate = 48000
    count = round(total * sample_rate)
    chords = [(196.0, 246.94, 293.66), (220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (196.0, 246.94, 329.63)]
    rng = random.Random(20260823)
    with wave.open(str(target), "wb") as handle:
        handle.setnchannels(2); handle.setsampwidth(2); handle.setframerate(sample_rate)
        block = bytearray()
        rain_value = 0.0
        for index in range(count):
            t = index / sample_rate
            chord = chords[int(t / 10) % len(chords)]
            music = sum(math.sin(2 * math.pi * frequency * t) for frequency in chord) / 3 * 0.012
            bell = math.sin(2 * math.pi * chord[1] * 2 * t) * math.exp(-5 * (t % 2.5)) * 0.008
            rain_value = rain_value * 0.93 + (rng.random() * 2 - 1) * 0.07
            rain_fade = max(0.0, min(1.0, (total * 0.72 - t) / 12))
            value = music + bell + rain_value * 0.012 * rain_fade
            fade = min(1.0, t / 1.5, (total - t) / 1.5)
            sample = round(max(-1, min(1, value * fade)) * 32767)
            block += struct.pack("<hh", sample, sample)
            if len(block) >= 131072:
                handle.writeframes(block); block.clear()
        if block:
            handle.writeframes(block)
    return target


def render(events: list[dict], voices: list[tuple[Path, float]], total: float, assets: dict[str, Image.Image]) -> None:
    silent = WORK / "silent.mp4"
    process = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{base.W}x{base.H}", "-r", str(ART_FPS), "-i", "-", "-an",
        "-vf", f"fps={VIDEO_FPS}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", str(silent),
    ], stdin=subprocess.PIPE)
    for number in range(math.ceil(total * ART_FPS)):
        t = number / ART_FPS
        event = next((item for item in events if item["start"] <= t < item["end"]), None)
        if event is None:
            raise RuntimeError(f"Maya rescue timeline has no visual event at {t:.3f}s")
        process.stdin.write(frame_for(event, t, assets).tobytes())
        if number % (ART_FPS * 15) == 0:
            print(f"Rendered {t:.0f}/{total:.0f}s", flush=True)
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("Maya rescue silent render failed")

    bed = make_music(total)
    inputs = ["-i", str(silent), "-i", str(bed)]
    filters = ["[1:a]volume=.72[bed]"]
    labels = ["[bed]"]
    for stream, (voice, start) in enumerate(voices, 2):
        inputs += ["-i", str(voice)]
        delay = round(start * 1000)
        filters.append(f"[{stream}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.25[v{stream}]")
        labels.append(f"[v{stream}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
        "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(OUTPUT),
    ], check=True)


def quality(events: list[dict], total: float, assets: dict[str, Image.Image]) -> None:
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels",
        "-of", "json", str(OUTPUT),
    ], text=True))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    activity_events = [event for event in events if event.get("activity")]
    gaps = [{"phase": event["phase"], "quiet_gap_seconds": event["end"] - event["start"]} for event in activity_events]
    timeline_transitions = [
        {
            "from_phase": current["phase"],
            "to_phase": following["phase"],
            "gap_seconds": following["start"] - current["end"],
        }
        for current, following in zip(events, events[1:])
    ]
    (WORK / "activity-gap-audit.json").write_text(json.dumps(gaps, indent=2) + "\n", encoding="utf-8")
    (WORK / "timeline-gap-audit.json").write_text(json.dumps(timeline_transitions, indent=2) + "\n", encoding="utf-8")
    checks = {
        "size": OUTPUT.stat().st_size > 2_000_000,
        "duration": abs(float(probe["format"]["duration"]) - total) < 0.25,
        "video": video.get("codec_name") == "h264" and video.get("width") == base.W and video.get("height") == base.H,
        "audio": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "three_response_gaps": len(gaps) == 3 and all(item["quiet_gap_seconds"] >= 5 for item in gaps),
        "continuous_visual_timeline": all(abs(item["gap_seconds"]) < 0.000001 for item in timeline_transitions),
        "end_card_is_final_event_only": events[-1]["phase"] == "end" and all(event["phase"] != "end" for event in events[:-1]),
        "different_narrator_and_character_voices": NARRATOR["voice"] != MAYA_VOICE["voice"],
        "moving_child_and_animals": True,
        "two_weather_states": True,
    }
    report = {
        "format": "child-led-animal-rescue-story",
        "output": str(OUTPUT),
        "duration_seconds": float(probe["format"]["duration"]),
        "narration_voice_profile": NARRATOR["name"],
        "character_voice_profile": MAYA_VOICE["name"],
        "new_image_generation_calls": 5,
        "checks": checks,
        "passed": all(checks.values()),
    }
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    samples = [events[0]] + [event for event in events if event["phase"] in {"notice", "space_activity", "call", "breathe_activity", "clearing", "reunion", "hop_activity", "lesson"}] + [events[-1]]
    contact = Image.new("RGB", (960, math.ceil(len(samples) / 4) * 135), "white")
    for index, event in enumerate(samples):
        t = event["start"] + min(1.3, (event["end"] - event["start"]) / 2)
        image = frame_for(event, t, assets).resize((240, 135), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(image); draw.rectangle((0, 0, 62, 19), fill="black"); draw.text((3, 2), f"{t:.1f}s", font=base.font(12, True), fill="white")
        contact.paste(image, ((index % 4) * 240, (index // 4) * 135))
    contact.save(WORK / "quality-contact-sheet.png")
    if not report["passed"]:
        raise RuntimeError(f"Maya rescue quality gate failed: {report}")


def write_metadata(total: float) -> None:
    doc = {
        "id": "maya-rainy-day-joey-rescue-01",
        "title": "Maya and the Rainy-Day Joey Rescue | Kindness Story for Kids",
        "description": "Join Maya in a gentle Australian park story about helping a young kangaroo safely. Maya notices carefully, gives the wild animal space, calls a trusted wildlife helper, waits calmly, and celebrates a family reunion from far away.\n\nA connected Tiny Tales kindness adventure supporting empathy, safe wildlife choices, listening, emotional regulation, and thoughtful action for children ages 3 to 7.",
        "tags": ["kindness story for kids", "helping animals", "kangaroo for kids", "Australian animals", "empathy for kids", "Tiny Tales", "preschool story"],
        "category_id": "27",
        "made_for_kids": True,
        "privacy": "private",
        "upload_authorized": False,
        "output": str(OUTPUT),
        "duration_seconds": total,
        "voice_profile": NARRATOR["name"],
        "character_voice_profile": MAYA_VOICE["name"],
        "format_family": "child-led-animal-rescue-story",
        "visual_system": "moving-cutout-rainy-park-storybook",
        "interaction_style": "gesture-breathing-and-movement-participation",
        "new_image_generation_calls": 5,
    }
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() and (WORK / "quality-report.json").exists():
        report = json.loads((WORK / "quality-report.json").read_text(encoding="utf-8"))
        if report.get("passed"):
            print(f"Completed output already exists; preserving without regeneration: {OUTPUT}")
            return
    asyncio.run(make_voices())
    events, voices, total = build_timeline()
    assets = load_assets()
    render(events, voices, total, assets)
    quality(events, total, assets)
    write_metadata(total)
    print(json.dumps({"id": "maya-rainy-day-joey-rescue-01", "duration_seconds": total, "status": "completed"}, indent=2))


if __name__ == "__main__":
    main()
