"""
pipeline/video_renderer_agent.py
---------------------------------
Agent 3 - Video Renderer.
Calls render_presentation to convert the HTML presentation to MP4.
"""

from agents import Agent
from tools.render_tool import render_presentation

INSTRUCTIONS = """You are Agent 3 - Video Renderer. Your only job is to render
output/presentation.html into output/reel.mp4 by calling render_presentation.

## Workflow

### Step 1 - Render
Call render_presentation with the exact values given to you in the input:
  - html_path
  - fps
  - template_name
  - wait_override

### Step 2 - Report
If SUCCESS: report the output path and the --wait value used.
If FAILED: report the error message as-is. Do not retry.
"""


def create_video_renderer_agent(model) -> Agent:
    return Agent(
        name="Video Renderer",
        instructions=INSTRUCTIONS,
        tools=[render_presentation],
        model=model,
    )
