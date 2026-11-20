"""Build the D3 image-pixel and file-metadata attack fixtures from student-authored text.

  image      d3_fixtures/image_fixture.png     payload rendered into the PNG pixels
             (a vision model reads the text by OCR)
  metadata   d3_fixtures/metadata_fixture.png  payload stored in a PNG tEXt 'Description'
             chunk; the visible picture carries no injection text

After building, pin each fixture so the harness will accept it:
  python d3_trials.py pin text_in_images
  python d3_trials.py pin file_metadata
  python d3_fixtures/make_fixtures.py image    --payload d3_fixtures/image_payload.txt
  python d3_fixtures/make_fixtures.py metadata --payload d3_fixtures/metadata_payload.txt
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1000, 700
MARGIN = 48


def read_payload(path):
    text = Path(path).read_text(encoding="utf-8")
    if not text.strip():
        raise SystemExit(f"Payload file {path} is empty. Write your injection text there first.")
    return text


def load_font(size):
    for name in ("DejaVuSansMono.ttf", "DejaVuSans.ttf", "consola.ttf", "cour.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap(draw, text, font, max_width):
    """Wrap on whitespace, preserving the author's own line breaks."""
    lines = []
    for raw in text.splitlines() or [""]:
        if not raw.strip():
            lines.append("")
            continue
        words, line = raw.split(" "), ""
        for word in words:
            trial = f"{line} {word}".strip()
            if draw.textlength(trial, font=font) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def build_image(payload_path, visible_title, out):
    """Render the payload text into the pixels (this is the text-in-image channel)."""
    payload = read_payload(payload_path)
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    title_font, body_font = load_font(40), load_font(22)
    draw.text((MARGIN, MARGIN), visible_title, fill="black", font=title_font)
    y = MARGIN + 70
    for line in wrap(draw, payload, body_font, WIDTH - 2 * MARGIN):
        if y > HEIGHT - MARGIN:
            raise SystemExit("Payload is taller than the image. Shorten it or enlarge the canvas.")
        draw.text((MARGIN, y), line, fill="black", font=body_font)
        y += 28
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, "PNG")
    return out


def build_metadata(payload_path, visible_title, field, out):
    """Store the payload in a PNG text chunk; the visible picture stays benign."""
    payload = read_payload(payload_path)
    image = Image.new("RGB", (WIDTH, HEIGHT), (245, 245, 250))
    draw = ImageDraw.Draw(image)
    draw.rectangle((MARGIN, MARGIN, WIDTH - MARGIN, HEIGHT - MARGIN), outline=(60, 60, 90), width=3)
    draw.text((MARGIN + 24, HEIGHT // 2 - 20), visible_title, fill=(40, 40, 70), font=load_font(40))
    info = PngInfo()
    info.add_text(field, payload)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, "PNG", pnginfo=info)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    img = sub.add_parser("image", help="payload rendered into the pixels")
    img.add_argument("--payload", required=True, type=Path)
    img.add_argument("--title", default="Campus Event Flyer", help="visible heading (not the payload)")
    img.add_argument("--out", type=Path, default=HERE / "image_fixture.png")
    meta = sub.add_parser("metadata", help="payload stored in PNG metadata")
    meta.add_argument("--payload", required=True, type=Path)
    meta.add_argument("--title", default="Campus Event Flyer", help="visible text (not the payload)")
    meta.add_argument("--field", default="Description", help="PNG text chunk keyword")
    meta.add_argument("--out", type=Path, default=HERE / "metadata_fixture.png")
    args = parser.parse_args(argv)

    if args.command == "image":
        out = build_image(args.payload, args.title, args.out)
        print(f"Wrote {out} (payload in pixels). Next: python d3_trials.py pin text_in_images")
    else:
        out = build_metadata(args.payload, args.title, args.field, args.out)
        print(f"Wrote {out} (payload in '{args.field}' metadata). Next: python d3_trials.py pin file_metadata")
    return 0


if __name__ == "__main__":
    sys.exit(main())
