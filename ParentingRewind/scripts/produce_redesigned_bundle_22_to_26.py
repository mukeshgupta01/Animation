"""Create redesigned local-only Parenting Rewind episodes 22 through 26."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import AAP_SLEEP, CDC_DIRECTIONS, CDC_PRAISE, WORK_ROOT, produce
from produce_redesigned_bundle_07_to_11 import CDC_CONNECTING
from produce_redesigned_bundle_12_to_16 import AAP_HOMEWORK


EPISODES = [
    {
        "number": 22,
        "slug": "praise-returning-books",
        "title": "Praise the Book-Returning Step",
        "asset": "library-grandmother-granddaughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 4, 5],
        "source": CDC_PRAISE,
        "narration": [
            "A child may feel disappointed about leaving the library and still return three books carefully.",
            "If attention stays only on the protest, the cooperative step can disappear from the story of what happened.",
            "Pause and notice the helpful action as soon as it occurs.",
            "Try: You put each book gently into the return shelf even though leaving was hard; that was careful helping.",
            "Specific praise does not erase the difficult feeling; it identifies the behavior the child managed inside that feeling.",
        ],
    },
    {
        "number": 23,
        "slug": "listen-to-each-sibling",
        "title": "Listen to One Sibling at a Time",
        "asset": "kitchen-siblings-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 5, 4],
        "source": CDC_CONNECTING,
        "narration": [
            "When two children explain the same argument at once, the volume rises while useful details disappear.",
            "Deciding who is wrong before either child feels heard can restart the conflict instead of settling it.",
            "Pause, separate the turns, and give each child your attention for a short moment.",
            "Say: I will listen to you first, then your brother gets a turn; reflect each feeling without agreeing to hurtful behavior.",
            "One voice at a time makes listening visible and helps the parent choose the next safe, fair action with better information.",
        ],
    },
    {
        "number": 24,
        "slug": "homework-ready-space",
        "title": "Make the Homework Space Ready",
        "asset": "homework-mother-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": AAP_HOMEWORK,
        "narration": [
            "Homework starts, then the child searches for a pencil, moves the backpack, and gets pulled toward another distraction.",
            "Treating every delay as defiance can miss the friction created by an unprepared work area.",
            "Pause and look at the environment before giving another reminder.",
            "Choose a regular well-lit place, keep basic materials nearby, reduce avoidable distractions, and identify the first task.",
            "A ready workspace cannot make every assignment easy, but it removes several barriers between the child and getting started.",
        ],
    },
    {
        "number": 25,
        "slug": "one-playground-warning",
        "title": "Use One Playground Warning",
        "asset": "playground-leaving-storyboard-01.png",
        "grid": [2, 3],
        "order": [0, 1, 2, 4, 3, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Five minutes becomes two minutes, then one more turn, then another final warning at the playground.",
            "Many repeated warnings can teach a child that the early directions are optional.",
            "Pause before the first warning and choose the consequence you can calmly carry out.",
            "Say: Two final turns, then hold my hand to the path; count the turns and follow through after the second.",
            "One clear warning works best when the ending is observable and the adult is ready to complete the transition.",
        ],
    },
    {
        "number": 26,
        "slug": "bedtime-comfort-choice",
        "title": "Offer One Safe Bedtime Comfort Choice",
        "asset": "bedtime-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 5, 4],
        "source": AAP_SLEEP,
        "narration": [
            "At bedtime, a child may want connection and comfort while also testing how far the routine can move.",
            "Adding a brand-new activity each night makes the ending less predictable for everyone.",
            "Pause and choose one safe comfort option that fits inside the existing routine.",
            "Try: Would you like your teddy or your blanket for cuddle time; after the choice, finish the same book-and-lights-out sequence.",
            "A familiar comfort item can support settling while the consistent routine shows where bedtime ends.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-22-to-26-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
