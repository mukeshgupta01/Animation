"""Create a varied Parenting Rewind bundle: episodes 77 through 79."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce


CTA = "If this helped, like and subscribe for more practical Parenting Rewind ideas."
PROMPT_RECORD = "production-assets/storyboard-prompts-77-to-79.md"

EPISODES = [
    {
        "number": 77,
        "slug": "preschool-night-waking-same-routine",
        "title": "When Your Preschooler Wakes at Night, Return to the Same Routine",
        "asset": "preschool-night-waking-mother-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-08-26",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "Healthy Sleep Habits: How Many Hours Does Your Child Need?",
            "url": "https://www.healthychildren.org/English/healthy-living/sleep/Pages/Healthy-Sleep-Habits-How-Many-Hours-Does-Your-Child-Need.aspx",
        },
        "new_image_generation_calls": 1,
        "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your four-year-old appears beside your bed again, and exhaustion can turn the middle of the night into a long negotiation.",
            "When the response changes each time, a child cannot predict whether waking means play, conversation, or a return to sleep.",
            "Pause, keep the room dim, check that your child is safe and well, and use the same brief words: You are safe; it is sleep time; I will walk you back.",
            "Return to the familiar sleep cues, such as one comfort toy, the same blanket, and a quiet goodnight, without starting a new activity.",
            "Consistency is the goal, not instant sleep. If waking is persistent, or comes with snoring, loud breathing, pain, or daytime sleepiness, talk with your child's pediatrician.",
            CTA,
        ],
    },
    {
        "number": 78,
        "slug": "one-mistake-wants-to-quit",
        "title": "When One Mistake Makes Your Child Want to Quit",
        "asset": "art-studio-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 4, 3, 5],
        "reviewed_on": "2026-08-26",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "Building Blocks for Healthy Self Esteem in Kids",
            "url": "https://www.healthychildren.org/English/ages-stages/gradeschool/Pages/Helping-Your-Child-Develop-A-Healthy-Sense-of-Self-Esteem.aspx",
        },
        "recycled_visuals_approved": True,
        "new_image_generation_calls": 0,
        "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "One tear in the artwork, and your child says, I am terrible at this; I quit.",
            "Rushing to say it is perfect, or taking over the repair, can miss the chance to show that mistakes belong inside learning.",
            "Pause and name what you saw: You worked carefully, and this did not turn out the way you hoped.",
            "Then ask one process question: What did you try before it tore, and what might you try next?",
            "Offer support without owning the result: a hint, help with one step, or time to try again. Praise the effort and the adjustment, not a flawless product.",
            CTA,
        ],
    },
    {
        "number": 79,
        "slug": "teen-driving-written-safety-plan",
        "title": "Before Your Teen Drives Alone, Put the Safety Plan in Writing",
        "asset": "teen-driving-agreement-mother-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 5, 4],
        "reviewed_on": "2026-08-26",
        "source": {
            "organization": "Centers for Disease Control and Prevention",
            "title": "Parent-Teen Driving Agreement",
            "url": "https://www.cdc.gov/teen-drivers/parents-are-the-key/driving-agreement.html",
        },
        "new_image_generation_calls": 1,
        "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your new driver reaches for the keys, and fear can come out as one vague instruction: Just be careful.",
            "A vague warning does not define what safe driving means, or what happens when a rule is broken.",
            "Pause and put the plan in writing together before the first solo trip.",
            "Cover seat belts, phones, passengers, night driving, weather, approved routes, who to call, and clear consequences, then match every rule to your local graduated-licensing laws.",
            "Keep practicing together, model the same safe habits yourself, and update privileges as experience and responsibility grow.",
            CTA,
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-77-to-79-ledger.json").write_text(
            json.dumps(
                {"approved": True, "upload_authorized": True, "results": results},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
