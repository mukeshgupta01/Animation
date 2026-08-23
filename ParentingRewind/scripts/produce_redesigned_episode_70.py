"""Create Parenting Rewind episode 70 about responding to a disappointing grade."""

from __future__ import annotations

import asyncio
import json

from produce_redesigned_bundle_02_to_06 import WORK_ROOT, produce


CTA = "If this helped, like and subscribe for more practical Parenting Rewind ideas."

EPISODE = {
    "number": 70,
    "slug": "grade-process-not-worth",
    "title": "Talk About the Process, Not Their Worth",
    "asset": "teen-grade-mother-daughter-storyboard-01.png",
    "grid": [3, 2],
    "order": [0, 1, 2, 3, 4, 5],
    "source": {
        "organization": "American Academy of Pediatrics / HealthyChildren.org",
        "title": "Perfectionism: How to Help Your Child Avoid the Pitfalls",
        "url": "https://www.healthychildren.org/English/ages-stages/young-adult/Pages/What-Fuels-Perfectionism.aspx",
    },
    "new_image_generation_calls": 1,
    "generation_prompt_record": "production-assets/storyboard-prompt-70.md",
    "narration": [
        "Your fifteen-year-old shows you a grade far below what she expected, and your alarm can sound like judgment before you hear the story.",
        "If the first message is, this is not good enough, the grade can start feeling like a verdict on her worth instead of information about learning.",
        "Pause. Turn off the parent alarm and begin with curiosity: You look disappointed; tell me what felt hardest.",
        "Then ask about the process: Did the study plan fit this test, and what one support would help next time?",
        "High expectations can focus on effort, learning, and realistic next steps without pretending the result does not matter.",
        CTA,
    ],
}


async def main() -> None:
    result = await produce(EPISODE)
    (WORK_ROOT / "episode-70-ledger.json").write_text(
        json.dumps({"approved": True, "upload_authorized": False, "result": result}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
