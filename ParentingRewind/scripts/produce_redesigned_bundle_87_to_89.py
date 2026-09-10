"""Create a varied Parenting Rewind bundle: episodes 87 through 89."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce


CTA = "If this helped, like and subscribe for more practical Parenting Rewind ideas."
PROMPT_RECORD = "production-assets/storyboard-prompts-87-to-89.md"

EPISODES = [
    {
        "number": 87,
        "slug": "prepare-preschooler-new-baby-honestly",
        "title": "Prepare Your Preschooler for a New Baby Honestly",
        "asset": "new-baby-preschool-family-storyboard-01.png",
        "grid": [3, 2], "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-09-08",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "Preparing Your Older Child for a New Baby: How to Help Siblings Adjust",
            "url": "https://www.healthychildren.org/English/ages-stages/prenatal/Pages/Preparing-Your-Family-for-a-New-Baby.aspx",
        },
        "new_image_generation_calls": 1, "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "A new baby is coming, and it is tempting to promise your preschooler an instant best friend and nothing but excitement.",
            "But preschoolers can struggle with changed routines and shared attention. Honest preparation is kinder than asking them to feel happy all the time.",
            "Pause and explain what will really change: babies cry, need a lot of care, and may not be ready to play for quite a while.",
            "Invite one small choice, like picking a blanket, without making your child responsible for the baby. Reassure them that your love is not being divided.",
            "After the baby arrives, protect regular one-on-one time and make room for mixed feelings. Connection grows through ordinary moments, not a perfect first reaction.",
            CTA,
        ],
    },
    {
        "number": 88,
        "slug": "separation-not-childs-fault",
        "title": "Tell Your Child the Separation Is Not Their Fault",
        "asset": "separation-reassurance-family-storyboard-01.png",
        "grid": [3, 2], "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-09-08",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "Divorce and Separation: How to Help Your Child Adjust",
            "url": "https://www.healthychildren.org/English/family-life/family-dynamics/types-of-families/Pages/adjusting-to-divorce.aspx",
        },
        "new_image_generation_calls": 1, "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "When parents separate, a school-age child may quietly wonder whether something they did caused the family to change.",
            "Adult details, blame, or asking a child to carry messages can make that uncertainty heavier, even when you never intended to put them in the middle.",
            "Pause and give the clearest reassurance: This is an adult decision. It is not your fault, and it is not your job to fix it.",
            "Explain what will happen next in simple, concrete terms. Keep routines as steady as possible and invite questions more than once.",
            "When both parents are safe and able to care for the child, support their relationship with each parent. If conflict or distress is hard to manage, seek qualified family support.",
            CTA,
        ],
    },
    {
        "number": 89,
        "slug": "turn-off-parent-alarm-teen-opens-up",
        "title": "Turn Off the Parent Alarm When Your Teen Opens Up",
        "asset": "teen-parent-alarm-father-daughter-storyboard-01.png",
        "grid": [3, 2], "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-09-08",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "How to Communicate With and Listen to Your Teen: 3 Key Tips",
            "url": "https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline/Pages/How-to-Communicate-with-a-Teenager.aspx",
        },
        "new_image_generation_calls": 1, "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your teen starts telling you about a friendship or relationship problem, and your parent alarm is ready with warnings before the story is finished.",
            "Interrupting, catastrophizing, or condemning the other person can make your teen defend the situation or decide not to come back next time.",
            "Pause your first reaction. Put down what you are doing, soften your face, and listen for the whole story without turning it into an interrogation.",
            "Try one calm question: Do you want me to listen, help you think it through, or share what I am worried about?",
            "Your values still matter. Share them briefly and concretely after your teen feels heard, and respond urgently whenever there is an immediate safety concern.",
            CTA,
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-87-to-89-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": True, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
