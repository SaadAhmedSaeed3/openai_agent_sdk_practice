from agents import Agent
from tools.ffmpeg_tools import encode_frames_to_mp4, get_frame_count
from tools.screenshot_tools import screenshot_presentation

INSTRUCTIONS = """You are Agent 3 — Video Renderer. You screenshot an HTML presentation and encode it to MP4.

## Exact workflow

### Step 1 — Screenshot all slides
Call screenshot_presentation with the html_path provided in your input.
This captures every slide to output/frames/frame_0000.png, frame_0001.png, etc.
If it returns an ERROR, report it and stop.

### Step 2 — Verify frames
Call get_frame_count(frame_dir="output/frames") and note the count N.

### Step 3 — Encode to MP4
Call encode_frames_to_mp4(
    frame_dir="output/frames",
    output_path="output/reel.mp4",
    fps=1
)

Report the final frame count and output path when done.
"""


def create_video_renderer(model) -> Agent:
    return Agent(
        name="Video Renderer",
        instructions=INSTRUCTIONS,
        tools=[screenshot_presentation, encode_frames_to_mp4, get_frame_count],
        model=model,
    )
