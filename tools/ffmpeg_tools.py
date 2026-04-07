import base64
import json
import subprocess
from pathlib import Path

from agents import function_tool

FRAMES_DIR = Path("output/frames")
OUTPUT_DIR = Path("output")


@function_tool
def save_frame(base64_data: str, frame_index: int) -> str:
    """Decode a base64-encoded PNG screenshot and save it as output/frames/frame_NNNN.png."""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    frame_path = FRAMES_DIR / f"frame_{frame_index:04d}.png"
    image_bytes = base64.b64decode(base64_data)
    frame_path.write_bytes(image_bytes)
    return f"Saved frame {frame_index} → {frame_path.resolve()}"


@function_tool
def get_frame_count(frame_dir: str) -> int:
    """Count the number of PNG frames in the given directory."""
    return len(list(Path(frame_dir).glob("frame_*.png")))


@function_tool
def encode_frames_to_mp4(frame_dir: str, output_path: str, fps: int = 1) -> str:
    """
    Encode PNG frames into a 16:9 landscape MP4 (1920x1080).
    fps=1 means each frame lasts 1 second; fps=2 means 0.5s per frame.
    """
    frame_pattern = str(Path(frame_dir) / "frame_%04d.png")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", frame_pattern,
        "-vf", (
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black"
        ),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"FFmpeg error (code {result.returncode}):\n{result.stderr[-500:]}"
    return f"Encoded {get_frame_count(frame_dir)} frames → {output_path} at {fps} fps"


@function_tool
def check_video_info(path: str) -> str:
    """Get video metadata (duration, resolution, codec) using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"ffprobe error: {result.stderr}"
    data = json.loads(result.stdout)
    video = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"), {}
    )
    return json.dumps({
        "duration_seconds": round(float(data.get("format", {}).get("duration", 0)), 2),
        "width": video.get("width"),
        "height": video.get("height"),
        "codec": video.get("codec_name"),
        "fps": video.get("r_frame_rate"),
    }, indent=2)


@function_tool
def extract_thumbnail(video_path: str, output_path: str) -> str:
    """Extract the first frame of the video as a JPEG thumbnail."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"FFmpeg error: {result.stderr[-300:]}"
    return f"Thumbnail saved → {output_path}"
