"""Create redesigned local-only Parenting Rewind episodes 32 through 36."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import AAP_SLEEP, CDC_DIRECTIONS, CDC_PRAISE, WORK_ROOT, produce
from produce_redesigned_bundle_07_to_11 import CDC_CONNECTING
from produce_redesigned_bundle_27_to_31 import AAP_CHORES


EPISODES = [
    {
        "number": 32,
        "slug": "praise-chore-effort",
        "title": "Praise Chore Effort, Not Perfect Folding",
        "asset": "laundry-father-two-children-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 4, 5],
        "source": AAP_CHORES,
        "narration": [
            "A ten-year-old's folded towel may not match the neat stack an adult could make in half the time.",
            "Refolding everything immediately can turn a contribution into evidence that the child's work was not useful.",
            "Pause and decide whether the result is safe and good enough for the skill being learned.",
            "Try: You stayed with the whole towel stack and lined up the corners carefully; that effort helped our family.",
            "Honest praise for effort and completion supports responsibility while coaching can improve the skill gradually.",
        ],
    },
    {
        "number": 33,
        "slug": "quiet-bedtime-routine",
        "title": "Shift to Quiet Before Bed",
        "asset": "bedtime-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 5, 4],
        "source": AAP_SLEEP,
        "narration": [
            "A fast game right before lights out can leave a child's body excited while the clock says it is time to sleep.",
            "Demanding instant calm after active play asks the transition to do too much work at once.",
            "Pause and move the energetic activity earlier in the evening.",
            "Build a quiet final sequence such as washing, pajamas, one book, and a brief cuddle in the same order.",
            "A calm predictable routine gives the child repeated cues that the day is slowing down and sleep comes next.",
        ],
    },
    {
        "number": 34,
        "slug": "library-feeling-reflection",
        "title": "Reflect the Library Disappointment",
        "asset": "library-grandmother-granddaughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 5, 4],
        "source": CDC_CONNECTING,
        "narration": [
            "A child can understand that the library is closing and still feel deeply disappointed that reading time is over.",
            "Explaining the closing time again may answer the facts while missing the emotion.",
            "Pause, come to the child's level, and reflect the experience you see.",
            "Say: You found books you love and you wish we could stay longer; we are leaving now, and we can plan another visit.",
            "Naming the feeling communicates understanding while the clear leaving statement keeps the transition moving.",
        ],
    },
    {
        "number": 35,
        "slug": "direction-then-wait",
        "title": "Give the Direction, Then Wait",
        "asset": "pilot-01-shoe-storyboard.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 5, 4],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Please put on your shoes can be followed by three more reminders before the child has processed the first sentence.",
            "Rapid repeated language can make a simple direction harder to identify.",
            "Pause, get the child's attention, give one age-appropriate statement, and allow a brief moment to respond.",
            "Try: Please put on the red shoes; stay nearby without filling the pause with a new instruction.",
            "One clear direction at a time helps the parent see whether the child understood, needs help, or is choosing not to follow it.",
        ],
    },
    {
        "number": 36,
        "slug": "praise-separate-contributions",
        "title": "Praise Each Child's Separate Contribution",
        "asset": "kitchen-siblings-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": CDC_PRAISE,
        "narration": [
            "When siblings work together, a general good job can blur the different efforts each child made.",
            "The quieter contribution is especially easy to miss when one child has the more visible task.",
            "Pause and name one observable action from each child.",
            "Try: You stirred slowly so the bowl stayed steady, and you placed every napkin beside a plate.",
            "Separate specific praise shows both children that their own useful behavior was noticed without turning the moment into a comparison.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-32-to-36-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
