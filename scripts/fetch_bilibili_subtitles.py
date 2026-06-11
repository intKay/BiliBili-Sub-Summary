import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0"
REFERER = "https://www.bilibili.com/"


def http_get_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Referer": REFERER})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_bvid(value: str) -> str:
    direct_match = re.fullmatch(r"BV[0-9A-Za-z]{10}", value)
    if direct_match:
        return direct_match.group(0)
    parsed = urlparse(value)
    match = re.search(r"/video/(BV[0-9A-Za-z]{10})", parsed.path)
    if not match:
        raise SystemExit(f"Could not find BVID in input: {value}")
    return match.group(1)


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


@dataclass
class VideoPage:
    aid: int
    cid: int
    page: int
    part: str


@dataclass
class VideoMeta:
    aid: int
    bvid: str
    title: str
    cid: int
    pages: list[VideoPage]


@dataclass
class SubtitleTrack:
    id: int
    id_str: str
    lan: str
    lan_doc: str
    subtitle_url: str
    ai_status: int


def get_video_meta(bvid: str) -> VideoMeta:
    payload = http_get_json(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}")
    if payload.get("code") != 0:
        raise SystemExit(f"Video metadata API failed: {payload.get('message')}")
    data = payload["data"]
    pages = [
        VideoPage(
            aid=data["aid"],
            cid=page["cid"],
            page=page["page"],
            part=page["part"],
        )
        for page in data.get("pages", [])
    ]
    return VideoMeta(
        aid=data["aid"],
        bvid=data["bvid"],
        title=data["title"],
        cid=data["cid"],
        pages=pages,
    )


def get_subtitle_list(aid: int, cid: int) -> list[SubtitleTrack]:
    payload = http_get_json(f"https://api.bilibili.com/x/player/wbi/v2?aid={aid}&cid={cid}")
    if payload.get("code") != 0:
        raise SystemExit(f"Subtitle API failed: {payload.get('message')}")
    subtitles = (((payload.get("data") or {}).get("subtitle") or {}).get("subtitles") or [])
    return [
        SubtitleTrack(
            id=item["id"],
            id_str=item["id_str"],
            lan=item["lan"],
            lan_doc=item["lan_doc"],
            subtitle_url=item["subtitle_url"],
            ai_status=item.get("ai_status", 0),
        )
        for item in subtitles
    ]


def resolve_page(meta: VideoMeta, page: int | None) -> VideoPage:
    if not meta.pages:
        return VideoPage(aid=meta.aid, cid=meta.cid, page=1, part=meta.title)
    if page is None:
        return meta.pages[0]
    for item in meta.pages:
        if item.page == page:
            return item
    raise SystemExit(f"Page p={page} not found for {meta.bvid}")


def parse_hex_color(hex_color: str) -> tuple[str, str, str]:
    value = hex_color[1:] if hex_color.startswith("#") else hex_color
    return value[0:2], value[2:4], value[4:6]


def convert_hex_color_for_style(hex_color: str, opacity: float = 1.0) -> str:
    red, green, blue = parse_hex_color(hex_color)
    alpha = hex(round(255 * (1 - opacity)))[2:].rjust(2, "0")
    return f"&H{alpha}{blue}{green}{red}".upper()


def seconds_to_ass_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remain = seconds % 60
    integer, _, decimal = f"{remain:.2f}".partition(".")
    return f"{hours}:{str(minutes).rjust(2, '0')}:{integer.rjust(2, '0')}.{decimal[:2].ljust(2, '0')}"


def normalize_ass_content(content: str) -> str:
    replacements = {
        "{": "｛",
        "}": "｝",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'",
        "\n": r"\N",
    }
    normalized = content
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


def subtitle_items_to_ass(items: list[dict[str, Any]], title: str, width: int = 1920, height: int = 1080) -> str:
    color = convert_hex_color_for_style("#ffffff")
    background = convert_hex_color_for_style("#000000", 0.5)
    font_size = (48 * height) / 720
    style = (
        "Style: BottomCenter,微软雅黑,"
        f"{font_size},{color},{color},{background},{background},0,0,0,0,100,100,0,0,3,1,0,2,32,32,32,0"
    )
    header = f"""
[Script Info]
; Script generated from Bilibili Evolved subtitle logic
; https://github.com/the1812/Bilibili-Evolved/
Title: {title}
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
Timer: 10.0000
WrapStyle: 0
ScaledBorderAndShadow: no

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".strip()
    lines = []
    for item in items:
        start = seconds_to_ass_time(item["from"])
        end = seconds_to_ass_time(item["to"])
        content = normalize_ass_content(item["content"])
        lines.append(f"Dialogue: 0,{start},{end},BottomCenter,,0,0,0,,{content}")
    return header + "\n" + "\n".join(lines)


def pick_subtitle(subtitles: list[SubtitleTrack], language: str | None) -> SubtitleTrack:
    if not subtitles:
        raise SystemExit("No subtitles available for this page.")
    if language:
        exact = next((item for item in subtitles if item.lan == language), None)
        if exact:
            return exact
        prefix = next((item for item in subtitles if item.lan.startswith(language)), None)
        if prefix:
            return prefix
        raise SystemExit(f"Subtitle language not found: {language}")
    return subtitles[0]


def command_list(args: argparse.Namespace) -> int:
    bvid = extract_bvid(args.input)
    meta = get_video_meta(bvid)
    page = resolve_page(meta, args.page)
    subtitles = get_subtitle_list(meta.aid, page.cid)
    print(json.dumps(
        {
            "bvid": meta.bvid,
            "title": meta.title,
            "page": page.page,
            "cid": page.cid,
            "subtitle_count": len(subtitles),
            "subtitles": [item.__dict__ for item in subtitles],
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


def command_fetch(args: argparse.Namespace) -> int:
    bvid = extract_bvid(args.input)
    meta = get_video_meta(bvid)
    page = resolve_page(meta, args.page)
    subtitles = get_subtitle_list(meta.aid, page.cid)
    subtitle = pick_subtitle(subtitles, args.language)
    subtitle_json = http_get_json(subtitle.subtitle_url)
    items = subtitle_json["body"]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    page_suffix = f".p{page.page}" if len(meta.pages) > 1 else ""
    base_name = sanitize_filename(f"{meta.title}{page_suffix}.{subtitle.lan}")
    if args.format == "ass":
        content = subtitle_items_to_ass(items, f"{meta.title}{page_suffix}")
        output_path = output_dir / f"{base_name}.ass"
        output_path.write_text(content, encoding="utf-8")
    else:
        output_path = output_dir / f"{base_name}.json"
        output_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(
        {
            "bvid": meta.bvid,
            "title": meta.title,
            "page": page.page,
            "cid": page.cid,
            "language": subtitle.lan,
            "language_display": subtitle.lan_doc,
            "format": args.format,
            "output": str(output_path),
            "line_count": len(items),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Bilibili subtitles using the same metadata flow used by Bilibili Evolved."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("input", help="Bilibili URL or BV id")
    common.add_argument("--page", type=int, help="Page number for multi-part videos")

    list_parser = subparsers.add_parser("list", parents=[common], help="List subtitles for a video")
    list_parser.set_defaults(handler=command_list)

    fetch_parser = subparsers.add_parser("fetch", parents=[common], help="Download subtitle JSON or ASS")
    fetch_parser.add_argument("--language", help="Subtitle language, e.g. zh-CN or ai-zh")
    fetch_parser.add_argument("--format", choices=["json", "ass"], default="json")
    fetch_parser.add_argument("--output-dir", default="artifacts")
    fetch_parser.set_defaults(handler=command_fetch)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())

