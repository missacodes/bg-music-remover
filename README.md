# bg-music-remover

Strips background music from YouTube videos or local MP4 files, keeping only the vocal/speech track. Uses [Demucs](https://github.com/facebookresearch/demucs) (Meta Research) for source separation — no synthesis, no AI voice replacement.

## Requirements

- Python 3.11+
- ffmpeg
- yt-dlp
- demucs
- torchcodec

```bash
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Linux

pip install -r requirements.txt
pip install torchcodec
```

## Usage

```bash
# YouTube URL
python remove_bg_music.py "https://www.youtube.com/watch?v=..."

# Local file
python remove_bg_music.py video.mp4

# Custom output path
python remove_bg_music.py video.mp4 -o result.mp4

# Higher quality model
python remove_bg_music.py video.mp4 -m htdemucs_ft
```
## Output

Processed videos are saved to a `videos/` folder, named after the original video's title (e.g. `videos/My_Video_Title_clean.mp4`).
## Models

| Model         | Quality | Speed  |
|---------------|---------|--------|
| htdemucs      | ★★★★   | fast   |
| htdemucs_ft   | ★★★★★  | medium |
| mdx_extra     | ★★★★   | medium |
| mdx_extra_q   | ★★★    | fast   |

`htdemucs` is the default and works well for most cases.

## Notes

- Only the vocal stem is kept — ambient sound, footsteps, and room noise are also removed
- Processing time is roughly 1–3× the video duration on CPU
- The video stream is copied without re-encoding

## Legal
This tool is intended for use with content you own or have the right to process.
Downloading copyrighted YouTube videos without permission may violate YouTube's
Terms of Service and applicable copyright law.

## License

MIT
