import argparse
import json
import os
from pathlib import Path
from typing import Any


def format_timestamp(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000
    minutes = milliseconds // 60_000
    milliseconds %= 60_000
    secs = milliseconds // 1000
    millis = milliseconds % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def write_text_output(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_segments_output(path: Path, segments: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")


def transcribe_with_faster_whisper(
    audio_path: Path,
    model: str,
    language: str | None,
    device: str,
    compute_type: str,
) -> tuple[str, list[dict[str, Any]]]:
    from faster_whisper import WhisperModel  # type: ignore

    whisper_model = WhisperModel(model, device=device, compute_type=compute_type)
    raw_segments, _info = whisper_model.transcribe(str(audio_path), language=language)
    segments = []
    texts = []
    for segment in raw_segments:
        item = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
        }
        segments.append(item)
        texts.append(item["text"])
    return "\n".join(filter(None, texts)), segments


def transcribe_with_whisper(audio_path: Path, model: str, language: str | None) -> tuple[str, list[dict[str, Any]]]:
    import whisper  # type: ignore

    whisper_model = whisper.load_model(model)
    result = whisper_model.transcribe(str(audio_path), language=language)
    segments = [
        {
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip(),
        }
        for segment in result.get("segments", [])
    ]
    return result["text"].strip(), segments


def transcribe_with_openai(audio_path: Path, model: str, language: str | None) -> tuple[str, list[dict[str, Any]]]:
    from openai import OpenAI

    client = OpenAI()
    with audio_path.open("rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file,
            model=model,
            language=language,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    text = getattr(response, "text", "") or ""
    response_segments = getattr(response, "segments", None) or []
    segments = []
    for segment in response_segments:
        item = {
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip(),
        }
        segments.append(item)
    return text.strip(), segments


def resolve_model(provider: str, model: str | None) -> str:
    if model:
        return model
    if provider == "openai":
        return "gpt-4o-mini-transcribe"
    if provider == "faster-whisper":
        for local_model in (
            Path("artifacts/models/faster-whisper-small"),
            Path("artifacts/models/faster-whisper-base"),
            Path("artifacts/models/faster-whisper-tiny"),
        ):
            if local_model.exists():
                return str(local_model)
    return "base"


def render_timestamped_text(segments: list[dict[str, Any]]) -> str:
    lines = []
    for segment in segments:
        lines.append(
            f"[{format_timestamp(segment['start'])} - {format_timestamp(segment['end'])}] {segment['text']}"
        )
    return "\n".join(lines)


def auto_select_provider(provider: str) -> str:
    if provider != "auto":
        return provider
    try:
        import faster_whisper  # type: ignore  # noqa: F401

        return "faster-whisper"
    except ImportError:
        pass
    try:
        import whisper  # type: ignore  # noqa: F401

        return "whisper"
    except ImportError:
        pass
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    raise SystemExit(
        "No ASR backend available. Install `faster-whisper` or `openai-whisper`, or set OPENAI_API_KEY for cloud transcription."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe audio with a local Whisper backend or OpenAI audio transcription API."
    )
    parser.add_argument("audio", help="Path to audio/video file")
    parser.add_argument(
        "--provider",
        choices=["auto", "faster-whisper", "whisper", "openai"],
        default="auto",
        help="ASR backend to use",
    )
    parser.add_argument(
        "--model",
        help=(
            "Whisper model name/path. If omitted, faster-whisper uses the best local model "
            "under artifacts/models: small, then base, then tiny."
        ),
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Execution device for faster-whisper, such as cpu or cuda",
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        help="Compute type for faster-whisper, such as int8, float16, or float32",
    )
    parser.add_argument("--language", help="Language code such as zh or en")
    parser.add_argument("--txt-out", help="Output transcript text path")
    parser.add_argument("--segments-out", help="Output segments JSON path")
    parser.add_argument(
        "--timestamped-out",
        help="Output timestamped plain text path",
    )
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")

    provider = auto_select_provider(args.provider)
    model = resolve_model(provider, args.model)
    if provider == "faster-whisper":
        text, segments = transcribe_with_faster_whisper(
            audio_path,
            model,
            args.language,
            args.device,
            args.compute_type,
        )
    elif provider == "whisper":
        text, segments = transcribe_with_whisper(audio_path, model, args.language)
    else:
        text, segments = transcribe_with_openai(audio_path, model, args.language)

    txt_out = Path(args.txt_out) if args.txt_out else audio_path.with_suffix(".transcript.txt")
    segments_out = Path(args.segments_out) if args.segments_out else audio_path.with_suffix(".segments.json")
    timestamped_out = (
        Path(args.timestamped_out)
        if args.timestamped_out
        else audio_path.with_suffix(".timestamped.txt")
    )

    write_text_output(txt_out, text)
    write_segments_output(segments_out, segments)
    write_text_output(timestamped_out, render_timestamped_text(segments))

    print(
        json.dumps(
            {
                "provider": provider,
                "model": model,
                "language": args.language,
                "audio": str(audio_path),
                "txt_out": str(txt_out),
                "segments_out": str(segments_out),
                "timestamped_out": str(timestamped_out),
                "segment_count": len(segments),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
