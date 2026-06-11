import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_yt_dlp_command() -> list[str]:
    try:
        import yt_dlp  # noqa: F401

        return [sys.executable, "-m", "yt_dlp"]
    except ImportError:
        pass

    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]

    raise SystemExit(
        "yt-dlp is not available. Install it with `pip install yt-dlp` or run this script from a Python environment that has `yt_dlp`."
    )


def run_command(cmd: list[str]) -> int:
    print("Running:", " ".join(cmd))
    completed = subprocess.run(cmd)
    return completed.returncode


def build_common_args(args: argparse.Namespace) -> list[str]:
    cmd = resolve_yt_dlp_command()
    if args.cookies_from_browser:
        cmd.extend(["--cookies-from-browser", args.cookies_from_browser])
    return cmd


def command_list(args: argparse.Namespace) -> int:
    cmd = build_common_args(args)
    cmd.extend(["--list-subs", args.url])
    return run_command(cmd)


def command_fetch(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / "%(title).120s [%(id)s].%(ext)s")
    cmd = build_common_args(args)
    cmd.extend(
        [
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-format",
            args.sub_format,
            "--sub-langs",
            args.sub_langs,
            "-o",
            output_template,
            args.url,
        ]
    )
    return run_command(cmd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List or fetch Bilibili subtitles using yt-dlp without persisting browser cookies."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("url", help="Bilibili video URL")
    common.add_argument(
        "--cookies-from-browser",
        help="Temporary browser profile access, e.g. chrome, edge, firefox",
    )

    list_parser = subparsers.add_parser("list", parents=[common], help="List available subtitles")
    list_parser.set_defaults(handler=command_list)

    fetch_parser = subparsers.add_parser("fetch", parents=[common], help="Download subtitles only")
    fetch_parser.add_argument("--output-dir", default="artifacts", help="Directory for subtitle files")
    fetch_parser.add_argument("--sub-format", default="srt", help="Subtitle format, e.g. srt or vtt")
    fetch_parser.add_argument("--sub-langs", default="zh.*,en.*", help="Subtitle language preference")
    fetch_parser.set_defaults(handler=command_fetch)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())

