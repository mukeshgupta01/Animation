"""Create an age-diverse Parenting Rewind bundle: episodes 74 through 76."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce


CTA = "If this helped, like and subscribe for more practical Parenting Rewind ideas."
PROMPT_RECORD = "production-assets/storyboard-prompts-74-to-76.md"

EPISODES = [
    {
        "number": 74,
        "slug": "stop-biting-without-shame",
        "title": "Stop Biting Without Calling Your Toddler Bad",
        "asset": "toddler-biting-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-08-26",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "10 Tips to Prevent Aggressive Behavior in Young Children",
            "url": "https://www.healthychildren.org/English/ages-stages/toddler/Pages/Aggressive-Behavior.aspx",
        },
        "new_image_generation_calls": 1,
        "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your toddler bites during a toy struggle, and shock can make the first words sound like a label: Why are you so bad?",
            "A two-year-old still has very little impulse control, but the safety limit must be immediate and clear.",
            "Pause, separate the children calmly, check the other child, and say: I will not let you bite; biting hurts.",
            "Once everyone is calm, teach the missing action: say mine, ask for help, or bring the toy to an adult.",
            "Notice gentle hands when they happen, and ask your pediatrician for support if aggression is frequent, severe, or hard to manage.",
            CTA,
        ],
    },
    {
        "number": 75,
        "slug": "listen-before-fixing-bullying",
        "title": "When Your Child Reports Bullying, Listen Before You Fix",
        "asset": "bullying-disclosure-mother-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 5, 4],
        "reviewed_on": "2026-08-26",
        "source": {
            "organization": "U.S. Department of Health and Human Services / StopBullying.gov",
            "title": "How to Talk About Bullying",
            "url": "https://www.stopbullying.gov/resources/how-to-talk-about-bullying",
        },
        "new_image_generation_calls": 1,
        "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your child quietly says the same kids keep targeting him, and your alarm may jump straight to calls, accusations, and a complete rescue plan.",
            "Moving too fast can make him feel unheard or afraid that telling you will make school even harder.",
            "Pause, thank him for telling you, say it is not his fault, and listen for what happened, where, how often, and who feels safe at school.",
            "Ask what would help him feel safer, write down the facts together, and contact the school through its bullying process without asking him to confront the other child.",
            "Treat threats, injury, or immediate danger urgently; otherwise keep checking in so support continues after the first report.",
            CTA,
        ],
    },
    {
        "number": 76,
        "slug": "look-at-week-teen-overloaded",
        "title": "When Your Teen Is Overloaded, Look at the Week Together",
        "asset": "teen-grade-mother-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 5, 4],
        "reviewed_on": "2026-08-26",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "The 5Rs: Ways to Support Your Teen's Resilience During Stressful Times",
            "url": "https://www.healthychildren.org/English/healthy-living/emotional-wellness/Building-Resilience/Pages/the-5rs-ways-to-support-your-teens-resilience-during-stressful-times.aspx",
        },
        "recycled_visuals_approved": True,
        "new_image_generation_calls": 0,
        "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your teen says, I cannot keep up, and the parent alarm may answer with a lecture about effort before you know what is overloaded.",
            "Stress can come from school, sport, friendships, sleep, or too many commitments, so do not assume the first explanation is the whole story.",
            "Pause, listen without judgment, and try: I am glad you told me; let us look at the week and see what feels impossible right now.",
            "Choose one practical adjustment together, protect basic routines like sleep and meals, and agree on when you will check in again.",
            "If stress is persistent, disrupts daily life, or raises any safety concern, involve a pediatrician or qualified mental-health professional.",
            CTA,
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-74-to-76-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": True, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
