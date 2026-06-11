import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36"
)
REFERER = "https://www.bilibili.com/"


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


def http_get_json(url: str, referer: str = REFERER) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": referer,
            "Accept": "application/json, text/plain, */*",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(urls: list[str], output_path: Path, referer: str) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for url in urls:
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Referer": referer,
                    "Accept": "*/*",
                    "Origin": "https://www.bilibili.com",
                },
            )
            with urlopen(request, timeout=60) as response, output_path.open("wb") as file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    file.write(chunk)
            return url
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if output_path.exists():
                output_path.unlink()
    raise SystemExit(f"Audio download failed for all mirrors: {last_error}")


@dataclass
class VideoPage:
    cid: int
    page: int
    part: str
    duration: int


@dataclass
class VideoMeta:
    aid: int
    bvid: str
    title: str
    cid: int
    pages: list[VideoPage]


@dataclass
class AudioStream:
    id: int
    bandwidth: int
    codecs: str
    urls: list[str]


def get_video_meta(bvid: str) -> VideoMeta:
    payload = http_get_json(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}")
    if payload.get("code") != 0:
        raise SystemExit(f"Video metadata API failed: {payload.get('message')}")
    data = payload["data"]
    return VideoMeta(
        aid=data["aid"],
        bvid=data["bvid"],
        title=data["title"],
        cid=data["cid"],
        pages=[
            VideoPage(
                cid=page["cid"],
                page=page["page"],
                part=page["part"],
                duration=int(page.get("duration") or 0),
            )
            for page in data.get("pages", [])
        ],
    )


def resolve_page(meta: VideoMeta, page: int | None) -> VideoPage:
    if not meta.pages:
        return VideoPage(cid=meta.cid, page=1, part=meta.title, duration=0)
    if page is None:
        return meta.pages[0]
    for item in meta.pages:
        if item.page == page:
            return item
    raise SystemExit(f"Page p={page} not found for {meta.bvid}")


def get_audio_streams(meta: VideoMeta, page: VideoPage) -> list[AudioStream]:
    params = {
        "avid": meta.aid,
        "cid": page.cid,
        "qn": "",
        "otype": "json",
        "fourk": 1,
        "fnver": 0,
        "fnval": 4048,
    }
    url = f"https://api.bilibili.com/x/player/playurl?{urlencode(params)}"
    payload = http_get_json(url, referer=f"https://www.bilibili.com/video/{meta.bvid}/")
    if payload.get("code") != 0:
        raise SystemExit(f"Playurl API failed: {payload.get('message')}")
    audio_items = (((payload.get("data") or {}).get("dash") or {}).get("audio") or [])
    streams = []
    for item in audio_items:
        primary = item.get("baseUrl") or item.get("base_url")
        backups = item.get("backupUrl") or item.get("backup_url") or []
        urls = [url for url in [primary, *backups] if url]
        if urls:
            streams.append(
                AudioStream(
                    id=int(item.get("id") or 0),
                    bandwidth=int(item.get("bandwidth") or 0),
                    codecs=item.get("codecs") or "",
                    urls=urls,
                )
            )
    return sorted(streams, key=lambda stream: stream.bandwidth, reverse=True)


def command_list(args: argparse.Namespace) -> int:
    bvid = extract_bvid(args.input)
    meta = get_video_meta(bvid)
    page = resolve_page(meta, args.page)
    streams = get_audio_streams(meta, page)
    print(
        json.dumps(
            {
                "bvid": meta.bvid,
                "title": meta.title,
                "aid": meta.aid,
                "page": page.page,
                "part": page.part,
                "duration": page.duration,
                "cid": page.cid,
                "page_count": len(meta.pages) or 1,
                "audio_count": len(streams),
                "audio": [
                    {
                        "id": stream.id,
                        "bandwidth": stream.bandwidth,
                        "codecs": stream.codecs,
                        "mirror_count": len(stream.urls),
                    }
                    for stream in streams
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_fetch(args: argparse.Namespace) -> int:
    bvid = extract_bvid(args.input)
    meta = get_video_meta(bvid)
    page = resolve_page(meta, args.page)
    streams = get_audio_streams(meta, page)
    if not streams:
        raise SystemExit("No DASH audio streams available.")

    stream = streams[args.stream_index]
    page_suffix = f".p{page.page}" if len(meta.pages) > 1 else ""
    base_name = sanitize_filename(f"{meta.title}{page_suffix} [{meta.bvid}]")
    output_dir = Path(args.output_dir)
    output_path = output_dir / f"{base_name}.m4a"
    used_url = download_file(stream.urls, output_path, referer=f"https://www.bilibili.com/video/{meta.bvid}/")

    print(
        json.dumps(
            {
                "bvid": meta.bvid,
                "title": meta.title,
                "aid": meta.aid,
                "page": page.page,
                "part": page.part,
                "duration": page.duration,
                "cid": page.cid,
                "stream_id": stream.id,
                "bandwidth": stream.bandwidth,
                "codecs": stream.codecs,
                "output": str(output_path),
                "bytes": output_path.stat().st_size,
                "source_host": urlparse(used_url).netloc,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download Bilibili DASH audio without saving cookies.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("input", help="Bilibili URL or BV id")
    common.add_argument("--page", type=int, help="Page number for multi-part videos")

    list_parser = subparsers.add_parser("list", parents=[common], help="List available audio streams")
    list_parser.set_defaults(handler=command_list)

    fetch_parser = subparsers.add_parser("fetch", parents=[common], help="Download the selected audio stream")
    fetch_parser.add_argument("--output-dir", default="artifacts/audio", help="Directory for audio files")
    fetch_parser.add_argument("--stream-index", type=int, default=0, help="Index from the bandwidth-sorted audio list")
    fetch_parser.set_defaults(handler=command_fetch)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
