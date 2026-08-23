"""Create five visually distinct local-review Parenting Rewind episodes 60 through 64."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import CDC_DIRECTIONS, WORK_ROOT, produce


CDC_ACTIVE_LISTENING = {
    "organization": "Centers for Disease Control and Prevention",
    "title": "Tips for Active Listening",
    "url": "https://www.cdc.gov/parenting-toddlers/communication/active-listening.html",
}

AAP_COMMUNICATION = {
    "organization": "American Academy of Pediatrics / HealthyChildren.org",
    "title": "Communication Skills Start at Home",
    "url": "https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline/Pages/Components-of-Good-Communication.aspx",
}

PROMPT_RECORD = "production-assets/storyboard-prompts-60-to-64.md"

EPISODES = [
    {
        "number": 60,
        "slug": "let-child-correct-feeling-guess",
        "title": "Let Your Child Correct Your Feeling Guess",
        "asset": "art-studio-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "source": CDC_ACTIVE_LISTENING,
        "new_image_generation_calls": 2,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your seven-year-old leaves art class unusually quiet, and you guess that she is sad about the picture she made.",
            "A feeling guess can show attention, but insisting that your label is correct can make the child defend herself instead of explaining.",
            "Pause, stay curious, and leave room for her to correct what you noticed.",
            "Try: You seem disappointed; did I get that right, or is something else going on?",
            "When she says she is frustrated because the paper tore, reflect her correction and help with the problem she actually named.",
        ],
    },
    {
        "number": 61,
        "slug": "check-what-child-heard",
        "title": "Check What Your Child Heard",
        "asset": "apartment-morning-mother-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 5, 4],
        "source": CDC_DIRECTIONS,
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "During a busy school morning, three directions at once can leave a five-year-old standing still among shoes and bags.",
            "Repeating the whole list louder does not show which part he understood or where the sequence became confusing.",
            "Pause, move close, and check one first step rather than testing his memory for everything.",
            "Try: Tell me the first thing you heard; yes, put on one shoe, then I will give you the next step.",
            "Checking understanding keeps the direction concrete and gives the child an achievable place to begin.",
        ],
    },
    {
        "number": 62,
        "slug": "i-statement-not-blame",
        "title": "Use an I-Statement Instead of Blame",
        "asset": "craft-kitchen-father-twins-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 4, 3, 5],
        "source": AAP_COMMUNICATION,
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "When two nine-year-olds pull for the same bowl, a frustrated parent may quickly say: You two always ruin helping time.",
            "That blame describes the children as the problem instead of naming the behaviour that needs to change.",
            "Pause, describe your own concern, and make the safe next action specific.",
            "Try: I feel worried when the bowl is pulled because it could fall; I need both hands off while I set the timer for turns.",
            "An I-statement can hold the limit without attacking character, then a fair plan gives both children a way back into teamwork.",
        ],
    },
    {
        "number": 63,
        "slug": "name-two-feelings",
        "title": "Name Two Feelings at the Same Time",
        "asset": "rainy-pavilion-mother-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 2, 1, 3, 4, 5],
        "source": CDC_ACTIVE_LISTENING,
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Cancelled football practice can leave a six-year-old kicking at a puddle while still watching the empty field.",
            "Calling him only angry may miss that he is also worried about the game, his team, or when practice will happen again.",
            "Pause and reflect more than one feeling when his face and actions seem mixed.",
            "Try: You look angry that practice stopped, and maybe worried about missing it too; is that close?",
            "Children can hold two feelings at once, and a tentative reflection gives them language while leaving room to explain it differently.",
        ],
    },
    {
        "number": 64,
        "slug": "stay-close-fewer-words",
        "title": "Stay Close When Words Are Too Much",
        "asset": "evening-reading-father-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": CDC_ACTIVE_LISTENING,
        "new_image_generation_calls": 2,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "An overwhelmed four-year-old may not be able to answer questions or absorb a careful explanation, even when your voice is kind.",
            "Adding more words can become another demand when his body is already showing that language is too much.",
            "Pause, stop explaining, and stay nearby with a calm face and comfortable space.",
            "You can say: I am here; we do not have to talk yet, then let quiet presence do the rest.",
            "Active listening does not always require words; when the child is ready, connection can begin with moving closer or sharing one simple book.",
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-60-to-64-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
