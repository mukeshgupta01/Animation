"""Create redesigned local-only Parenting Rewind episodes 37 through 41."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import CDC_DIRECTIONS, CDC_PRAISE, WORK_ROOT, produce
from produce_redesigned_bundle_12_to_16 import AAP_HOMEWORK
from produce_redesigned_bundle_27_to_31 import AAP_CHORES


EPISODES = [
    {
        "number": 37,
        "slug": "soccer-final-shot",
        "title": "Make the Final Soccer Turn Concrete",
        "asset": "soccer-father-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Five more minutes at soccer practice is hard for a seven-year-old to measure while running with the ball.",
            "A vague time warning can end with parent and child holding different ideas about when play should stop.",
            "Pause and choose an ending the child can see and complete.",
            "Say: One final shot, then place the ball in the bag and walk with me; stay close and follow through after the shot.",
            "A concrete final action turns an abstract time limit into a clear sequence without reopening the decision.",
        ],
    },
    {
        "number": 38,
        "slug": "visual-chore-plan",
        "title": "Make the Chore Plan Visible",
        "asset": "laundry-father-two-children-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 5, 4],
        "source": AAP_CHORES,
        "narration": [
            "The same laundry directions can disappear between the family room and the basket ten minutes later.",
            "More verbal reminders may add tension without giving children a stable way to remember their separate jobs.",
            "Pause and turn the routine into a simple visible plan.",
            "Use two pictures: towels for the older child and socks for the younger child; point to the plan, then introduce changes one at a time.",
            "A visual reminder supports the routine while specific praise helps each child connect effort with family contribution.",
        ],
    },
    {
        "number": 39,
        "slug": "one-library-direction",
        "title": "Give One Library Direction at a Time",
        "asset": "library-grandmother-granddaughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Choose a book, return the others, put on your bag, and come to the door is a lot for a four-year-old at once.",
            "When only the first piece happens, repeating the entire list can make the next step less clear.",
            "Pause and give one short age-appropriate direction at a time.",
            "Start with: Place these books on the return shelf; after that is complete, give the direction to hold hands for leaving.",
            "Short sequential directions make it easier to notice understanding, help when needed, and praise each successful step.",
        ],
    },
    {
        "number": 40,
        "slug": "praise-homework-start",
        "title": "Praise the Homework Start",
        "asset": "homework-mother-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 5, 4],
        "source": AAP_HOMEWORK,
        "narration": [
            "A child may spend several hard minutes settling, then quietly write a name and begin the first question.",
            "Waiting until the whole worksheet is perfect misses the effort required to cross the starting line.",
            "Pause and notice the specific beginning behavior without interrupting concentration for long.",
            "Try: You got your pencil, sat at the agreed table, and started question one; that was a strong start.",
            "Honest attention to the routine and effort can support independence while the child's actual answers remain their own work.",
        ],
    },
    {
        "number": 41,
        "slug": "praise-leaving-playground",
        "title": "Praise the Leaving Step You Saw",
        "asset": "playground-leaving-storyboard-01.png",
        "grid": [2, 3],
        "order": [0, 2, 1, 4, 3, 5],
        "source": CDC_PRAISE,
        "narration": [
            "A three-year-old can feel upset about leaving and still walk from the slide to the gate holding a parent's hand.",
            "Calling the whole transition bad because of the protest hides the successful safety behavior at the end.",
            "Pause and name the action that helped everyone leave safely.",
            "Try: You held my hand all the way from the slide to the path even while you felt sad about leaving.",
            "Specific praise recognizes the skill the child used without pretending the transition or the feeling was easy.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-37-to-41-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
