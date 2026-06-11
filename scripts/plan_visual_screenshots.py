#!/usr/bin/env python3
"""Plan low-cost screenshots from timestamped subtitles or transcripts.

The script is intentionally conservative: it produces a timestamp plan first,
and only extracts frames when a local video path and --extract are provided.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


TIMESTAMP_RE = re.compile(
    r"(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})(?:[,.](?P<ms>\d{1,3}))?"
)

VISUAL_CUES = [
    "如图",
    "看这里",
    "这里",
    "这个表",
    "这张图",
    "画面",
    "屏幕",
    "左边",
    "右边",
    "上面",
    "下面",
    "列表",
    "排名",
    "排行榜",
    "参数",
    "价格",
    "地图",
    "路线",
    "界面",
    "按钮",
    "代码",
    "图表",
    "截图",
    "幻灯片",
    "PPT",
]

UNCERTAIN_CUES = [
    "疑似",
    "不确定",
    "听不清",
    "unclear",
    "unknown",
    "ASR",
]

SECTION_CUES = [
    "第一",
    "第二",
    "第三",
    "步骤",
    "总结",
    "结论",
    "接下来",
    "最后",
]


@dataclass
class Cue:
    seconds: float
    timestamp: str
    text: str
    reason: str


def parse_seconds(match: re.Match[str]) -> float:
    hours = int(match.group("h"))
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    ms = match.group("ms") or "0"
    return hours * 3600 + minutes * 60 + seconds + int(ms.ljust(3, "0")) / 1000


def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def read_cues(path: Path) -> list[Cue]:
    cues: list[Cue] = []
    last_seconds: float | None = None
    last_timestamp = ""

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = TIMESTAMP_RE.search(line)
        if match:
            last_seconds = parse_seconds(match)
            last_timestamp = format_timestamp(last_seconds)

        if last_seconds is None:
            continue

        reasons: list[str] = []
        if any(cue.lower() in line.lower() for cue in VISUAL_CUES):
            reasons.append("visual cue")
        if any(cue.lower() in line.lower() for cue in UNCERTAIN_CUES):
            reasons.append("ASR uncertainty")
        if any(cue.lower() in line.lower() for cue in SECTION_CUES):
            reasons.append("section change")

        if reasons:
            cues.append(
                Cue(
                    seconds=last_seconds,
                    timestamp=last_timestamp,
                    text=line,
                    reason=", ".join(reasons),
                )
            )

    return cues


def dedupe_by_window(cues: list[Cue], window_seconds: int) -> list[Cue]:
    selected: list[Cue] = []
    for cue in sorted(cues, key=lambda item: item.seconds):
        if selected and cue.seconds - selected[-1].seconds < window_seconds:
            if "visual cue" in cue.reason and "visual cue" not in selected[-1].reason:
                selected[-1] = cue
            continue
        selected.append(cue)
    return selected


def choose_plan(cues: list[Cue], max_frames: int) -> list[Cue]:
    if not cues:
        return [
            Cue(5, "00:00:05", "No transcript cue found; capture title/opening card.", "fallback"),
        ]

    visual = [cue for cue in cues if "visual cue" in cue.reason]
    uncertain = [cue for cue in cues if "ASR uncertainty" in cue.reason]
    section = [cue for cue in cues if "section change" in cue.reason]

    merged: list[Cue] = []
    for group in (visual, uncertain, section):
        for cue in group:
            if cue not in merged:
                merged.append(cue)

    plan = dedupe_by_window(merged, window_seconds=20)
    if plan and plan[0].seconds > 20:
        plan.insert(0, Cue(5, "00:00:05", "Opening/title card.", "opening"))
    return plan[:max_frames]


def write_markdown(plan: list[Cue], output: Path) -> None:
    lines = [
        "# Visual Screenshot Plan",
        "",
        "| # | Timestamp | Reason | Evidence cue |",
        "|---:|---|---|---|",
    ]
    for index, cue in enumerate(plan, 1):
        text = cue.text.replace("|", "\\|")
        lines.append(f"| {index} | `{cue.timestamp}` | {cue.reason} | {text} |")
    lines.extend(
        [
            "",
            "Use these frames first. Escalate to 6-12 focused frames only if they reveal dense charts, UI steps, code, maps, rankings, or uncertain names/numbers.",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_frames(video: Path, plan: list[Cue], output_dir: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg was not found on PATH; install ffmpeg or omit --extract.")

    output_dir.mkdir(parents=True, exist_ok=True)
    for index, cue in enumerate(plan, 1):
        target = output_dir / f"{index:02d}-{cue.timestamp.replace(':', '-')}.jpg"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-ss",
                cue.timestamp,
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(target),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path, help="SRT/VTT/timestamped transcript path")
    parser.add_argument("--max-frames", type=int, default=5, help="default: 5")
    parser.add_argument("--plan-out", type=Path, default=Path("artifacts/visual_screenshot_plan.md"))
    parser.add_argument("--video", type=Path, help="optional local video file for frame extraction")
    parser.add_argument("--extract", action="store_true", help="extract frames with ffmpeg")
    parser.add_argument("--frames-dir", type=Path, default=Path("artifacts/visual_frames"))
    args = parser.parse_args()

    cues = read_cues(args.transcript)
    plan = choose_plan(cues, max(1, args.max_frames))
    write_markdown(plan, args.plan_out)

    if args.extract:
        if not args.video:
            raise SystemExit("--extract requires --video")
        extract_frames(args.video, plan, args.frames_dir)

    print(f"Wrote screenshot plan: {args.plan_out}")
    for cue in plan:
        print(f"{cue.timestamp}\t{cue.reason}\t{cue.text}")


if __name__ == "__main__":
    main()
