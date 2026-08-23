"""Generate a genuinely sung Baa Baa Black Sheep track with ACE-Step 1.5."""

from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parent
ACE_ROOT = ROOT / "tools" / "ACE-Step-1.5"
OUTPUT = ROOT / "output" / "baa-baa-black-sheep" / "audio" / "ace-step"
SOURCE = ROOT / "output" / "baa-baa-black-sheep" / "audio" / "storybook-arrangement-35s.wav"
# The T550's native float16 path is paired with conservative sampler controls
# below to avoid the overflow seen with aggressive timestep shifting.
os.environ.setdefault("ACESTEP_DTYPE", "float16")
# Float32 generation with CPU offload is deliberately slow on a 4 GB GPU.
# Give ACE-Step enough time to finish instead of its default 600-second cutoff.
os.environ.setdefault("ACESTEP_GENERATION_TIMEOUT", "1800")
sys.path.insert(0, str(ACE_ROOT))

from acestep.handler import AceStepHandler
from acestep.inference import GenerationConfig, GenerationParams, generate_music
from acestep.llm_inference import LLMHandler


LYRICS = """[Intro - instrumental]

[Verse 1]
Baa, baa, black sheep,
Have you any wool?
Yes sir, yes sir,
Three bags full.

[Verse 2]
One for the master,
One for the dame,
And one for the little child
Who lives down the lane.

[Outro - instrumental fade]"""


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    handler = AceStepHandler()
    status, ready = handler.initialize_service(
        project_root=str(ACE_ROOT),
        config_path="acestep-v15-turbo",
        device="cuda",
        use_flash_attention=False,
        compile_model=False,
        offload_to_cpu=True,
        offload_dit_to_cpu=True,
        quantization="int8_weight_only",
        use_mlx_dit=False,
    )
    print(status)
    if not ready:
        raise SystemExit("ACE-Step DiT initialization failed")

    params = GenerationParams(
        task_type="text2music",
        caption=(
            "Traditional English nursery rhyme for preschool children, genuinely sung by "
            "one warm cheerful female singer with crisp English pronunciation. Familiar "
            "Baa Baa Black Sheep melody, gentle acoustic storybook arrangement, ukulele, "
            "marimba, glockenspiel, soft pizzicato strings and light hand percussion. "
            "Simple memorable tune, steady pulse, bright wholesome mood. Fully melodic "
            "singing throughout; no spoken word, no narration, no rap, no animal sounds."
        ),
        lyrics=LYRICS,
        instrumental=False,
        vocal_language="en",
        bpm=96,
        keyscale="C Major",
        timesignature="4",
        duration=30,
        inference_steps=8,
        seed=20260814,
        shift=1.0,
        audio_cover_strength=0.72,
        dcw_enabled=False,
        velocity_norm_threshold=2.0,
        thinking=False,
        use_cot_metas=False,
        use_cot_caption=False,
        use_cot_language=False,
    )
    config = GenerationConfig(
        batch_size=1,
        use_random_seed=False,
        seeds=[20260814],
        audio_format="wav",
    )
    result = generate_music(handler, LLMHandler(), params, config, save_dir=str(OUTPUT))
    if not result.success:
        raise SystemExit(f"ACE-Step generation failed: {result.error}")
    for audio in result.audios:
        print(f"Generated: {audio['path']}")


if __name__ == "__main__":
    main()
