"""Create a varied Parenting Rewind bundle: episodes 80 through 82."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce


CTA = "If this helped, like and subscribe for more practical Parenting Rewind ideas."
PROMPT_RECORD = "production-assets/storyboard-prompts-80-to-82.md"

EPISODES = [
    {
        "number": 80, "slug": "preschool-greeting-without-forced-hug",
        "title": "Let Your Preschooler Choose a Greeting Without Forcing a Hug",
        "asset": "preschool-body-autonomy-greeting-father-daughter-grandmother-storyboard-01.png",
        "grid": [3, 2], "order": [0, 1, 2, 3, 4, 5], "reviewed_on": "2026-08-26",
        "source": {"organization": "American Academy of Pediatrics / HealthyChildren.org", "title": "Sexual Behaviors in Young Children: What's Normal, What's Not?", "url": "https://www.healthychildren.org/English/ages-stages/preschool/Pages/Sexual-Behaviors-Young-Children.aspx"},
        "new_image_generation_calls": 1, "upload_authorized": True, "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "Grandma arrives, your four-year-old stays close, and the familiar pressure appears: Go on, give her a hug.",
            "Guilting or pushing a child into affection teaches that politeness matters more than listening to their own body.",
            "Pause and take the pressure off: You do not have to hug. You can wave, give a thumbs-up, or choose a high-five.",
            "Let the adult accept that choice warmly, without teasing, bargaining, or acting hurt.",
            "Body autonomy does not remove manners. It teaches a child to greet people respectfully without making physical affection compulsory.", CTA],
    },
    {
        "number": 81, "slug": "after-game-listen-before-coaching",
        "title": "After the Game, Listen Before You Start Coaching",
        "asset": "soccer-father-son-storyboard-01.png", "grid": [3, 2], "order": [0, 1, 2, 5, 3, 4],
        "reviewed_on": "2026-08-26",
        "source": {"organization": "American Academy of Pediatrics", "title": "Organized Sports for Children, Preadolescents, and Adolescents", "url": "https://publications.aap.org/pediatrics/article-abstract/143/6/e20190997/37135"},
        "recycled_visuals_approved": True, "new_image_generation_calls": 0, "upload_authorized": True, "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "The game ends, and before your child reaches the car, you are already explaining every missed pass.",
            "Even useful advice can feel like pressure when a child is tired, disappointed, or still processing the game.",
            "Pause and reconnect first. Try: I liked watching you play. Do you want to talk about the game now, later, or not today?",
            "If they want to talk, ask what felt good, what felt hard, and whether they want listening or ideas.",
            "Keep their experience bigger than the score. Support, enjoyment, rest, and connection help sport remain something they choose to return to.", CTA],
    },
    {
        "number": 82, "slug": "ask-teen-before-posting-photo",
        "title": "Before You Post Your Teen's Photo, Ask Them First",
        "asset": "teen-sharenting-permission-mother-daughter-storyboard-01.png", "grid": [3, 2], "order": [0, 1, 2, 3, 4, 5],
        "reviewed_on": "2026-08-26",
        "source": {"organization": "American Academy of Pediatrics", "title": "Sharing Photos and Videos of Children on Social Media (Sharenting)", "url": "https://www.aap.org/en/patient-care/media-and-children/center-of-excellence-on-social-media-and-youth-mental-health/qa-portal/qa-portal-library/qa-portal-library-questions/sharing-photos-and-videos-of-children-on-social-media/"},
        "new_image_generation_calls": 1, "upload_authorized": True, "generation_prompt_record": PROMPT_RECORD,
        "narration": [
            "You are proud of your teen's achievement and reach for post before noticing the hesitation on their face.",
            "A photo that feels joyful to you may feel private, embarrassing, or permanent to them.",
            "Pause before sharing and ask clearly: Are you comfortable with this photo being posted, and who can see it?",
            "Treat no as a complete answer. You can keep the photo private, share it only with agreed family, crop identifying details, or not share it at all.",
            "Asking first models consent, protects trust, and gives your teen a voice in the digital footprint being created about them.", CTA],
    },
]


async def main() -> None:
    results = []
    for spec in EPISODES:
        results.append(await produce(spec))
        (WORK_ROOT / "bundle-80-to-82-ledger.json").write_text(json.dumps({"approved": True, "upload_authorized": True, "results": results}, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(results[-1]), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
