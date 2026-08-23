"""Generate the sung rhyme with the official ACE-Step 1.5 Hugging Face Space."""

from pathlib import Path
import shutil

from gradio_client import Client


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output" / "baa-baa-black-sheep" / "audio" / "ace-step"
OUTPUT = OUTPUT_DIR / "baa-baa-black-sheep-ace-step.mp3"

PROMPT = (
    "Traditional English nursery rhyme for preschool children, genuinely sung by one "
    "warm cheerful female singer with crisp English pronunciation. Familiar Baa Baa "
    "Black Sheep melody, gentle acoustic storybook arrangement, ukulele, marimba, "
    "glockenspiel, soft pizzicato strings and light hand percussion. Simple memorable "
    "tune, steady pulse, bright wholesome mood. Fully melodic singing throughout; no "
    "spoken word, no narration, no rap, no animal sounds."
)

LYRICS = """[Intro - instrumental]

[Verse]
Baa, baa, black sheep,
Have you any wool?
Yes sir, yes sir,
Three bags full.

One for the master,
One for the dame,
And one for the little child
Who lives down the lane.

[Outro - instrumental fade]"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = Client("ACE-Step/Ace-Step-v1.5", httpx_kwargs={"timeout": 120.0})
    args = [
        "acestep-v15-turbo", "custom", PROMPT, "en", PROMPT, LYRICS,
        96, "C Major", "4", "en", 8, 7.0, False, "20260814", None,
        30, 1, None, "", 0.0, -1,
        "Fill the audio semantic mask based on the given conditions:",
        1.0, "text2music", False, 0.0, 1.0, 3.0, "ode", "", "mp3",
        0.85, False, 2.0, 0, 0.9,
        "spoken word, narration, rap, animal sounds, distorted voice",
        False, False, False, False, True, False, True, 0.5, 8,
        "vocals", [], False,
    ]
    result = client.predict(*args, api_name="/generation_wrapper")
    generated = next((Path(item) for item in result[:8] if item), None)
    if generated is None or not generated.exists():
        raise SystemExit(f"ACE-Step Space returned no audio: {result}")
    shutil.copy2(generated, OUTPUT)
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    main()
