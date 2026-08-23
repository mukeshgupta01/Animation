"""Create five age-diverse Parenting Rewind episodes 65 through 69."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce


AAP_COMMUNICATION = {
    "organization": "American Academy of Pediatrics / HealthyChildren.org",
    "title": "Communication Skills Start at Home",
    "url": "https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline/Pages/Components-of-Good-Communication.aspx",
}

AAP_MEDIA_PLAN = {
    "organization": "American Academy of Pediatrics / HealthyChildren.org",
    "title": "Family Media Plan",
    "url": "https://www.healthychildren.org/English/fmp/Pages/MediaPlan.aspx",
}

AAP_SEPARATION = {
    "organization": "American Academy of Pediatrics / HealthyChildren.org",
    "title": "Soothing Your Child's Separation Anxiety",
    "url": "https://www.healthychildren.org/English/ages-stages/toddler/Pages/Soothing-Your-Childs-Separation-Anxiety.aspx",
}

AAP_CAR_SEATS = {
    "organization": "American Academy of Pediatrics / HealthyChildren.org",
    "title": "Car Safety Seats: Information for Families",
    "url": "https://www.healthychildren.org/English/safety-prevention/on-the-go/Pages/Car-Safety-Seats-Information-for-Families.aspx",
}

PROMPT_RECORD = "production-assets/storyboard-prompts-65-to-69.md"
CTA = "If this helped, like and subscribe for more practical Parenting Rewind ideas."

EPISODES = [
    {
        "number": 65,
        "slug": "repair-curfew-miss",
        "title": "Repair a Curfew Miss Without a Lecture",
        "asset": "teen-curfew-father-daughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "source": AAP_COMMUNICATION,
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your sixteen-year-old comes home after curfew, and worry can turn into a lecture before she has even put down her bag.",
            "The boundary matters, but attacking her character can bury the information you need about what happened and what needs to change.",
            "Pause, settle your voice, and separate tonight's safety check from tomorrow's problem-solving conversation.",
            "Try: I was worried when you were late; tell me what happened, then we will agree on how you will contact me next time.",
            "Listening does not erase the limit; it helps you make a clear, realistic plan that respects growing independence and family safety.",
            CTA,
        ],
    },
    {
        "number": 66,
        "slug": "short-daycare-goodbye",
        "title": "Use the Same Short Daycare Goodbye",
        "asset": "daycare-separation-mother-toddler-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 5, 4],
        "source": AAP_SEPARATION,
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "At daycare drop-off, your two-year-old grips your leg, and stretching the goodbye can make both of you feel less certain.",
            "Sneaking away breaks trust, but returning for several extra hugs can accidentally restart the separation again and again.",
            "Pause, keep your face calm, and use the same brief goodbye routine your toddler can begin to recognize.",
            "Try: One hug, bunny stays with you, and I will come back after afternoon snack; then wave once and let the educator support the transition.",
            "Your toddler may still cry; predictability and a reliable return matter more than forcing an instant happy reaction.",
            CTA,
        ],
    },
    {
        "number": 67,
        "slug": "build-phone-boundary-together",
        "title": "Build the Phone Boundary Together",
        "asset": "teen-phone-boundary-mother-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": AAP_MEDIA_PLAN,
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your fourteen-year-old is scrolling beside unfinished schoolwork, and grabbing the phone can turn the whole evening into a power struggle.",
            "A boundary works better when it names the shared goal instead of treating normal teenage privacy as suspicious behaviour.",
            "Pause, ask what is pulling his attention, and choose a rule you are also willing to model consistently.",
            "Try: Let us charge phones here during focused work, then check them during the planned break; what timing feels realistic tonight?",
            "A collaborative media plan still has limits, but it gives a teenager a voice in how the family protects sleep, attention, and connection.",
            CTA,
        ],
    },
    {
        "number": 68,
        "slug": "calm-car-seat-boundary",
        "title": "Hold the Car-Seat Boundary Calmly",
        "asset": "car-seat-father-toddler-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 5, 4],
        "source": AAP_CAR_SEATS,
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "When a three-year-old refuses the car seat, time pressure can make a parent repeat the demand louder and faster.",
            "The safety limit is not optional, but a toddler can still have one small choice about how the safe step happens.",
            "Pause beside the parked car, use few words, and offer only options you can calmly follow through with.",
            "Try: You can climb into the seat, or I can help your body into the seat; the car moves after the buckle is secure.",
            "A calm choice does not negotiate away safety; it reduces extra conflict while the adult keeps the boundary clear.",
            CTA,
        ],
    },
    {
        "number": 69,
        "slug": "friendship-listening-or-ideas",
        "title": "Ask: Listening or Ideas?",
        "asset": "friendship-listening-grandfather-granddaughter-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "source": AAP_COMMUNICATION,
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your eleven-year-old shows you a painful friendship message, and your first instinct may be to tell her exactly what to send back.",
            "Fast advice can make a child stop explaining, especially when she is still working out what she feels and what she wants.",
            "Pause, listen for the full story, and ask what kind of support would be useful before offering solutions.",
            "Try: Do you want me to listen while you sort this out, or would you like a few ideas when you are ready?",
            "You do not have to solve the friendship immediately; staying curious helps your child think while knowing she is not alone.",
            CTA,
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-65-to-69-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
