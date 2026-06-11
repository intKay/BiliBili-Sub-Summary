import argparse
import re
from pathlib import Path


TIMESTAMP_RE = re.compile(
    r"^\s*(\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?\s*-->\s*(\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?\s*$"
)
VTT_HEADER_RE = re.compile(r"^(WEBVTT|Kind:|Language:)")
TAG_RE = re.compile(r"<[^>]+>")


def normalize_line(line: str) -> str:
    line = TAG_RE.sub("", line)
    line = line.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", line).strip()


def read_subtitle_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    raw_lines = text.splitlines()
    cleaned: list[str] = []

    for raw in raw_lines:
        line = raw.strip()
        if not line:
            cleaned.append("")
            continue
        if line.isdigit():
            continue
        if TIMESTAMP_RE.match(line):
            cleaned.append("")
            continue
        if VTT_HEADER_RE.match(line):
            continue
        if line.startswith("NOTE") or line.startswith("STYLE"):
            continue
        normalized = normalize_line(line)
        if normalized:
            cleaned.append(normalized)

    return cleaned


def collapse_lines(lines: list[str]) -> str:
    paragraphs: list[str] = []
    buffer: list[str] = []
    last_line = ""

    for line in lines:
        if not line:
            if buffer:
                paragraph = " ".join(buffer)
                if not paragraphs or paragraphs[-1] != paragraph:
                    paragraphs.append(paragraph)
                buffer = []
            continue
        if line == last_line:
            continue
        buffer.append(line)
        last_line = line

    if buffer:
        paragraph = " ".join(buffer)
        if not paragraphs or paragraphs[-1] != paragraph:
            paragraphs.append(paragraph)

    return "\n\n".join(paragraphs).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize srt/vtt subtitles into plain text.")
    parser.add_argument("input", help="Input .srt or .vtt file")
    parser.add_argument("--txt-out", help="Output text file path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Subtitle file not found: {input_path}")

    output_path = Path(args.txt_out) if args.txt_out else input_path.with_suffix(".clean.txt")
    lines = read_subtitle_lines(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(collapse_lines(lines), encoding="utf-8")
    print(f"Wrote normalized transcript: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
