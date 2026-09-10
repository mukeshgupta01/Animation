"""Build a narration-only Ollie review master while preserving the archived video stream."""

from __future__ import annotations

from array import array
import asyncio
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import wave

import edge_tts


PROJECT = Path(__file__).resolve().parents[2]
AUTOMATION = PROJECT / "automation"
ITEM_ID = "ollie-otter-floating-picnic-01"
SOURCE_VIDEO = AUTOMATION / "archive" / f"{ITEM_ID}.mp4"
SOURCE_MUSIC = AUTOMATION / "production-work" / ITEM_ID / "original-ollie-balance-rhyme.wav"
SOURCE_EFFECTS = AUTOMATION / "production-work" / ITEM_ID / "original-river-action-effects.wav"
WORK = AUTOMATION / "production-work" / f"{ITEM_ID}-narration-revision"
SEGMENTS = WORK / "narration-segments"
OUTPUT = AUTOMATION / "production-output" / "ollie-narration-review.mp4"
TOTAL = 150.0
SCENE_SECONDS = 16.0
VOICE = "en-AU-NatashaNeural"
VOICE_NAME = "natasha-au"
BASE_RATE = "-7%"
BASE_PITCH = "+2Hz"

SCENES = (
    ("Sun on the river—picnic day!", "Ollie smiles and calls, “This way!”", "Basket, blanket, water too—", "How can three friends safely cruise?"),
    ("Basket, blanket, jug go left.", "Oops! That side has all the heft!", "Left side low, right side high—", "Keep it tied and keep it flat."),
    ("Ollie rolls the blue jug right.", "Willa watches, eyes so bright.", "Left and right now share the load—", "Smooth and level as a road!"),
    ("Willa boards and sits down low.", "Clip the straps before we go.", "One friend moves, the others wait—", "Patient turns will keep things straight."),
    ("Left and right—then find the middle!", "Slow and steady, just a little.", "Sit down low and help it glide—", "Balance, balance—side to side!"),
    ("Fern sees ducks and waves hello.", "One side dips—so soft and slow.", "Point to centre—can you show?", "Back we scoot before we row."),
    ("Fern scoots back to centre, please.", "A level raft, a laughing breeze.", "Paddles dip on either side—", "Together, together—glide, glide, glide!"),
    ("Ropes are tied at Picnic Bay.", "Unload first—that is the way.", "Hand to hand the basket goes,", "Then the blanket softly rolls."),
    ("Left and right—then find the middle!", "Slow and steady, just a little.", "Friends who listen, friends who guide—", "Balance, balance—side by side!"),
)

ACTION_WORDS = (
    ("river", "calls", "blanket", "cruise"),
    ("left", "Oops", "right", "flat"),
    ("rolls", "watches", "load", "level"),
    ("boards", "straps", "moves", "straight"),
    ("middle", "steady", "glide", "balance"),
    ("waves", "dips", "centre", "scoot"),
    ("scoots", "level", "dip", "glide"),
    ("tied", "Unload", "basket", "blanket"),
    ("middle", "steady", "guide", "balance"),
)

VISUAL_ACTIONS = (
    "friends inspect the tied empty raft and three picnic loads",
    "the loads move left and the raft visibly tilts",
    "Ollie rolls the jug right and the raft returns level",
    "Willa boards low and the opposite loads are secured",
    "the seated friends gesture left, right and centre",
    "Fern waves to ducks, the raft dips, and Ollie cues centre",
    "Fern scoots to centre and the friends paddle together",
    "the raft is tied before the basket and blanket move ashore",
    "three cups appear and the friends perform the final chorus",
)


def performance(scene: int, line: int) -> tuple[str, str, str]:
    if scene in {5, 9}:
        return "-5%", "+4Hz", "chorus-bright"
    if (scene, line) in {(1, 1), (1, 2), (2, 2), (3, 4), (7, 4)}:
        return "-6%", "+3Hz", "playful-emphasis"
    if (scene, line) in {(1, 4), (6, 3)}:
        return "-6%", "+3Hz", "curious-question"
    if (scene, line) in {(5, 2), (6, 2), (8, 4), (9, 2)}:
        return "-9%", "+1Hz", "gentle-breath"
    return BASE_RATE, BASE_PITCH, "warm-story"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def media_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


