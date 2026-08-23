"""Create redesigned local-only Parenting Rewind episodes 27 through 31."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import CDC_DIRECTIONS, CDC_PRAISE, WORK_ROOT, produce
from produce_redesigned_bundle_07_to_11 import CDC_CONNECTING
from produce_redesigned_bundle_12_to_16 import AAP_HOMEWORK


AAP_CHORES = {
    "organization": "American Academy of Pediatrics / HealthyChildren.org",
    "title": "Age-Appropriate Chores for Children",
    "url": "https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline/Pages/Chores-and-Responsibility.aspx",
}


EPISODES = [
    {
        "number": 27,
        "slug": "one-new-chore",
        "title": "Introduce One New Chore at a Time",
        "asset": "laundry-father-two-children-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "source": AAP_CHORES,
        "narration": [
            "Sort, fold, match, carry, and put away can turn one laundry request into a long list of new skills.",
            "Expecting a child to learn every step at once can make an ordinary family chore feel overwhelming.",
            "Pause and choose one new responsibility that fits the child's age and current ability.",
            "Try: Your job today is pairing the socks; demonstrate the first pair, keep the rest visible, and praise honest effort.",
            "One clear new task gives the child a realistic chance to build competence before the routine expands.",
        ],
    },
    {
        "number": 28,
        "slug": "positive-library-direction",
        "title": "Say What to Do With the Books",
        "asset": "library-grandmother-granddaughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": CDC_DIRECTIONS,
        "narration": [
            "Do not grab every book and stop making a mess name the problem but leave the useful action unclear.",
            "In a public place, several negative instructions can add shame without helping a young child organize the next step.",
            "Pause, move close, and describe the behavior you want to see.",
            "Say: Place these two books gently on the return shelf, then hold the one book we are borrowing.",
            "A specific positive direction gives the child something observable to do and a success the caregiver can notice.",
        ],
    },
    {
        "number": 29,
        "slug": "full-attention-listening",
        "title": "Give Thirty Seconds of Full Attention",
        "asset": "screen-time-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 5, 4],
        "source": CDC_CONNECTING,
        "narration": [
            "A child starts explaining why the game mattered while the parent is already tidying the tablet and planning dinner.",
            "Half-listening can stretch the conversation because the child keeps searching for a sign that the message landed.",
            "Pause the other task briefly and turn your face and body toward the child.",
            "Reflect one sentence: You were building something important and wanted time to finish; then restate the limit calmly.",
            "A short period of full attention can communicate more connection than a much longer conversation delivered while distracted.",
        ],
    },
    {
        "number": 30,
        "slug": "child-input-homework-plan",
        "title": "Give Your Child Input on Homework Timing",
        "asset": "homework-mother-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 4, 3, 5],
        "source": AAP_HOMEWORK,
        "narration": [
            "Some children work best soon after school, while others need time to move, eat, and reset first.",
            "Choosing the schedule during an argument can make the plan feel like another punishment.",
            "Pause and discuss timing outside the homework conflict.",
            "Offer two family-compatible options: start after snack, or start after a short outdoor break; then keep the chosen routine consistent.",
            "Child input can improve ownership, while the regular time and place protect homework from becoming a new daily negotiation.",
        ],
    },
    {
        "number": 31,
        "slug": "praise-shopping-help",
        "title": "Praise the Shopping Help Specifically",
        "asset": "supermarket-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 4, 5],
        "source": CDC_PRAISE,
        "narration": [
            "A child may place fruit in the trolley, stay close, and help at checkout before making one difficult request.",
            "If the request receives all the attention, the helpful shopping behavior becomes easy to overlook.",
            "Pause and name one useful action while it is happening.",
            "Try: You carried the list and put the apples in gently; that helped us finish the shopping together.",
            "Specific praise tells the child exactly which contribution the parent appreciated and hopes to see again.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-27-to-31-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
