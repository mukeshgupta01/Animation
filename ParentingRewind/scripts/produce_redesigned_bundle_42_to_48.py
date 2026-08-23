"""Create redesigned local-only Parenting Rewind episodes 42 through 48."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import AAP_SLEEP, CDC_DIRECTIONS, CDC_PRAISE, WORK_ROOT, produce
from produce_redesigned_bundle_07_to_11 import CDC_CONNECTING
from produce_redesigned_bundle_12_to_16 import AAP_HOMEWORK
from produce_redesigned_bundle_27_to_31 import AAP_CHORES


EPISODES = [
    {
        "number": 42,
        "slug": "shopping-job-before-entry",
        "title": "Give a Shopping Job Before You Enter",
        "asset": "supermarket-storyboard-01.png",
        "grid": [3, 2],
        "order": [1, 0, 2, 4, 3, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "A busy supermarket asks a five-year-old to wait, follow, ignore bright displays, and remember rules all at once.",
            "Giving directions only after grabbing begins can leave the child without a clear role during the hardest moments.",
            "Pause before entering and offer one concrete, age-appropriate job.",
            "Try: Stay beside the trolley and find three red apples for our bag; when that is done, I will give you the next job.",
            "A specific job gives attention somewhere useful while one-step directions remain easier to understand and praise.",
        ],
    },
    {
        "number": 43,
        "slug": "bedtime-choice-inside-boundary",
        "title": "Offer a Bedtime Choice Inside the Boundary",
        "asset": "bedtime-father-daughter-storyboard-01.png",
        "grid": [2, 3],
        "order": [1, 0, 3, 2, 4, 5],
        "source": AAP_SLEEP,
        "narration": [
            "At bedtime, a six-year-old may fight for control over every small step even when the need for sleep has not changed.",
            "Turning lights-out itself into a choice can accidentally make the boundary sound open for negotiation.",
            "Pause and keep the limit steady while offering control over a detail that is genuinely flexible.",
            "Try: It is time for bed; would you like the moon pajamas or the striped pajamas before our one story?",
            "A small real choice can support cooperation without changing the calm, predictable sequence that ends the day.",
        ],
    },
    {
        "number": 44,
        "slug": "sibling-turns-visible",
        "title": "Make Sibling Turns Visible",
        "asset": "kitchen-siblings-storyboard-01.png",
        "grid": [3, 2],
        "order": [2, 0, 1, 4, 3, 5],
        "source": CDC_CONNECTING,
        "narration": [
            "When two children both want the same kitchen job, repeated promises that everyone will get a turn can still feel uncertain.",
            "Arguing over who asked first keeps attention on fairness claims instead of showing when each turn will happen.",
            "Pause and make the sequence visible with names, pictures, or a short timer.",
            "Try: Your sister stirs until the timer rings, then you pour the measured cup while she carries the napkins.",
            "A visible sequence acknowledges both children and lets the parent follow through without reopening the decision each minute.",
        ],
    },
    {
        "number": 45,
        "slug": "soccer-effort-praise",
        "title": "Praise the Soccer Effort You Saw",
        "asset": "soccer-father-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [1, 2, 0, 4, 5, 3],
        "source": CDC_PRAISE,
        "narration": [
            "A missed goal can make a seven-year-old feel that the whole practice was a failure.",
            "Saying you were amazing may be kind, but it can miss the specific effort the child can recognize and repeat.",
            "Pause and describe one action you genuinely noticed.",
            "Try: You kept your eyes on the ball, tried the pass again, and stayed with your team after the miss.",
            "Specific praise separates effort and teamwork from the final score without asking the child to ignore disappointment.",
        ],
    },
    {
        "number": 46,
        "slug": "laundry-teach-then-step-back",
        "title": "Teach the Chore, Then Step Back",
        "asset": "laundry-father-two-children-storyboard-01.png",
        "grid": [2, 3],
        "order": [1, 0, 2, 3, 5, 4],
        "source": AAP_CHORES,
        "narration": [
            "A child learning to fold towels will work more slowly and less neatly than an adult who has done it for years.",
            "Correcting every corner or taking the towel back can turn a family contribution into a performance test.",
            "Pause, demonstrate one manageable step, and leave room for practice.",
            "Try: Match these two corners, press the fold once, and place the towel in this stack; I will help if you ask.",
            "Clear teaching plus reasonable expectations lets competence grow while the child still contributes real work to the household.",
        ],
    },
    {
        "number": 47,
        "slug": "library-reflect-excitement",
        "title": "Reflect the Library Excitement",
        "asset": "library-grandmother-granddaughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [2, 1, 0, 3, 5, 4],
        "source": CDC_CONNECTING,
        "narration": [
            "A four-year-old who finds several favorite books may talk loudly and move quickly through a quiet library.",
            "Starting with shushing can miss the excitement driving the behavior and make the limit harder to hear.",
            "Pause, reflect the feeling briefly, then give the next clear direction.",
            "Try: You found so many stories you love; use your quiet voice and carry these two books with me to the desk.",
            "Acknowledging excitement does not remove the library limit; it creates connection before the child practices it.",
        ],
    },
    {
        "number": 48,
        "slug": "screen-time-plan-before-play",
        "title": "Make the Screen-Time Ending Plan First",
        "asset": "screen-time-storyboard-01.png",
        "grid": [2, 3],
        "order": [0, 2, 1, 3, 4, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Ending a game feels more abrupt when a child hears the plan only at the exact moment the screen turns off.",
            "Adding several last-minute warnings can still leave the final action unclear and invite a new negotiation each time.",
            "Pause before play begins and state one concrete ending sequence.",
            "Try: When this episode ends, press stop, place the tablet on the shelf, and meet me at the table for snack.",
            "A plan given before the exciting activity makes follow-through more predictable while the same calm boundary remains in place.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-42-to-48-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