async def make_segments() -> list[dict]:
    SEGMENTS.mkdir(parents=True, exist_ok=True)
    cache: dict[tuple[str, str, str], tuple[Path, Path]] = {}
    rows = []
    for scene_index, lines in enumerate(SCENES, 1):
        for line_index, text in enumerate(lines, 1):
            rate, pitch, emotion = performance(scene_index, line_index)
            key = (text, rate, pitch)
            raw = SEGMENTS / f"scene-{scene_index:02d}-line-{line_index:02d}-{VOICE_NAME}-raw.mp3"
            wav = SEGMENTS / f"scene-{scene_index:02d}-line-{line_index:02d}-{VOICE_NAME}.wav"
            if key in cache:
                shutil.copy2(cache[key][0], raw)
                shutil.copy2(cache[key][1], wav)
            else:
                await edge_tts.Communicate(
                    text, VOICE, rate=rate, pitch=pitch, volume="-1%"
                ).save(str(raw))
                raw_duration = media_duration(raw)
                run([
                    "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                    "-af", (
                        f"highpass=f=90,lowpass=f=10500,"
                        f"afade=t=in:st=0:d=0.025,afade=t=out:st={max(0.0, raw_duration - .07):.4f}:d=0.07,"
                        "acompressor=threshold=0.12:ratio=1.55:attack=20:release=180:makeup=1.05"
                    ),
                    "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(wav),
                ])
                cache[key] = (raw, wav)
            rows.append({
                "scene": scene_index, "line_number": line_index, "narration": text,
                "rate": rate, "pitch": pitch, "emotion": emotion, "file": str(wav),
                "duration": media_duration(wav), "action_word": ACTION_WORDS[scene_index - 1][line_index - 1],
                "visible_action": VISUAL_ACTIONS[scene_index - 1],
            })
    return rows


def schedule(rows: list[dict]) -> None:
    for scene in range(1, 10):
        group = [row for row in rows if row["scene"] == scene]
        scene_start = (scene - 1) * SCENE_SECONDS
        group[0]["start"] = scene_start + .38
        group[0]["end"] = group[0]["start"] + group[0]["duration"]
        group[1]["start"] = group[0]["end"] + .40
        group[1]["end"] = group[1]["start"] + group[1]["duration"]
        second_pair_span = group[2]["duration"] + .33 + group[3]["duration"]
        group[2]["start"] = max(scene_start + 7.80, group[1]["end"] + .32, scene_start + 15.25 - second_pair_span)
        group[2]["end"] = group[2]["start"] + group[2]["duration"]
        group[3]["start"] = group[2]["end"] + .33
        group[3]["end"] = group[3]["start"] + group[3]["duration"]
        if group[3]["end"] > scene_start + 15.62:
            raise RuntimeError(f"Scene {scene} narration overruns its safe window: {group[3]['end']:.3f}")
        for row in group:
            words = re.findall(r"[A-Za-z0-9’']+", row["narration"])
            normalized = row["narration"].casefold()
            action = row["action_word"].casefold()
            action_index = next((i for i, word in enumerate(words) if action in word.casefold()), len(words) - 1)
            row["estimated_action_word_time"] = row["start"] + row["duration"] * ((action_index + .55) / max(1, len(words)))
            row["scene_start"] = scene_start
            row["visual_action_state_start"] = scene_start + SCENE_SECONDS / 3
            row["visual_end_state_start"] = scene_start + 2 * SCENE_SECONDS / 3
            row["word_count"] = len(words)
            row["spoken_wpm"] = len(words) * 60 / row["duration"]
    for index, row in enumerate(rows):
        row["gap_before"] = row["start"] - (rows[index - 1]["end"] if index else 0.0)
        row["short_gap_flag"] = index > 0 and row["gap_before"] < .30
        row["long_gap_flag"] = index > 0 and row["gap_before"] > 2.0


