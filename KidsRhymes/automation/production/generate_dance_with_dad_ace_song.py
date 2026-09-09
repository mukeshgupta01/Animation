"""Generate a genuinely sung Dance With Dad track with ACE-Step.

The local TTS note-chopping experiment was intelligibility-first in intent but
made consonants unclear in practice.  This generator keeps complete lyric lines
inside a music model and forces the VAE decode onto CPU float32 for stability on
the project's pre-Ampere GPU.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

import numpy as np
import soundfile as sf


PROJECT = Path(__file__).resolve().parents[2]
ITEM_ID = "dance-with-dad-animal-parade-01"
ACE_ROOT = PROJECT / "tools" / "ACE-Step-1.5"
WORK = PROJECT / "automation" / "production-work" / ITEM_ID
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"

sys.path.insert(0, str(ACE_ROOT))
os.environ["ACESTEP_DTYPE"] = "float32"
os.environ["ACESTEP_VAE_ON_CPU"] = "1"

from acestep.handler import AceStepHandler  # noqa: E402
from acestep.inference import GenerationConfig, GenerationParams, generate_music  # noqa: E402


def lyric_block(plan: dict, first_scene: int, last_scene: int) -> str:
    scenes = plan["scenes"][first_scene:last_scene]
    sections: list[str] = []
    for local_index, scene in enumerate(scenes):
        index = first_scene + local_index
        label = "Chorus" if index in (0, 6, 7) else "Verse"
        sections.append(f"[{label}]\n" + "\n".join(scene["lyrics"]))
    return "\n\n".join(sections)


def generate_section(handler: AceStepHandler, plan: dict, section: int, out_dir: Path) -> np.ndarray:
    first_scene = section * 2
    params = GenerationParams(
        task_type="text2music",
        thinking=False,
        use_cot_metas=False,
        use_cot_caption=False,
        use_cot_language=False,
        caption=(
            "Fun lively children's Father's Day singalong, exceptionally clear English diction, "
            "warm child lead with friendly dad responses and a small children's chorus, D major, "
            "bright ukulele, marimba, handclaps and light drums, catchy simple melody, no spoken "
            "narration, no hiss, no distortion, complete words, family friendly"
        ),
        lyrics=lyric_block(plan, first_scene, first_scene + 2),
        bpm=120,
        keyscale="D major",
        timesignature="4/4",
        vocal_language="en",
        duration=24.0,
        inference_steps=8,
        guidance_scale=1.0,
        seed=260903,
        latent_rescale=1.0,
    )
    config = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[260903], audio_format="wav32")
    section_dir = out_dir / f"section-{section + 1}"
    section_dir.mkdir(parents=True, exist_ok=True)
    result = generate_music(handler, None, params=params, config=config, save_dir=str(section_dir))
    if not result.success or not result.audios:
        raise RuntimeError(result.error or result.status_message)
    generated = Path(result.audios[0]["path"])
    samples, sample_rate = sf.read(generated, always_2d=True, dtype="float32")
    if sample_rate != 48000 or samples.size == 0 or not np.isfinite(samples).all():
        raise RuntimeError(f"ACE-Step section {section + 1} produced invalid audio")
    return samples


def instrumental_resolve(rate: int = 48000, duration: float = 4.0) -> np.ndarray:
    count = round(rate * duration)
    t = np.arange(count, dtype=np.float64) / rate
    fade = np.minimum(1.0, t / 0.08) * np.maximum(0.0, (duration - t) / 3.5)
    chord = sum(np.sin(2 * np.pi * frequency * t) for frequency in (293.66, 369.99, 440.0))
    bell = np.sin(2 * np.pi * 587.33 * t) * np.exp(-2.4 * t)
    mono = (0.055 * chord + 0.08 * bell) * fade
    return np.column_stack((mono, mono)).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Generate a short two-scene clarity test")
    args = parser.parse_args()

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    out_dir = WORK / ("ace-step-v5-preview" if args.preview else "ace-step-v5")
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = WORK / ("dance-with-dad-ace-preview-v5.wav" if args.preview else "dance-with-dad-sung-song-v5.wav")

    handler = AceStepHandler()
    status, success = handler.initialize_service(
        project_root=str(ACE_ROOT),
        config_path="acestep-v15-turbo",
        device="cuda",
        offload_to_cpu=True,
        offload_dit_to_cpu=True,
        quantization="int8_weight_only",
    )
    if not success:
        raise RuntimeError(status)

    section_count = 1 if args.preview else 4
    sections = [generate_section(handler, plan, section, out_dir) for section in range(section_count)]
    if not args.preview:
        # Ten-millisecond boundary fades prevent clicks without changing the
        # exact 24-second bar-aligned duration of any section.
        fade_samples = 480
        ramp = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)[:, None]
        for index, samples in enumerate(sections):
            if index:
                samples[:fade_samples] *= ramp
            if index < len(sections) - 1:
                samples[-fade_samples:] *= ramp[::-1]
        sections.append(instrumental_resolve())
    samples = np.concatenate(sections, axis=0)
    if samples.size == 0 or not np.isfinite(samples).all() or float(np.max(np.abs(samples))) < 1e-5:
        raise RuntimeError("ACE-Step produced invalid or silent audio")
    sf.write(destination, samples, 48000, subtype="FLOAT")
    print(destination)
    print(f"sample_rate=48000 peak={float(np.max(np.abs(samples))):.6f}")


if __name__ == "__main__":
    main()
