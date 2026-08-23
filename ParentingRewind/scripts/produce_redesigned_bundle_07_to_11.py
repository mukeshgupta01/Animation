"""Create redesigned local-only Parenting Rewind episodes 07 through 11."""

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


CDC_CONNECTING = {
    "organization": "Centers for Disease Control and Prevention",
    "title": "Tips for Connecting and Communicating",
    "url": "https://www.cdc.gov/parenting-toddlers/communication/",
}


EPISODES = [
    {
        "number": 7,
        "slug": "checkout-choices",
        "title": "When the Checkout Request Becomes a Battle",
        "asset": "supermarket-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 5, 4],
        "source": CDC_DIRECTIONS,
        "narration": [
            "The checkout display appears, your five-year-old asks for a treat, and the line behind you keeps moving.",
            "A long explanation can become an accidental negotiation when the answer has already been decided.",
            "Pause, get close, and choose two options you can genuinely accept.",
            "Say: We are not buying checkout sweets today; you may help place the apples on the belt or hold the shopping list.",
            "A short direction and two bounded choices give the child a useful next action without changing the limit.",
        ],
    },
    {
        "number": 8,
        "slug": "one-step-morning",
        "title": "One Morning Direction at a Time",
        "asset": "pilot-01-shoe-storyboard.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 4, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Shoes, bag, water bottle, and jacket can sound like one instruction to an adult but four separate jobs to a young child.",
            "Repeating the whole list more loudly usually adds pressure without making the first step clearer.",
            "Pause, move close, and decide which single action needs to happen now.",
            "Try: Please put on your shoes; when that is finished, give the next short direction and notice the follow-through.",
            "One age-appropriate direction at a time makes success easier to see and keeps the morning moving.",
        ],
    },
    {
        "number": 9,
        "slug": "separate-kitchen-jobs",
        "title": "Give Each Child One Clear Job",
        "asset": "kitchen-siblings-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Two children hear help with dinner, then both reach for the same bowl and the teamwork disappears.",
            "Telling everyone to just help is vague when each child is waiting to learn what their own job is.",
            "Pause and turn the shared request into one clear, age-appropriate direction for each child.",
            "Try: You stir five times; you place one napkin at each chair; then tell each child exactly what they completed well.",
            "Separate observable jobs reduce competition and make cooperation easier to notice and praise.",
        ],
    },
    {
        "number": 10,
        "slug": "listen-before-screen-limit",
        "title": "Listen Before Repeating the Screen Limit",
        "asset": "screen-time-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 4, 3, 5],
        "source": CDC_CONNECTING,
        "narration": [
            "The tablet turns off and your child says it is unfair, even though the timer and limit were clear.",
            "Repeating the rule immediately can sound like you did not hear the disappointment underneath the protest.",
            "Pause and listen for the feeling without turning the limit into a debate.",
            "Say: You wanted more time and stopping feels disappointing; the screen is still finished, and I am here while you switch activities.",
            "Reflecting the feeling communicates understanding; keeping the boundary steady shows that listening is not the same as giving in.",
        ],
    },
    {
        "number": 11,
        "slug": "prepare-bedtime-needs",
        "title": "Prepare Bedtime Needs Before Lights Out",
        "asset": "bedtime-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 4, 5],
        "source": AAP_SLEEP,
        "narration": [
            "Lights out arrives, then come the requests for water, a different blanket, and one more trip down the hallway.",
            "Solving each request after goodnight can slowly move the routine later and later.",
            "Rewind to the start of bedtime and prepare the predictable needs before the final story.",
            "Try a simple check: toilet, water, comfort item, one book, then goodnight in the same order each evening.",
            "A quiet consistent routine helps a child know what comes next while leaving room to respond when they are genuinely unwell or unsafe.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-07-to-11-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