def overlay_narration(rows: list[dict]) -> Path:
    target = WORK / "combined-narration-track.wav"
    sample_rate = 48000
    samples = array("h", [0]) * round(TOTAL * sample_rate * 2)
    for row in rows:
        with wave.open(row["file"], "rb") as source:
            if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (2, 2, sample_rate):
                raise RuntimeError(f"Unexpected segment format: {row['file']}")
            segment = array("h")
            segment.frombytes(source.readframes(source.getnframes()))
        offset = round(row["start"] * sample_rate * 2)
        for index, value in enumerate(segment):
            position = offset + index
            if position >= len(samples):
                raise RuntimeError("Narration sample escaped the master duration")
            samples[position] = max(-32768, min(32767, samples[position] + value))
    with wave.open(str(target), "wb") as output:
        output.setnchannels(2); output.setsampwidth(2); output.setframerate(sample_rate)
        output.writeframes(samples.tobytes())
    normalized = WORK / "combined-narration-track-normalized.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(target),
        "-af", "loudnorm=I=-20:TP=-3:LRA=7", "-ar", "48000", "-ac", "2",
        "-c:a", "pcm_s16le", str(normalized),
    ])
    normalized.replace(target)
    return target


def make_mix(narration: Path) -> tuple[Path, Path, Path]:
    music = WORK / "music-track.wav"
    effects = WORK / "effects-track.wav"
    shutil.copy2(SOURCE_MUSIC, music)
    shutil.copy2(SOURCE_EFFECTS, effects)
    ducked_music = WORK / "ducked-music-track.wav"
    ducked_effects = WORK / "ducked-effects-track.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(music), "-i", str(narration),
        "-filter_complex", "[0:a]volume=.44[m];[m][1:a]sidechaincompress=threshold=.008:ratio=8:attack=25:release=340:makeup=1[d]",
        "-map", "[d]", "-t", str(TOTAL), "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(ducked_music),
    ])
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(effects), "-i", str(narration),
        "-filter_complex", "[0:a]volume=1.15[e];[e][1:a]sidechaincompress=threshold=.012:ratio=3:attack=18:release=240:makeup=1[d]",
        "-map", "[d]", "-t", str(TOTAL), "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(ducked_effects),
    ])
    final = WORK / "final-mixed-audio-track.wav"
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(narration), "-i", str(ducked_music), "-i", str(ducked_effects),
        "-filter_complex", "[0:a][1:a][2:a]amix=inputs=3:duration=first:normalize=0,lowpass=f=8200:p=2,lowpass=f=8200:p=2,loudnorm=I=-16:TP=-1.5:LRA=8[a]",
        "-map", "[a]", "-t", str(TOTAL), "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(final),
    ])
    return ducked_music, ducked_effects, final


def loudness(path: Path) -> tuple[float, float]:
    result = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-filter_complex", "ebur128=peak=true", "-f", "null", "NUL",
    ], text=True, capture_output=True)
    loud = re.findall(r"I:\s*(-?[0-9.]+) LUFS", result.stderr)
    peak = re.findall(r"Peak:\s*(-?[0-9.]+) dBFS", result.stderr)
    if not loud or not peak:
        raise RuntimeError(f"Unable to measure {path}")
    return float(loud[-1]), float(peak[-1])


def video_hash(path: Path) -> str:
    result = run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-c", "copy", "-f", "hash", "-"])
    return result.stdout.strip()


def write_timing(rows: list[dict]) -> None:
    columns = [
        "scene", "line_number", "start", "end", "gap_before", "duration", "narration",
        "action_word", "estimated_action_word_time", "visual_action_state_start", "visible_action",
        "rate", "pitch", "emotion", "spoken_wpm", "short_gap_flag", "long_gap_flag", "file",
    ]
    with (WORK / "narration-timing-report.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)
    (WORK / "narration-timing-report.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def make_evidence() -> None:
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(OUTPUT),
        "-filter_complex", "showwavespic=s=1600x500:colors=0x1d6f78|0xf3c54b:split_channels=1",
        "-frames:v", "1", "-update", "1", str(WORK / "review-waveform.png"),
    ])
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(OUTPUT),
        "-lavfi", "showspectrumpic=s=1600x700:legend=disabled:color=intensity:scale=sqrt",
        "-frames:v", "1", "-update", "1", str(WORK / "review-spectrum.png"),
    ])


