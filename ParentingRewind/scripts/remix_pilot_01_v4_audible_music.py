"""Remix pilot 01 with clearly audible, narration-ducked dynamic music.

The visual stream, V2 narration clips, and V3 original score are reused. No
image, speech, or music generation service is called.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import produce_pilot_01_v2 as conversational


base = conversational.base
PROJECT = base.PROJECT
V3_VIDEO = PROJECT / "output" / "parenting-rewind-pilot-01-shoes-v3-dynamic-music.mp4"
V3_SCORE = PROJECT / "production-work" / "pilot-01-shoes-v3-dynamic-music" / "original-dynamic-emotional-score.wav"
OUTPUT = PROJECT / "output" / "parenting-rewind-pilot-01-shoes-v4-audible-dynamic-music.mp4"
WORK = PROJECT / "production-work" / "pilot-01-shoes-v4-audible-dynamic-music"


def remix() -> None:
    if OUTPUT.exists():
        print(f"Completed V4 already exists; preserving without regeneration: {OUTPUT}")
        return
    if not V3_VIDEO.exists():
        raise FileNotFoundError(V3_VIDEO)
    if not V3_SCORE.exists():
        raise FileNotFoundError(V3_SCORE)

    events, total = base.make_timeline()
    inputs = ["-i", str(V3_VIDEO), "-i", str(V3_SCORE)]
    filters: list[str] = []
    voice_labels: list[str] = []

    for input_index, event in enumerate(events, start=2):
        voice = base.WORK / f"voice-{event['key']}.mp3"
        if not voice.exists():
            raise FileNotFoundError(voice)
        inputs.extend(["-i", str(voice)])
        delay = round(event["voice_start"] * 1000)
        filters.append(
            f"[{input_index}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"adelay={delay}|{delay},volume=1.18[v{input_index}]"
        )
        voice_labels.append(f"[v{input_index}]")

    filters.append(
        "".join(voice_labels)
        + f"amix=inputs={len(voice_labels)}:normalize=0:dropout_transition=0,"
        + "alimiter=limit=.93[voice_mix]"
    )
    filters.append("[voice_mix]asplit=2[voice_sidechain][voice_final]")

    # Raise the original score by about 9.5 dB. Side-chain compression then
    # lowers it only while speech is present, allowing transitions to breathe.
    filters.append(
        "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
        "volume=3.0,alimiter=limit=.90[music_full]"
    )
    filters.append(
        "[music_full][voice_sidechain]sidechaincompress="
        "threshold=.025:ratio=3.2:attack=18:release=320[music_ducked]"
    )
    filters.append(
        "[music_ducked][voice_final]amix=inputs=2:normalize=0:dropout_transition=0,"
        "alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=9[a]"
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-t",
            f"{total:.3f}",
            "-movflags",
            "+faststart",
            str(OUTPUT),
        ],
        check=True,
    )

    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,size",
                "-show_entries",
                "stream=codec_name,codec_type,width,height,sample_rate,channels",
                "-of",
                "json",
                str(OUTPUT),
            ],
            text=True,
        )
    )
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    checks = {
        "nontrivial_size": OUTPUT.stat().st_size > 1_500_000,
        "duration": abs(float(probe["format"]["duration"]) - total) < 0.30,
        "vertical_h264": video.get("codec_name") == "h264" and video.get("width") == 1080 and video.get("height") == 1920,
        "aac_48khz_stereo": audio.get("codec_name") == "aac" and audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
    }
    report = {
        "version": "v4-audible-dynamic-music",
        "output": str(OUTPUT),
        "duration_seconds": float(probe["format"]["duration"]),
        "music_gain_db_approx": 9.54,
        "narration_sidechain_ducking": True,
        "checks": checks,
        "passed": all(checks.values()),
    }
    (WORK / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise RuntimeError(f"V4 quality gate failed: {report}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    remix()
