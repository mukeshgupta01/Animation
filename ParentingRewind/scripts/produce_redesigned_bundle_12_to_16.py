"""Create redesigned local-only Parenting Rewind episodes 12 through 16."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import (
    AAP_SLEEP,
    CDC_DIRECTIONS,
    CDC_PRAISE,
    WORK_ROOT,
    produce,
)
from produce_redesigned_bundle_07_to_11 import CDC_CONNECTING


AAP_HOMEWORK = {
    "organization": "American Academy of Pediatrics / HealthyChildren.org",
    "title": "Developing Good Homework Habits",
    "url": "https://www.healthychildren.org/English/ages-stages/gradeschool/school/Pages/Developing-Good-Homework-Habits.aspx",
}


EPISODES = [
    {
        "number": 12,
        "slug": "homework-time-together",
        "title": "Choose a Homework Time Together",
        "asset": "homework-mother-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "source": AAP_HOMEWORK,
        "narration": [
            "Your nine-year-old reaches the homework table already tired, and the first question turns into a daily argument.",
            "There is no single perfect homework time; insisting on one schedule without noticing the child's energy can add conflict.",
            "Pause and discuss the routine when neither of you is in the middle of the struggle.",
            "Offer a workable plan: snack and a short movement break, then homework at the same quiet table; agree on the start cue together.",
            "A regular place and predictable time reduce repeated decisions, while ongoing schoolwork concerns belong in a conversation with the teacher.",
        ],
    },
    {
        "number": 13,
        "slug": "move-close-first",
        "title": "Move Close Before Giving the Direction",
        "asset": "playground-leaving-storyboard-01.png",
        "grid": [2, 3],
        "order": [0, 2, 1, 3, 4, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "At a busy playground, a direction called from across the equipment has to compete with movement, noise, and fun.",
            "Calling it again and again from the gate can turn the first few directions into background sound.",
            "Pause, walk over, and make sure your child is close enough to attend before you speak.",
            "Use one clear statement: One final slide, then take my hand at the gate; keep your voice neutral and follow through.",
            "Closeness, one age-appropriate direction, and a visible next action make the transition easier to understand.",
        ],
    },
    {
        "number": 14,
        "slug": "praise-patient-waiting",
        "title": "Name the Patient Waiting You Notice",
        "asset": "supermarket-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 4, 3, 5],
        "source": CDC_PRAISE,
        "narration": [
            "A child may wait beside the trolley through three aisles, while the one loud request receives most of the attention.",
            "Saying good job at the end is warm, but it does not identify the waiting behavior you hope to see again.",
            "Pause during the ordinary successful moment and describe exactly what you see.",
            "Try: You stayed beside the trolley while I chose the groceries; that was patient and helpful waiting.",
            "Specific praise makes the successful behavior visible to the child and easier for the parent to notice again.",
        ],
    },
    {
        "number": 15,
        "slug": "same-bedtime-sequence",
        "title": "Keep the Bedtime Sequence Familiar",
        "asset": "bedtime-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": AAP_SLEEP,
        "narration": [
            "When bedtime changes every night, a child has to keep asking what happens next and when the routine is really finished.",
            "Extra explanations in the tired moment can make the ending longer without making it more predictable.",
            "Pause and choose a short sequence your family can repeat on ordinary evenings.",
            "For example: pajamas, teeth, one book, cuddle, lights out; show the steps, then follow the same order calmly.",
            "Consistency helps a child know what to expect, and a simple routine can still adapt when illness or safety requires it.",
        ],
    },
    {
        "number": 16,
        "slug": "describe-cooperation",
        "title": "Describe Cooperation Like a Commentator",
        "asset": "kitchen-siblings-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 4, 3, 5],
        "source": CDC_CONNECTING,
        "narration": [
            "During dinner preparation, small cooperative actions can pass unnoticed because the parent is focused on finishing the meal.",
            "Waiting for perfect teamwork means missing the useful steps happening in front of you.",
            "Pause and describe one action in plain language, like a calm sports commentator.",
            "Say: You placed the napkins beside each plate while your sister stirred; both jobs are helping the table get ready.",
            "Description shows attention without exaggeration and gives children clear language for the contribution they just made.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-12-to-16-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