async def main() -> None:
    for path in (SOURCE_VIDEO, SOURCE_MUSIC, SOURCE_EFFECTS):
        if not path.is_file():
            raise FileNotFoundError(path)
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = await make_segments()
    schedule(rows)
    write_timing(rows)
    narration = overlay_narration(rows)
    ducked_music, ducked_effects, final = make_mix(narration)
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(SOURCE_VIDEO), "-i", str(final),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "224k",
        "-ar", "48000", "-ac", "2", "-t", str(TOTAL), "-movflags", "+faststart", str(OUTPUT),
    ])
    decode = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"], capture_output=True)
    narration_lufs, narration_peak = loudness(narration)
    final_lufs, final_peak = loudness(OUTPUT)
    source_vhash, review_vhash = video_hash(SOURCE_VIDEO), video_hash(OUTPUT)
    report = {
        "status": "local-review-only-no-upload", "selected_voice": VOICE_NAME,
        "edge_voice": VOICE, "base_rate": BASE_RATE, "base_pitch": BASE_PITCH,
        "expressive_rate_range": "-5% to -9%", "expressive_pitch_range": "+1Hz to +4Hz",
        "narration_segments": len(rows), "script_lines_changed": 14,
        "wording_changes": 5, "performance_punctuation_changes": 9,
        "narration_loudness_lufs": narration_lufs, "narration_true_peak_dbfs": narration_peak,
        "final_mix_loudness_lufs": final_lufs, "final_mix_true_peak_dbfs": final_peak,
        "minimum_gap_seconds": min(row["gap_before"] for row in rows[1:]),
        "maximum_gap_seconds": max(row["gap_before"] for row in rows[1:]),
        "short_gap_flags": sum(row["short_gap_flag"] for row in rows),
        "long_gap_flags": sum(row["long_gap_flag"] for row in rows),
        "maximum_spoken_line_wpm": max(row["spoken_wpm"] for row in rows),
        "full_decode_passed": decode.returncode == 0,
        "video_bitstream_preserved": source_vhash == review_vhash,
        "source_video_stream_hash": source_vhash, "review_video_stream_hash": review_vhash,
        "source_master_sha256": sha256(SOURCE_VIDEO), "review_sha256": sha256(OUTPUT),
        "output": str(OUTPUT), "combined_narration": str(narration),
        "music_track": str(WORK / "music-track.wav"), "effects_track": str(WORK / "effects-track.wav"),
        "ducked_music_track": str(ducked_music), "ducked_effects_track": str(ducked_effects),
        "final_mixed_audio_track": str(final),
        "uploaded_or_scheduled": False,
    }
    checks = {
        "duration": abs(media_duration(OUTPUT) - TOTAL) < .1,
        "full_decode": decode.returncode == 0,
        "video_preserved": report["video_bitstream_preserved"],
        "all_segments_scene_contained": all(row["scene_start"] <= row["start"] < row["end"] <= row["scene_start"] + SCENE_SECONDS for row in rows),
        "no_short_gaps": report["short_gap_flags"] == 0,
        "no_multi_second_gaps": report["long_gap_flags"] == 0,
        "narration_priority": narration_lufs >= -20.5,
        "final_loudness": -17.0 <= final_lufs <= -15.0,
        "true_peak_safe": final_peak <= -1.0,
        "individual_segment_files": len(list(SEGMENTS.glob("scene-*-line-*-natasha-au.wav"))) == 36,
    }
    report["checks"] = checks
    report["passed"] = all(checks.values())
    (WORK / "audio-review-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    make_evidence()
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise RuntimeError("Ollie narration review failed one or more local gates")


if __name__ == "__main__":
    asyncio.run(main())
