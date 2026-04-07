import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from agents import OpenAIChatCompletionsModel, Runner
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI

from pipeline.content_planner import create_content_planner
from pipeline.html_builder import create_html_builder
from pipeline.video_renderer import create_video_renderer
from pipeline.qa_metadata import create_qa_metadata_agent

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Model setup — Groq Cloud via OpenAI-compatible endpoint
# ---------------------------------------------------------------------------
provider = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
gemini_model = OpenAIChatCompletionsModel(
    model="arcee-ai/trinity-large-preview:free",
    openai_client=provider,
)

# Playwright MCP — portrait viewport for 9:16 screenshots
stdio_params = {
    "command": "npx.cmd",
    "args": ["@playwright/mcp", "--viewport-size", "1080,1920"],
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Reel Generator — 4-agent pipeline (OpenAI Agent SDK)"
    )
    parser.add_argument("--topic", required=True, help='Video topic, e.g. "Top 5 AI tools"')
    parser.add_argument("--brand", required=True, help='Brand name, e.g. "TechBrand"')
    parser.add_argument(
        "--tone",
        default="professional",
        choices=["professional", "energetic", "casual"],
        help="Presentation tone (default: professional)",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=30,
        help="Target reel length in seconds (default: 30)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
async def run_pipeline(topic: str, brand: str, tone: str, length: int) -> None:
    Path("output/frames").mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  AI Reel Generator")
    print(f"  Topic : {topic}")
    print(f"  Brand : {brand}")
    print(f"  Tone  : {tone}")
    print(f"  Length: {length}s")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # Agent 1 — Content Planner
    # ------------------------------------------------------------------
    print(">>> Agent 1 — Content Planner")
    planner = create_content_planner(gemini_model)
    result1 = await Runner.run(
        planner,
        (
            f"Create a slide outline for a {length}-second short-form video reel.\n"
            f"Topic: {topic}\n"
            f"Brand: {brand}\n"
            f"Tone: {tone}\n"
            f"Target length: {length} seconds\n\n"
            "When done, save the markdown with save_slides_markdown."
        ),
    )
    print(result1.final_output)

    # ------------------------------------------------------------------
    # Agent 2 — HTML Builder
    # ------------------------------------------------------------------
    print("\n>>> Agent 2 — HTML Builder")
    builder = create_html_builder(gemini_model)
    result2 = await Runner.run(
        builder,
        (
            f"Build a self-contained HTML presentation from the saved slides.\n"
            f"Brand: {brand}  |  Tone: {tone}\n\n"
            "Steps: read slides → list templates → pick best match → read template → "
            "build HTML → save_presentation_html."
        ),
    )
    print(result2.final_output)

    # ------------------------------------------------------------------
    # Agent 3 — Video Renderer  (needs Playwright MCP)
    # ------------------------------------------------------------------
    print("\n>>> Agent 3 — Video Renderer")
    html_path = Path("output/presentation.html").resolve()
    file_url = html_path.as_uri()

    async with MCPServerStdio(
        name="Playwright",
        params=stdio_params,
        client_session_timeout_seconds=120.0,
    ) as playwright_server:
        renderer = create_video_renderer(gemini_model, playwright_server)
        result3 = await Runner.run(
            renderer,
            (
                f"Render the presentation to a video reel.\n"
                f"Presentation URL: {file_url}\n"
                f"Save frames to: output/frames/\n"
                f"Output MP4: output/reel.mp4\n"
                f"Target length: {length}s → use fps=1 (each slide = 1 second)\n\n"
                "Follow the workflow in your instructions exactly."
            ),
            max_turns=60,
        )
        print(result3.final_output)

    # ------------------------------------------------------------------
    # Agent 4 — QA + Metadata
    # ------------------------------------------------------------------
    print("\n>>> Agent 4 — QA + Metadata")
    qa_agent = create_qa_metadata_agent(gemini_model)
    result4 = await Runner.run(
        qa_agent,
        (
            f"QA the reel and produce social media metadata.\n"
            f"Topic: {topic}\n"
            f"Brand: {brand}\n"
            f"Tone: {tone}\n"
            f"Target length: {length} seconds\n"
            f"Video: output/reel.mp4"
        ),
    )
    print(result4.final_output)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("  Pipeline complete — output files:")
    for label, fpath in [
        ("Slide outline ", "output/slides.md"),
        ("Presentation  ", "output/presentation.html"),
        ("Reel          ", "output/reel.mp4"),
        ("Thumbnail     ", "output/thumbnail.jpg"),
        ("Caption       ", "output/caption.txt"),
    ]:
        mark = "✓" if Path(fpath).exists() else "✗"
        print(f"  {mark}  {label}  {fpath}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_pipeline(args.topic, args.brand, args.tone, args.length))
