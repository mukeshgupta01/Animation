"""Produce five authorized 20-second Father's Day Shorts for Parenting Rewind."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

# Reuse the project's pinned speech package without changing either environment.
sys.path.insert(0, r"C:\DocSphere\Animation\ParentingRewind\.venv\Lib\site-packages")
import edge_tts  # noqa: E402


PROJECT = Path(__file__).resolve().parents[1]
ASSETS = PROJECT / "production-assets"
OUTPUT = PROJECT / "output" / "fathers-day-20-second-shorts"
WORK = PROJECT / "production-work" / "fathers-day-20-second-shorts"
META = PROJECT / "metadata" / "fathers-day-20-second-shorts"
FPS = 30
DURATION = 20.0
VOICE = "en-US-AvaMultilingualNeural"
FONT = Path(r"C:\Windows\Fonts\segoeui.ttf")
BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")


STORIES = [
    {
        "slug": "the-missed-call",
        "title": "The Missed Call",
        "asset": "01-missed-call-triptych.png",
        "accent": (231, 170, 92),
        "narration": "Dad never asked for expensive gifts. He was only hoping to hear your voice. This Father's Day, call Dad. Like and subscribe for more heartfelt Parenting Rewind stories.",
        "screen": ["HE WAS ONLY HOPING", "TO HEAR YOUR VOICE", "THIS FATHER'S DAY, CALL DAD"],
        "youtube_title": "The Missed Call That Meant Everything | Father's Day Short",
        "description": "Dad may not ask for presents. Sometimes he is simply hoping to hear your voice. A short Father's Day reminder to make the call while you can.\n\n#FathersDay #Dad #Fatherhood #CallDad #ParentingRewind #Shorts",
        "tags": ["Father's Day", "dad", "fatherhood", "call dad", "family", "parent appreciation", "emotional short", "Parenting Rewind"],
        "music_root": 50,
    },
    {
        "slug": "the-shoes-by-the-door",
        "title": "The Shoes by the Door",
        "asset": "02-shoes-by-door-triptych.png",
        "accent": (157, 190, 145),
        "narration": "He helped me take my first steps. Now I will walk beside him. Happy Father's Day, Dad. Like and subscribe for more heartfelt Parenting Rewind stories.",
        "screen": ["HE HELPED ME TAKE", "MY FIRST STEPS", "NOW I'LL WALK BESIDE HIM"],
        "youtube_title": "He Tied My Shoes. Now I Walk Beside Him | Father's Day Short",
        "description": "He helped with the little steps first. Years later, love can look like slowing down and walking beside him. Happy Father's Day to the dads who were there.\n\n#FathersDay #Dad #Fatherhood #FamilyLove #ParentingRewind #Shorts",
        "tags": ["Father's Day", "dad", "father daughter", "growing older", "family love", "fatherhood", "emotional short", "Parenting Rewind"],
        "music_root": 53,
    },
    {
        "slug": "his-old-wallet",
        "title": "His Old Wallet",
        "asset": "03-old-wallet-triptych.png",
        "accent": (196, 145, 96),
        "narration": "I grew up and became busy. But Dad carried my picture every day. I was always his greatest treasure. Like and subscribe for more heartfelt Parenting Rewind stories.",
        "screen": ["I GREW UP AND GOT BUSY", "DAD CARRIED ME EVERY DAY", "I WAS ALWAYS HIS TREASURE"],
        "youtube_title": "What Dad Kept in His Wallet All These Years | Father's Day Short",
        "description": "Tucked inside an old wallet was a small reminder: even when life became busy, his child was never far from his heart. A Father's Day story about quiet love.\n\n#FathersDay #Dad #Fatherhood #FamilyMemories #ParentingRewind #Shorts",
        "tags": ["Father's Day", "dad", "old wallet", "family memories", "quiet love", "fatherhood", "emotional short", "Parenting Rewind"],
        "music_root": 48,
    },
    {
        "slug": "one-more-story",
        "title": "One More Story",
        "asset": "04-one-more-story-triptych.png",
        "accent": (126, 173, 205),
        "narration": "When I was little, Dad always gave me one more story. Now it is my turn to stay a little longer. Like and subscribe for more heartfelt Parenting Rewind stories.",
        "screen": ["DAD GAVE ME", "ONE MORE STORY", "NOW I'LL STAY A LITTLE LONGER"],
        "youtube_title": "Dad Always Read One More Story | Father's Day Short",
        "description": "When we were little, Dad gave us one more story and a little more time. Now the most meaningful gift may be giving some of that time back.\n\n#FathersDay #Dad #BedtimeStories #FamilyTime #ParentingRewind #Shorts",
        "tags": ["Father's Day", "dad", "bedtime story", "family time", "aging parents", "father daughter", "emotional short", "Parenting Rewind"],
        "music_root": 55,
    },
    {
        "slug": "the-empty-chair",
        "title": "The Empty Chair",
        "asset": "05-empty-chair-triptych.png",
        "accent": (221, 129, 105),
        "narration": "Dad said he did not need anything. But when we came home, this was everything. Happy Father's Day, Dad. Like and subscribe for more heartfelt Parenting Rewind stories.",
        "screen": ["DAD SAID HE NEEDED NOTHING", "THEN WE CAME HOME", "AND IT MEANT EVERYTHING"],
        "youtube_title": "The Empty Chair Wasn't Empty for Long | Father's Day Short",
        "description": "Dad said he did not need anything. Then the door opened, the chair was filled, and the whole room changed. Sometimes presence is the greatest Father's Day gift.\n\n#FathersDay #Dad #FamilyReunion #Fatherhood #ParentingRewind #Shorts",
        "tags": ["Father's Day", "dad", "family reunion", "coming home", "fatherhood", "family time", "emotional short", "Parenting Rewind"],
        "music_root": 52,
    },
]


def run(args: list[str], cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], text=True).strip())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def split_triptych(source_path: Path, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    source = Image.open(source_path).convert("RGB")
    paths = []
    for index in range(3):
        left = round(index * source.width / 3) + 10
        right = round((index + 1) * source.width / 3) - 10
        panel = source.crop((left, 8, right, source.height - 8))
        target = destination / f"panel-{index + 1}.jpg"
        panel.save(target, quality=95, optimize=True)
        paths.append(target)
    return paths


def note_frequency(midi: float) -> float:
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0)


def synth_music(target: Path, root: int, variation: int) -> None:
    rate = 48000
    length = int(DURATION * rate)
    t = np.arange(length, dtype=np.float64) / rate
    music = np.zeros((length, 2), dtype=np.float64)
    progressions = [(0, 9, 5, 7), (0, 5, 9, 7), (0, 7, 9, 5), (9, 5, 0, 7), (0, 9, 7, 5)]
    progression = progressions[variation % len(progressions)]
    chord_intervals = (0, 4, 7, 11)
    segment = DURATION / 4
    for chord_index, degree in enumerate(progression):
        start = chord_index * segment
        local = t - start
        active = (local >= 0) & (local < segment + 0.7)
        env = np.where(active, np.minimum(1.0, np.maximum(0.0, local) / 0.12) * np.exp(-np.maximum(0.0, local) / 4.8), 0.0)
        for tone_index, interval in enumerate(chord_intervals):
            freq = note_frequency(root + degree + interval)
            rhodes = np.sin(2 * np.pi * freq * t) + 0.22 * np.sin(2 * np.pi * freq * 2.01 * t + 0.3)
            pan = 0.35 + 0.18 * tone_index
            music[:, 0] += rhodes * env * (1.0 - pan) * 0.085
            music[:, 1] += rhodes * env * pan * 0.085
        bass_freq = note_frequency(root + degree - 12)
        bass = np.sin(2 * np.pi * bass_freq * t) * env * 0.055
        music[:, 0] += bass
        music[:, 1] += bass
    # A sparse original pentatonic response, deliberately unlike any known song.
    melody = (0, 2, 4, 7, 9, 7, 4, 2, 0, 4, 7, 9)
    for index, step in enumerate(melody):
        start = 1.0 + index * 1.5
        local = t - start
        active = (local >= 0) & (local < 1.35)
        env = np.where(active, (1.0 - np.exp(-np.maximum(local, 0.0) / 0.035)) * np.exp(-np.maximum(local, 0.0) / 0.75), 0.0)
        freq = note_frequency(root + 12 + step)
        tone = (np.sin(2 * np.pi * freq * t) + 0.15 * np.sin(2 * np.pi * 2 * freq * t)) * env * 0.045
        pan = 0.42 if index % 2 == 0 else 0.58
        music[:, 0] += tone * (1 - pan)
        music[:, 1] += tone * pan
    fade = np.minimum(1.0, t / 0.8) * np.minimum(1.0, (DURATION - t) / 1.2)
    music *= np.maximum(0.0, fade[:, None])
    music /= max(1.0, np.max(np.abs(music)) / 0.72)
    pcm = np.int16(np.clip(music, -1, 1) * 32767)
    with wave.open(str(target), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())


def stamp(value: float) -> str:
    centiseconds = max(0, round(value * 100))
    hours, centiseconds = divmod(centiseconds, 360000)
    minutes, centiseconds = divmod(centiseconds, 6000)
    seconds, centiseconds = divmod(centiseconds, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def write_overlay(story: dict, target: Path) -> None:
    accent = story["accent"]
    # ASS uses BGR order.
    color = f"&H00{accent[2]:02X}{accent[1]:02X}{accent[0]:02X}"
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Brand,Segoe UI,25,&H00FFFFFF,&H00FFFFFF,&H60000000,&HA0000000,-1,0,0,0,100,100,2,0,3,1,0,8,55,55,64,1
Style: Title,Segoe UI Semibold,47,{color},{color},&H78000000,&HC0000000,-1,0,0,0,100,100,0,0,3,2,0,8,65,65,145,1
Style: Message,Segoe UI Semibold,55,&H00FFFFFF,&H00FFFFFF,&H90000000,&HCA101010,-1,0,0,0,100,100,0,0,3,2,0,2,65,65,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header.rstrip()]
    lines.append(f"Dialogue: 0,{stamp(0)},{stamp(DURATION)},Brand,,0,0,0,,PARENTING REWIND")
    lines.append(f"Dialogue: 0,{stamp(0)},{stamp(3.0)},Title,,0,0,0,,{story['title'].upper()}")
    times = ((0.4, 6.55), (6.55, 12.95), (12.95, 19.7))
    for text, (start, end) in zip(story["screen"], times):
        lines.append(f"Dialogue: 0,{stamp(start)},{stamp(end)},Message,,0,0,0,,{text}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


async def create_narration(text: str, target: Path) -> None:
    await edge_tts.Communicate(text, VOICE, rate="+3%", pitch="-1Hz", volume="-1%").save(str(target))
    voice_duration = duration(target)
    if voice_duration > 19.0:
        ratio = voice_duration / 18.7
        adjusted = target.with_name("narration-adjusted.mp3")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(target), "-filter:a", f"atempo={ratio:.6f}", str(adjusted)])
        adjusted.replace(target)


def render(story: dict, panels: list[Path], narration: Path, music: Path, overlay: Path, target: Path) -> None:
    clip = 7.1
    inputs: list[str] = []
    for panel in panels:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", str(clip), "-i", str(panel)]
    inputs += ["-i", str(narration), "-i", str(music)]
    filters = []
    for index in range(3):
        zoom = "min(zoom+0.00011,1.045)" if index != 1 else "min(zoom+0.00008,1.035)"
        x = "(iw-iw/zoom)/2" if index != 0 else "(iw-iw/zoom)*0.46"
        filters.append(f"[{index}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='{zoom}':x='{x}':y='(ih-ih/zoom)/2':d={math.ceil(clip*FPS)}:s=1080x1920:fps={FPS},eq=saturation=0.98:contrast=1.025,setsar=1[v{index}]")
    filters += [
        "[v0][v1]xfade=transition=fade:duration=0.65:offset=6.45[x1]",
        "[x1][v2]xfade=transition=fade:duration=0.65:offset=12.90[base]",
        "[base]ass=overlay.ass[v]",
        "[3:a]adelay=300|300,aformat=sample_rates=48000:channel_layouts=stereo,volume=1.12,asplit=2[side][voice]",
        "[4:a]atrim=duration=20,aformat=sample_rates=48000:channel_layouts=stereo,volume=0.82[music]",
        "[music][side]sidechaincompress=threshold=.025:ratio=3.8:attack=18:release=360[ducked]",
        "[ducked][voice]amix=inputs=2:normalize=0:dropout_transition=0,alimiter=limit=.92,loudnorm=I=-16:TP=-1.5:LRA=8[a]",
    ]
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", "20", "-movflags", "+faststart", str(target)], cwd=overlay.parent)


def make_thumbnail(story: dict, panels: list[Path], target: Path) -> None:
    base = Image.open(panels[2]).convert("RGB")
    scale = max(1280 / base.width, 720 / base.height)
    base = base.resize((round(base.width * scale), round(base.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (base.width - 1280) // 2)
    top = max(0, round((base.height - 720) * 0.32))
    base = base.crop((left, top, left + 1280, top + 720)).filter(ImageFilter.GaussianBlur(0.3))
    base = ImageEnhance.Contrast(base).enhance(1.08)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, 1280, 720), fill=(8, 10, 14, 58))
    draw.rounded_rectangle((72, 315, 1208, 650), radius=34, fill=(10, 13, 18, 202), outline=(*story["accent"], 230), width=4)
    base = Image.alpha_composite(base.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(base)
    title_font = ImageFont.truetype(str(BOLD), 74)
    sub_font = ImageFont.truetype(str(BOLD), 43)
    title = story["title"].upper()
    message = story["screen"][2]
    for text, font, y, color in ((title, title_font, 365, (255, 255, 255)), (message, sub_font, 490, story["accent"])):
        box = draw.textbbox((0, 0), text, font=font, stroke_width=2)
        x = (1280 - (box[2] - box[0])) // 2
        draw.text((x, y), text, font=font, fill=color, stroke_width=2, stroke_fill=(0, 0, 0))
    base.convert("RGB").save(target, quality=94, optimize=True)


def validate(target: Path, work: Path) -> dict:
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels", "-of", "json", str(target)], text=True))
    video = next(item for item in probe["streams"] if item["codec_type"] == "video")
    audio = next(item for item in probe["streams"] if item["codec_type"] == "audio")
    checks = {
        "duration_20_seconds": abs(float(probe["format"]["duration"]) - 20.0) < 0.15,
        "vertical_h264_1080x1920": video.get("codec_name") == "h264" and video.get("width") == 1080 and video.get("height") == 1920,
        "aac_48khz_stereo": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
        "nontrivial_size": target.stat().st_size > 1_000_000,
    }
    run(["ffmpeg", "-v", "error", "-i", str(target), "-f", "null", "-"])
    report = {"file": str(target), "duration": float(probe["format"]["duration"]), "size": int(probe["format"]["size"]), "checks": checks, "full_decode": "passed", "passed": all(checks.values())}
    (work / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise RuntimeError(report)
    return report


async def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    results = []
    for index, story in enumerate(STORIES):
        story_work = WORK / story["slug"]
        story_work.mkdir(parents=True, exist_ok=True)
        panels = split_triptych(ASSETS / story["asset"], story_work / "panels")
        narration = story_work / "narration.mp3"
        music = story_work / "original-soulful-score.wav"
        overlay = story_work / "overlay.ass"
        video = OUTPUT / f"{index + 1:02d}-{story['slug']}-fathers-day-short.mp4"
        thumbnail = OUTPUT / f"{index + 1:02d}-{story['slug']}-thumbnail.jpg"
        await create_narration(story["narration"], narration)
        synth_music(music, story["music_root"], index)
        write_overlay(story, overlay)
        render(story, panels, narration, music, overlay, video)
        make_thumbnail(story, panels, thumbnail)
        report = validate(video, story_work)
        metadata = {
            "episode_id": f"fathers-day-20s-{story['slug']}",
            "title": story["youtube_title"],
            "status": "upload-authorized",
            "audience_intent": "Adults and parents; not directed to children",
            "narration": {"type": "synthetic", "voice": VOICE, "transcript": story["narration"]},
            "artwork": {"source": f"production-assets/{story['asset']}", "panel_count": 3, "new_image_generation_calls": 1},
            "music": {"type": "original locally synthesized soulful instrumental", "copyright_safe": True, "narration_sidechain_ducking": True, "ambient_noise": False, "sound_effects": False},
            "youtube": {"title": story["youtube_title"], "description": story["description"], "tags": story["tags"], "privacy": "public", "made_for_kids": False, "contains_synthetic_media": True, "thumbnail": str(thumbnail.relative_to(PROJECT))},
            "output": {"file": str(video.relative_to(PROJECT)), "duration_seconds": report["duration"], "sha256": sha256(video)},
            "published": False,
            "upload_authorized": True,
        }
        meta_path = META / f"{story['slug']}.json"
        meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        results.append({"slug": story["slug"], "video": str(video), "thumbnail": str(thumbnail), "metadata": str(meta_path), "quality": report})
        print(json.dumps(results[-1]), flush=True)
    (WORK / "collection-report.json").write_text(json.dumps({"count": len(results), "results": results}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
