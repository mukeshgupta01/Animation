"""Create a local-review-only Father's Day tribute for Parenting Rewind."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from produce_redesigned_bundle_02_to_06 import PROJECT, WORK_ROOT, produce


ASSET_DIR = PROJECT / "production-assets"
PROMPT_RECORD = "production-assets/fathers-day-dads-who-show-up-portrait-prompts.md"
CTA = "If this helped, like and subscribe for more practical Parenting Rewind ideas."
EPISODE_ID = "parenting-rewind-redesign-86-fathers-day-dads-who-show-up"
THUMBNAIL = WORK_ROOT / EPISODE_ID / "thumbnail.jpg"

PORTRAIT_ASSETS = [
    "fathers-day-quiet-love-portrait-01.png",
    "fathers-day-daily-work-portrait-01.png",
    "fathers-day-repair-portrait-01.png",
    "fathers-day-listening-child-portrait-01.png",
    "fathers-day-listening-teen-portrait-01.png",
    "fathers-day-family-hug-portrait-01.png",
]


def build_thumbnail() -> None:
    selected = [Image.open(ASSET_DIR / PORTRAIT_ASSETS[index]).convert("RGB") for index in (0, 3, 5)]
    width, height = 1280, 720
    canvas = Image.new("RGB", (width, height), (24, 18, 16))
    cell_width = (width + 2) // 3
    for index, panel in enumerate(selected):
        scale = max(cell_width / panel.width, height / panel.height)
        resized = panel.resize((round(panel.width * scale), round(panel.height * scale)), Image.Resampling.LANCZOS)
        left = max(0, (resized.width - cell_width) // 2)
        top = max(0, round((resized.height - height) * 0.36))
        canvas.paste(resized.crop((left, top, left + cell_width, top + height)), (index * cell_width, 0))
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((120, 150, width - 120, height - 125), radius=34, fill=(20, 14, 12, 190), outline=(226, 176, 94, 180), width=3)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(canvas)
    bold = Path(r"C:\Windows\Fonts\segoeuib.ttf")
    line1 = ImageFont.truetype(str(bold), 76)
    line2 = ImageFont.truetype(str(bold), 60)
    line3 = ImageFont.truetype(str(bold), 39)
    for text, font, y, color in (
        ("TO THE DADS", line1, 205, (255, 249, 235)),
        ("WHO KEEP SHOWING UP", line2, 310, (248, 204, 126)),
        ("A FATHER'S DAY TRIBUTE", line3, 425, (255, 249, 235)),
    ):
        box = draw.textbbox((0, 0), text, font=font, stroke_width=2)
        x = (width - (box[2] - box[0])) // 2
        draw.text((x, y), text, font=font, fill=color, stroke_width=2, stroke_fill=(35, 21, 15))
    THUMBNAIL.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(THUMBNAIL, quality=93, optimize=True)


SPEC = {
    "number": 86,
    "slug": "fathers-day-dads-who-show-up",
    "title": "To the Dads Who Keep Showing Up - A Father's Day Tribute",
    "asset": None,
    "panel_files": PORTRAIT_ASSETS,
    "order": [0, 1, 2, 3, 4, 5],
    "beat_labels": [
        "QUIET LOVE",
        "THE DAILY WORK",
        "NOT PERFECTION",
        "WHY IT MATTERS",
        "WE SEE YOU",
        "HAPPY FATHER'S DAY",
    ],
    "title_duration": 6.0,
    "force_rebuild": False,
    "reviewed_on": "2026-09-02",
    "source": {
        "organization": "American Academy of Pediatrics",
        "title": "Fathers' Roles in the Care and Development of Their Children: The Role of Pediatricians",
        "url": "https://publications.aap.org/pediatrics/article/138/1/e20161128/52467/Fathers-Roles-in-the-Care-and-Development-of-Their",
    },
    "new_image_generation_calls": 6,
    "recycled_visuals_approved": False,
    "generation_prompt_record": PROMPT_RECORD,
    "upload_authorized": False,
    "mirror_to_onedrive": False,
    "narration": [
        "This Father's Day is for the dads whose love does not always arrive as a speech. It arrives as a packed lunch, a school pickup, a repaired toy, and one more story when they are exhausted.",
        "It is for the dads who work, worry, wash uniforms, remember the appointment, and still wonder whether they are doing enough.",
        "The truth is, children do not need a flawless father. They need a dad who notices, responds, listens, plays, sets safe limits, and comes back to repair after getting it wrong.",
        "Research reviewed by the American Academy of Pediatrics links involved fathering across childhood with children's well-being. The ordinary moments of caring, playing, reading, guiding, and listening matter.",
        "So to every dad, stepdad, grandfather, foster dad, and father figure who keeps showing up: your presence is not background. It is part of what makes home feel safe.",
        "Today, let someone say it clearly. We see the work, the love, and the sacrifices you rarely name. Happy Father's Day, Dad.",
        CTA,
    ],
}


async def main() -> None:
    build_thumbnail()
    result = await produce(SPEC)
    metadata_path = PROJECT / "metadata" / "parenting-rewind-redesign-86-fathers-day-dads-who-show-up-v1.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["artwork"]["source_assets"] = [
        {"file": f"production-assets/{name}", "native_aspect_ratio": "9:16"}
        for name in PORTRAIT_ASSETS
    ]
    metadata["artwork"]["composite_is_new_generation"] = False
    metadata["artwork"]["portrait_native_visual_rebuild"] = True
    metadata["research"]["claim_limits"] = [
        "The tribute describes common forms of involved fathering; individual families and roles vary.",
        "Association between father involvement and child outcomes does not make any one activity a guaranteed result.",
        "Dad includes dads, stepdads, grandfathers, foster dads and other father figures in the narration.",
    ]
    metadata["youtube"] = {
        "title": "To the Dads Who Keep Showing Up | A Father's Day Tribute",
        "description": "Some dads say love with words. Others say it through packed lunches, school pickups, play, listening, safe limits, and repairing after a hard moment. This Father's Day tribute is for every dad, stepdad, grandfather, foster dad, and father figure who keeps showing up.\n\nResearch basis: American Academy of Pediatrics, Fathers' Roles in the Care and Development of Their Children.\n\n#FathersDay #Fatherhood #Parenting #Dads #ParentingRewind",
        "tags": [
            "Father's Day",
            "fatherhood",
            "dads",
            "parenting",
            "father appreciation",
            "involved father",
            "father figure",
            "Parenting Rewind"
        ],
        "thumbnail": str(THUMBNAIL.relative_to(PROJECT)),
        "privacy": "public",
        "made_for_kids": False,
        "contains_synthetic_media": True,
        "upload_authorized": False,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (WORK_ROOT / "fathers-day-dads-who-show-up-ledger.json").write_text(
        json.dumps({"approved": False, "upload_authorized": False, "result": result}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
