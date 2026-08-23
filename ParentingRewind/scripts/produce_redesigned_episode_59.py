"""Create redesigned local-only Parenting Rewind episode 59."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce


AAP_COMMUNICATION = {
    "organization": "American Academy of Pediatrics / HealthyChildren.org",
    "title": "Communication Skills Start at Home",
    "url": "https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline/Pages/Components-of-Good-Communication.aspx",
}

EPISODE = {
    "number": 59,
    "slug": "repair-after-yelling",
    "title": "Repair After You Lose Your Temper",
    "asset": "pilot-01-shoe-storyboard.png",
    "grid": [3, 2],
    "order": [1, 2, 0, 3, 5, 4],
    "source": AAP_COMMUNICATION,
    "recycled_visuals_approved": True,
    "narration": [
        "Sometimes the direction was reasonable, but your voice became much louder than you wanted.",
        "Acting as if nothing happened can leave a child unsure, while blaming the child for your yelling shifts responsibility away from the adult choice.",
        "Pause until both of you are calmer, then return and name your action without adding an excuse.",
        "Try: I am sorry I yelled; feeling frustrated is okay, but yelling at you was not. The shoe direction still matters, and I want to try again calmly.",
        "A clear apology models responsibility without erasing the boundary; repair means owning the response and reconnecting before trying again.",
    ],
}


async def main() -> None:
    result = await produce(EPISODE)
    ledger = WORK_ROOT / "episode-59-ledger.json"
    ledger.write_text(
        json.dumps({"approved": True, "upload_authorized": False, "results": [result]}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
