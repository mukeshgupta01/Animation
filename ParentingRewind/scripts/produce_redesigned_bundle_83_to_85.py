"""Create a varied Parenting Rewind bundle: episodes 83 through 85."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce


CTA = "If this helped, like and subscribe for more practical Parenting Rewind ideas."
PROMPT_RECORD = "production-assets/storyboard-prompts-83-to-85.md"

EPISODES = [
    {
        "number": 83,
        "slug": "coach-preschool-friendship-words",
        "title": "Coach the Words, Then Let Preschool Friends Try",
        "asset": "preschool-friendship-conflict-aunt-nephew-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-08-27",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "Growing Independence: Tips for Parents of Young Children",
            "url": "https://www.healthychildren.org/English/ages-stages/preschool/Pages/Growing-Independence-Tips-for-Parents-of-Young-Children.aspx",
        },
        "new_image_generation_calls": 1,
        "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Two preschoolers reach for the same chalk, voices rise, and your instinct is to decide who gets it before anyone gets more upset.",
            "Taking over every friendship problem may end this moment, but it does not let a young child practice the words they will need next time.",
            "Pause and get close. Name what you see without choosing a villain: You both wanted the same chalk, and you are feeling frustrated.",
            "Coach one short sentence your child can actually use: I was using that. Can I have it back, or can we choose a turn?",
            "Stay nearby for safety, then let the children try. Step in for hitting or grabbing, but leave room for calm words, another idea, and a repaired game.",
            CTA,
        ],
    },
    {
        "number": 84,
        "slug": "left-out-listen-before-investigating",
        "title": "When Your Child Feels Left Out, Listen Before You Investigate",
        "asset": "school-peer-exclusion-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-08-27",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "Problems With Peers: How to Help Your Child Navigate Social Challenges",
            "url": "https://www.healthychildren.org/English/ages-stages/gradeschool/school/pages/Problems-With-Peers.aspx",
        },
        "new_image_generation_calls": 1,
        "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your child comes home saying everyone left them out, and the protective part of you is already reaching for the phone.",
            "Calling another family or labeling it bullying before you understand the pattern can make your child feel that the problem has become bigger than they can handle.",
            "Pause and listen first: That sounds painful. Tell me what happened, where it happened, and whether this has happened more than once.",
            "Then ask what support would help: practicing what to say, finding another person to join, taking a break, or speaking with a trusted teacher together.",
            "One friendship conflict and repeated targeted bullying need different responses. Stay on your child's side, watch the pattern, and involve the school when exclusion persists or safety is affected.",
            CTA,
        ],
    },
    {
        "number": 85,
        "slug": "teen-overnight-phone-sleep-plan",
        "title": "Make the Overnight Phone Plan With Your Teen",
        "asset": "teen-phone-sleep-plan-mother-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-08-27",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "My teen is having trouble falling asleep at night. How can I help?",
            "url": "https://www.healthychildren.org/English/tips-tools/ask-the-pediatrician/Pages/My-teen-is-having-more-trouble-falling-asleep.aspx",
        },
        "new_image_generation_calls": 1,
        "upload_authorized": True,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "It is late, your teen is still scrolling, and a tired reminder can quickly turn into a fight about taking the phone away.",
            "The phone matters, but so does the timing of the conversation. A midnight power struggle rarely creates a plan either of you can keep.",
            "Pause and revisit it during the day. Agree on a wind-down time, with screens put away about an hour before bed and notifications kept from waking them.",
            "Choose a charging place outside the bedroom and put your own phone there too. If the phone must stay for an alarm, agree on do-not-disturb and where it rests.",
            "Treat the plan as a sleep support, not a punishment. Review what works together, and talk with your teen's doctor if sleep trouble persists or affects daytime life.",
            CTA,
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-83-to-85-ledger.json").write_text(
            json.dumps(
                {"approved": True, "upload_authorized": True, "results": results},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
