#!/usr/bin/env python3
"""Isolate vocals from a YouTube video or local MP4 using Demucs."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ANSI = {
    "reset":  "\033[0m",
    "bold":   "\033[1m",
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "red":    "\033[91m",
    "cyan":   "\033[96m",
}

def info(msg):  print(f"{ANSI['cyan']}{ANSI['bold']}[•]{ANSI['reset']} {msg}")
def ok(msg):    print(f"{ANSI['green']}{ANSI['bold']}[✓]{ANSI['reset']} {msg}")
def error(msg): print(f"{ANSI['red']}{ANSI['bold']}[✗]{ANSI['reset']} {msg}", file=sys.stderr)


def check_dependencies():
    missing = []

    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg  →  brew install ffmpeg / apt install ffmpeg")
    if not shutil.which("yt-dlp"):
        missing.append("yt-dlp  →  pip install yt-dlp")
    try:
        import demucs  # noqa: F401
    except ImportError:
        missing.append("demucs  →  pip install demucs")

    if missing:
        error("Missing dependencies:\n")
        for m in missing:
            print(f"   {ANSI['yellow']}{m}{ANSI['reset']}")
        sys.exit(1)


def download_youtube(url: str, out_dir: str) -> str:
    info("Downloading video ...")
    cmd = [
        "yt-dlp",
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--output", os.path.join(out_dir, "source.%(ext)s"),
        "--no-playlist",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error("yt-dlp failed:\n" + result.stderr)
        sys.exit(1)

    for f in Path(out_dir).glob("source.*"):
        ok(f"Downloaded → {f.name}")
        return str(f)

    error("Download finished but no output file found.")
    sys.exit(1)


def extract_audio(video_path: str, out_wav: str):
    info("Extracting audio ...")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
        out_wav,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error("ffmpeg extraction failed:\n" + result.stderr)
        sys.exit(1)
    ok("Audio extracted.")


def run_demucs(audio_wav: str, out_dir: str, model: str) -> str:
    info(f"Running Demucs ({model}) ...")

    cmd = [sys.executable, "-m", "demucs", "--out", out_dir, "--name", model]

    # --two-stems is faster and sufficient when we only need vocals
    if model.startswith("htdemucs"):
        cmd += ["--two-stems", "vocals"]

    cmd.append(audio_wav)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error("Demucs failed:\n" + result.stderr)
        sys.exit(1)

    vocals_path = Path(out_dir) / model / Path(audio_wav).stem / "vocals.wav"
    if not vocals_path.exists():
        found = list(Path(out_dir).rglob("vocals.wav"))
        if not found:
            error("Could not locate Demucs output.")
            sys.exit(1)
        vocals_path = found[0]

    ok("Vocals isolated.")
    return str(vocals_path)


def merge_audio_video(video_path: str, vocals_wav: str, output_path: str):
    info("Merging clean audio into video ...")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", vocals_wav,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error("ffmpeg merge failed:\n" + result.stderr)
        sys.exit(1)
    ok(f"Output → {output_path}")


def is_youtube_url(s: str) -> bool:
    return any(x in s for x in ("youtube.com", "youtu.be", "yt.be"))


def main():
    parser = argparse.ArgumentParser(
        description="Remove background music from a YouTube video or MP4 file."
    )
    parser.add_argument("source", help="YouTube URL or local MP4 path")
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument(
        "--model", "-m",
        default="htdemucs",
        choices=["htdemucs", "htdemucs_ft", "mdx_extra", "mdx_extra_q"],
    )
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    check_dependencies()

    with tempfile.TemporaryDirectory(prefix="bgremove_") as tmp:
        if is_youtube_url(args.source):
            video_path = download_youtube(args.source, tmp)
            default_output = "clean_output.mp4"
        else:
            video_path = os.path.abspath(args.source)
            if not os.path.exists(video_path):
                error(f"File not found: {video_path}")
                sys.exit(1)
            default_output = f"{Path(video_path).stem}_clean.mp4"

        output_path = args.output or default_output
        audio_wav = os.path.join(tmp, "audio.wav")

        extract_audio(video_path, audio_wav)
        vocals_wav = run_demucs(audio_wav, os.path.join(tmp, "demucs"), args.model)
        merge_audio_video(video_path, vocals_wav, output_path)

        if args.keep_temp:
            shutil.copytree(tmp, "bgremove_temp", dirs_exist_ok=True)


if __name__ == "__main__":
    main()
