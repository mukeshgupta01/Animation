"""Generate truthful custom thumbnails from archived Tiny Tales video frames."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "thumbnail-manifest.json"
OUTPUT = HERE / "thumbnails"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_ratio = size[0] / size[1]
    ratio = image.width / image.height
    if ratio > target_ratio:
        width = round(image.height * target_ratio)
        left = (image.width - width) // 2
        image = image.crop((left, 0, left + width, image.height))
    else:
        height = round(image.width / target_ratio)
        top = (image.height - height) // 2
        image = image.crop((0, top, image.width, top + height))
    return image.resize(size, Image.Resampling.LANCZOS)


def extract(source: Path, timestamp: float, target: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-ss", f"{timestamp:.3f}", "-i", str(source),
        "-frames:v", "1", "-vf", "scale=1600:-2", "-q:v", "2", str(target),
    ], check=True)


def wrapped(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def make_thumbnail(item: dict[str, object]) -> Path:
    source = HERE / str(item["source"])
    if not source.is_file():
        raise FileNotFoundError(source)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    raw = OUTPUT / f".{item['video_id']}-frame.jpg"
    extract(source, float(item["timestamp"]), raw)
    frame = fit(Image.open(raw).convert("RGB"), (1280, 720))
    raw.unlink()
    background = ImageEnhance.Brightness(frame.filter(ImageFilter.GaussianBlur(18))).enhance(0.7)
    canvas = background.convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    side = str(item["text_side"])
    panel = (35, 42, 585, 678) if side == "left" else (695, 42, 1245, 678)
    image_box = (545, 70, 1245, 650) if side == "left" else (35, 70, 735, 650)
    draw.rounded_rectangle((image_box[0] + 14, image_box[1] + 16, image_box[2] + 14, image_box[3] + 16), 44, fill=(0, 0, 0, 100))
    inset = fit(frame, (image_box[2] - image_box[0], image_box[3] - image_box[1]))
    mask = Image.new("L", inset.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, inset.width - 1, inset.height - 1), 40, fill=255)
    canvas.paste(inset, image_box[:2], mask)
    draw.rounded_rectangle(image_box, 40, outline=(255, 255, 255, 235), width=7)
    accent = tuple(int(str(item["accent"])[i:i + 2], 16) for i in (1, 3, 5))
    draw.rounded_rectangle(panel, 44, fill=(*accent, 242), outline=(255, 255, 255, 235), width=6)
    badge_x = panel[0] + 40
    draw.rounded_rectangle((badge_x, 90, badge_x + 205, 144), 25, fill=(255, 255, 255, 238))
    badge_font = ImageFont.truetype(FONT_BOLD, 25)
    draw.text((badge_x + 23, 103), "TINY TALES", font=badge_font, fill=accent)
    headline_font = ImageFont.truetype(FONT_BOLD, 58)
    lines = wrapped(draw, str(item["headline"]), headline_font, panel[2] - panel[0] - 80)
    line_height = 69
    text_y = 210
    for line in lines[:3]:
        draw.text((panel[0] + 40, text_y), line, font=headline_font, fill="white", stroke_width=2, stroke_fill=(35, 35, 45))
        text_y += line_height
    sub_font = ImageFont.truetype(FONT_BOLD, 31)
    draw.rounded_rectangle((panel[0] + 38, 545, panel[2] - 38, 615), 26, fill=(20, 29, 44, 220))
    sub = str(item["subheadline"])
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    sub_x = panel[0] + (panel[2] - panel[0] - (bbox[2] - bbox[0])) // 2
    draw.text((sub_x, 562), sub, font=sub_font, fill=(255, 247, 191))
    for offset, radius in ((0, 16), (44, 11), (78, 8)):
        x = panel[2] - 125 + offset
        y = 174 + (offset % 3) * 12
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 255, 255, 180))
    target = OUTPUT / f"{item['video_id']}.jpg"
    canvas.convert("RGB").save(target, quality=91, optimize=True, progressive=True)
    if target.stat().st_size > 2_000_000:
        raise RuntimeError(f"Thumbnail exceeds YouTube 2 MB limit: {target}")
    return target


def main() -> None:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if doc.get("version") != 1 or doc.get("channel_id") != "UCEn9N-ITQHshjgt6fy7fxnw":
        raise RuntimeError("Invalid Tiny Tales thumbnail manifest")
    paths = [make_thumbnail(item) for item in doc["items"]]
    review = Image.new("RGB", (1920, 1440), (20, 25, 34))
    for index, path in enumerate(paths):
        thumb = Image.open(path).convert("RGB").resize((640, 360), Image.Resampling.LANCZOS)
        review.paste(thumb, ((index % 3) * 640, (index // 3) * 360))
    review_path = HERE / "runtime" / "thumbnail-review-contact-sheet.jpg"
    review.save(review_path, quality=92)
    print(json.dumps({"generated": len(paths), "files": [str(path) for path in paths], "review": str(review_path)}, indent=2))


if __name__ == "__main__":
    main()
