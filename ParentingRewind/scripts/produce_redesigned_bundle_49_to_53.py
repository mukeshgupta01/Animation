"""Create redesigned local-only Parenting Rewind episodes 49 through 53."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import AAP_SLEEP, CDC_DIRECTIONS, CDC_PRAISE, WORK_ROOT, produce
from produce_redesigned_bundle_07_to_11 import CDC_CONNECTING
from produce_redesigned_bundle_12_to_16 import AAP_HOMEWORK


EPISODES = [
    {
        "number": 49,
        "slug": "homework-break-plan",
        "title": "Plan the Homework Break Before Frustration",
        "asset": "homework-mother-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [1, 0, 2, 4, 5, 3],
        "source": AAP_HOMEWORK,
        "narration": [
            "A nine-year-old may push through homework until one difficult problem turns tiredness into an argument.",
            "Offering a break only after frustration peaks can make stopping feel like an escape from every challenging question.",
            "Pause before work begins and agree on a short break point the child can predict.",
            "Try: Finish these three questions, take a five-minute movement break, then return for the last section at this table.",
            "A planned pause protects concentration and keeps the parent in a supporting role while the child does the actual work.",
        ],
    },
    {
        "number": 50,
        "slug": "playground-feeling-and-limit",
        "title": "Name the Feeling and Keep the Playground Limit",
        "asset": "playground-leaving-storyboard-01.png",
        "grid": [2, 3],
        "order": [1, 2, 0, 3, 5, 4],
        "source": CDC_CONNECTING,
        "narration": [
            "Leaving the playground can bring real disappointment for a three-year-old who is still fully involved in play.",
            "Saying there is nothing to be upset about may add a fight over the feeling to the limit that already exists.",
            "Pause, acknowledge the feeling briefly, and keep the next action clear.",
            "Try: You are sad playtime is finished; it is time to hold my hand and walk with me to the gate.",
            "Naming disappointment does not cancel the boundary; it helps the child feel understood while the adult follows through.",
        ],
    },
    {
        "number": 51,
        "slug": "checkout-calm-repeat",
        "title": "Repeat the Checkout Answer Calmly",
        "asset": "supermarket-storyboard-01.png",
        "grid": [3, 2],
        "order": [2, 1, 0, 4, 3, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "At checkout, a five-year-old may ask for the same treat again in a louder voice after hearing no.",
            "Adding a longer explanation each time can accidentally signal that enough questions might change the answer.",
            "Pause, move close, and repeat the short direction in the same steady tone.",
            "Try: The treat is staying on the shelf; place both hands on the trolley and help me watch for our turn.",
            "A consistent answer reduces extra negotiation while a concrete next action shows the child what to do now.",
        ],
    },
    {
        "number": 52,
        "slug": "bedtime-notice-cooperation",
        "title": "Notice the Bedtime Step That Worked",
        "asset": "bedtime-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [2, 0, 1, 3, 5, 4],
        "source": CDC_PRAISE,
        "narration": [
            "Bedtime can include complaints and cooperation in the same few minutes.",
            "Focusing only on the complaint may hide the moment a six-year-old actually put on pajamas or climbed into bed.",
            "Pause and name the useful action without pretending the whole evening was easy.",
            "Try: You felt upset about stopping play, and you still put on your pajamas when the timer ended.",
            "Specific praise helps the child recognize the exact bedtime skill they used and can practice again tomorrow.",
        ],
    },
    {
        "number": 53,
        "slug": "sibling-listen-separately",
        "title": "Hear Each Sibling Separately First",
        "asset": "kitchen-siblings-storyboard-01.png",
        "grid": [2, 3],
        "order": [0, 2, 1, 4, 3, 5],
        "source": CDC_CONNECTING,
        "narration": [
            "When two children explain a kitchen conflict at once, volume can replace information before either story is understood.",
            "Demanding an immediate shared solution may ask children to cooperate before they feel heard or calm enough to listen.",
            "Pause and give each child a short uninterrupted turn while the other waits nearby.",
            "Try: I will listen to your sister first, then you will have your turn; after both stories, we will choose the next safe job.",
            "Separate listening slows the conflict down and gives the family a clearer starting point for repair and cooperation.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-49-to-53-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
