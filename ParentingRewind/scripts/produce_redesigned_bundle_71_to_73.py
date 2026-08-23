"""Create three age-diverse Parenting Rewind episodes 71 through 73."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce


CTA = "If this helped, like and subscribe for more practical Parenting Rewind ideas."
PROMPT_RECORD = "production-assets/storyboard-prompts-71-to-73.md"

EPISODES = [
    {
        "number": 71,
        "slug": "toilet-accident-without-shame",
        "title": "Treat Toilet Accidents as Practice, Not Misbehavior",
        "asset": "toilet-accident-aunt-niece-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-08-24",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "Toilet Training: 12 Tips to Keep the Process Positive",
            "url": "https://www.healthychildren.org/English/ages-stages/toddler/toilet-training/Pages/Praise-and-Reward-Your-Childs-Success.aspx",
        },
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your three-year-old has a toilet accident, looks embarrassed, and your surprise can sound like blame before you mean it to.",
            "Calling the mess dirty or naughty can turn a normal learning moment into shame and a bigger power struggle.",
            "Pause, soften your face, and keep your words simple: Accidents happen; we can take care of this together.",
            "Invite one manageable cleanup step, then help with clean clothes, handwashing, and the familiar bathroom routine.",
            "Stay positive and specific about progress, while asking a pediatrician about frequent or worrying accidents rather than assuming misbehavior.",
            CTA,
        ],
    },
    {
        "number": 72,
        "slug": "safer-to-tell-truth",
        "title": "Make It Safer to Tell the Truth",
        "asset": "honesty-father-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 4, 3, 5],
        "reviewed_on": "2026-08-24",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "When Children Lie: What Parents Can Do",
            "url": "https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline/Pages/When-Children-Lie.aspx",
        },
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "You find the plant on the floor, your ten-year-old denies touching it, and anger can turn the conversation into an interrogation.",
            "A harsh reaction may make avoiding your disappointment feel safer than telling you what actually happened.",
            "Pause, lower your voice, and describe the facts you can see without attacking his character.",
            "Try: The plant was upright before school, and now it is down; I want the truth so we can decide how to repair this.",
            "Keep a clear consequence for the behavior, but notice honesty when it arrives and model the same truthfulness you expect.",
            CTA,
        ],
    },
    {
        "number": 73,
        "slug": "leave-door-open-to-talk",
        "title": "Leave the Door Open When Your Teen Won't Talk",
        "asset": "teen-talk-mother-son-storyboard-01.png",
        "grid": [3, 2],
        "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-08-24",
        "source": {
            "organization": "American Academy of Pediatrics / HealthyChildren.org",
            "title": "How to Communicate With and Listen to Your Teen: 3 Key Tips",
            "url": "https://www.healthychildren.org/English/family-life/family-dynamics/communication-discipline/Pages/How-to-Communicate-with-a-Teenager.aspx",
        },
        "new_image_generation_calls": 1,
        "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Your seventeen-year-old comes home upset and says nothing, so worry can make you follow him with question after question.",
            "Pushing for an immediate explanation may turn concern into pressure and make a teenager protect even more space.",
            "Pause, turn off the parent alarm, and show that you are available without demanding a conversation on your timetable.",
            "Try: You do not have to talk right now; I am here tonight, and we can check in later unless this is about immediate safety.",
            "When he does begin, listen without catastrophizing or launching a lecture; being a steady sounding board helps keep the door open.",
            CTA,
        ],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        result = await produce(spec)
        results.append(result)
        (WORK_ROOT / "bundle-71-to-73-ledger.json").write_text(
            json.dumps({"approved": True, "upload_authorized": False, "results": results}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
