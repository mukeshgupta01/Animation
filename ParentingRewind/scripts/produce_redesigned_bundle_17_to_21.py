"""Create redesigned local-only Parenting Rewind episodes 17 through 21."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import CDC_DIRECTIONS, WORK_ROOT, produce
from produce_redesigned_bundle_07_to_11 import CDC_CONNECTING
from produce_redesigned_bundle_12_to_16 import AAP_HOMEWORK


EPISODES = [
    {
        "number": 17,
        "slug": "library-one-book-choice",
        "title": "Use One Real Choice at the Library",
        "asset": "library-grandmother-granddaughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Story time is ending, but your four-year-old is holding five books and wants the library visit to continue.",
            "Saying choose anything and then rejecting each choice creates more decisions in an already difficult transition.",
            "Pause and decide what the real limit allows before offering an option.",
            "Say: You may choose one book to borrow; do you want the animal book or the space book, then help return the others.",
            "Two acceptable options support independence while the clear leaving plan keeps the boundary understandable.",
        ],
    },
    {
        "number": 18,
        "slug": "reflect-before-solving",
        "title": "Reflect the Feeling Before Solving",
        "asset": "screen-time-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "source": CDC_CONNECTING,
        "narration": [
            "Your child loses a game when screen time ends and says the whole evening is ruined.",
            "Jumping straight to solutions can miss the feeling the child is trying to communicate.",
            "Pause, give your full attention, and reflect what you heard in a few calm words.",
            "Try: You worked hard on that game and losing at the end felt really disappointing; I am listening.",
            "Reflection does not require agreement or a changed limit; it shows the child that their experience reached you.",
        ],
    },
    {
        "number": 19,
        "slug": "homework-transition-warning",
        "title": "Warn Before Homework Starts",
        "asset": "homework-mother-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 4, 5],
        "source": AAP_HOMEWORK,
        "narration": [
            "A child can agree to a homework time and still struggle when play stops and the worksheet suddenly appears.",
            "An abrupt start cue may turn the transition itself into the conflict before any schoolwork begins.",
            "Pause and make the agreed homework time easier to anticipate.",
            "Try one ten-minute warning, prepare the quiet workspace, then begin with the first clearly identified task.",
            "A regular place, a predictable start time, and a brief warning can help the child shift into a homework frame of mind.",
        ],
    },
    {
        "number": 20,
        "slug": "say-what-to-do-shopping",
        "title": "Say What to Do in the Shop",
        "asset": "supermarket-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Do not run, do not touch, and stop wandering tell a child what is wrong without showing the useful replacement.",
            "Several negative instructions at once are hard to hold onto in a busy supermarket.",
            "Pause and name the one behavior you need right now.",
            "Say: Please keep one hand on the trolley while we walk to the next aisle; point to the handle as a visual cue.",
            "A specific positive direction gives the child an action they can understand, complete, and receive praise for.",
        ],
    },
    {
        "number": 21,
        "slug": "direction-not-question",
        "title": "Make the Direction a Statement",
        "asset": "pilot-01-shoe-storyboard.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Can you put your shoes on sounds polite, but a yes-or-no question also makes no sound like an available answer.",
            "Asking again with more urgency can create a debate that the parent never intended to open.",
            "Pause and separate respectful wording from optional wording.",
            "Try a clear statement: Please put on your shoes now; you may choose the red pair or the blue pair.",
            "The direction stays firm while the limited choice gives the child a real piece of control inside the boundary.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-17-to-21-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
