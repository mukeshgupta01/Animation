"""Create redesigned local-only Parenting Rewind episodes 54 through 58."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import CDC_DIRECTIONS, CDC_PRAISE, WORK_ROOT, produce
from produce_redesigned_bundle_07_to_11 import CDC_CONNECTING
from produce_redesigned_bundle_12_to_16 import AAP_HOMEWORK
from produce_redesigned_bundle_27_to_31 import AAP_CHORES


EPISODES = [
    {
        "number": 54,
        "slug": "soccer-ending-choice",
        "title": "Offer a Choice About How Soccer Ends",
        "asset": "soccer-father-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [2, 0, 1, 5, 3, 4],
        "source": CDC_DIRECTIONS,
        "narration": [
            "A seven-year-old cannot choose whether practice ends, but may still want some control over the transition.",
            "Offering unlimited extra play makes the boundary uncertain, while a command with no next step can feel abrupt.",
            "Pause and offer two acceptable ways to complete the same ending.",
            "Try: Practice is finished; would you like to carry the ball or the water bottle while we walk to the car?",
            "A limited choice keeps the adult's boundary intact and gives the child a useful role in how the transition happens.",
        ],
    },
    {
        "number": 55,
        "slug": "laundry-teamwork-praise",
        "title": "Praise Each Child's Laundry Contribution",
        "asset": "laundry-father-two-children-storyboard-01.png",
        "grid": [2, 3],
        "order": [0, 2, 1, 4, 5, 3],
        "source": CDC_PRAISE,
        "narration": [
            "Two children helping with laundry may contribute in different ways because their ages and skills are different.",
            "A general good job can blur the effort each child made and invite comparison about who helped more.",
            "Pause and describe each useful action separately.",
            "Try: You matched the socks carefully, and you carried the towels to the shelf; both jobs helped us finish.",
            "Specific praise lets each child connect a real action with family teamwork without requiring identical performance.",
        ],
    },
    {
        "number": 56,
        "slug": "library-leaving-preview",
        "title": "Preview the Library Leaving Steps",
        "asset": "library-grandmother-granddaughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [1, 0, 2, 3, 5, 4],
        "source": CDC_DIRECTIONS,
        "narration": [
            "A four-year-old absorbed in books may experience leaving the library as a sudden interruption.",
            "Announcing every step only after resistance begins can turn a simple transition into repeated new demands.",
            "Pause before the final book and preview a short sequence the child can follow.",
            "Try: After this story, choose one book, place the others on the trolley, then hold my hand at the door.",
            "A brief preview makes the ending more predictable while each direction remains concrete enough for a young child.",
        ],
    },
    {
        "number": 57,
        "slug": "screen-time-reconnect",
        "title": "Reconnect After the Screen-Time Limit",
        "asset": "screen-time-storyboard-01.png",
        "grid": [3, 2],
        "order": [1, 2, 0, 4, 3, 5],
        "source": CDC_CONNECTING,
        "narration": [
            "A child may follow the screen-time limit and still be angry about it for several minutes afterward.",
            "Demanding an immediate happy attitude can create a second conflict after the important boundary was already followed.",
            "Pause and reconnect without reopening the decision about the screen.",
            "Try: You wanted more time and stopping was hard; the tablet stays on the shelf, and I am here when you are ready for snack.",
            "Connection after a limit shows that difficult feelings do not threaten the relationship or erase the boundary.",
        ],
    },
    {
        "number": 58,
        "slug": "homework-help-signal",
        "title": "Agree on a Homework Help Signal",
        "asset": "homework-mother-daughter-storyboard-01.png",
        "grid": [2, 3],
        "order": [0, 1, 2, 4, 3, 5],
        "source": AAP_HOMEWORK,
        "narration": [
            "Homework support can become constant interruption when a child calls for help before trying each next step.",
            "Refusing all help or supplying every answer both move attention away from building independent work habits.",
            "Pause and agree on a simple signal that shows when support is genuinely needed.",
            "Try: Circle the question, try the next one, then place this card up when you want me to read the directions with you.",
            "A clear help routine keeps the parent available while leaving thinking, writing, and answers with the child.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-54-to-58-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
