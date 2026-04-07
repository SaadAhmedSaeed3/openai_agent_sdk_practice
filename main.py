"""
main.py
-------
3-agent pipeline: Web Researcher -> Presentation Builder -> Video Renderer.

Usage:
    python main.py --topic "The rise of AI agents"
    python main.py --topic "Quantum computing" --fps 1 --wait 2000
"""

import argparse
import asyncio
import os
import random
import re
from pathlib import Path

from dotenv import load_dotenv
from agents import OpenAIChatCompletionsModel, Runner
from openai import AsyncAzureOpenAI

from pipeline.web_researcher import create_web_researcher
from pipeline.presentation_builder import create_presentation_builder
from pipeline.video_renderer_agent import create_video_renderer_agent

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Model setup
# ---------------------------------------------------------------------------
provider = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_GPT_OPENAI_GPT4o_API_KEY"),
    azure_endpoint=os.getenv("AZURE_GPT4o_OPENAI_ENDPOINT"),
    api_version="2025-01-01-preview",
)
model = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=provider,
)

TEMPLATES_DIR = Path("presentation_creator/style-references")


def _make_topic_slug(topic: str) -> str:
    slug = topic.lower().strip()
    slug = re.sub(r"[^\w\s]", "", slug)
    slug = re.sub(r"\s+", "_", slug)
    return slug[:60]


def _pick_random_template() -> str:
    templates = [
        f for f in TEMPLATES_DIR.glob("*.html")
        if " " not in f.name  # exclude "cluely-style copy.html" etc.
    ]
    if not templates:
        raise FileNotFoundError(f"No templates found in {TEMPLATES_DIR}")
    return random.choice(templates).name


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Presentation-to-Video Generator — 3-agent pipeline"
    )
    parser.add_argument(
        "--topic", required=True,
        help='Research topic, e.g. "The rise of AI agents"',
    )
    parser.add_argument(
        "--fps", type=int, default=1,
        help="Frames per second for the output video (default: 1)",
    )
    parser.add_argument(
        "--wait", type=int, default=-1,
        help="ms to wait per slide for animations. Default: -1 (auto by template)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
async def run_pipeline(topic: str, fps: int, wait_override: int) -> None:
    Path("output").mkdir(exist_ok=True)

    topic_slug = _make_topic_slug(topic)
    template_name = _pick_random_template()
    research_filename = f"{topic_slug}.txt"

    print(f"\n{'='*62}")
    print(f"  AI Presentation-to-Video Generator")
    print(f"  Topic    : {topic}")
    print(f"  Template : {template_name}")
    print(f"  FPS      : {fps}")
    print(f"  Wait     : {'auto' if wait_override < 0 else f'{wait_override}ms'}")
    print(f"{'='*62}\n")

    # ------------------------------------------------------------------
    # Agent 1 - Web Researcher
    # ------------------------------------------------------------------
    print(">>> Agent 1 - Web Researcher")
    researcher = create_web_researcher(model)
    result1 = await Runner.run(
        researcher,
        (
            f"Research this topic and save the article:\n\n"
            f"Topic: {topic}\n"
            f"topic_slug: \"{topic_slug}\"\n\n"
            f"Run at least 4 web_search calls covering different angles, "
            f"then write a comprehensive article and call save_research_text."
        ),
        max_turns=20,
    )
    print(result1.final_output)

    # ------------------------------------------------------------------
    # Agent 2 - Presentation Builder
    # ------------------------------------------------------------------
    print("\n>>> Agent 2 - Presentation Builder")
    builder = create_presentation_builder(model)
    result2 = await Runner.run(
        builder,
        (
            f"Build the presentation HTML:\n\n"
            f"Research file : \"{research_filename}\"\n"
            f"Template      : \"{template_name}\"\n\n"
            f"Steps:\n"
            f"1. Call read_research_text(\"{research_filename}\")\n"
            f"2. Call read_template(\"{template_name}\")\n"
            f"3. Replace ONLY the text content in the template with research content.\n"
            f"   DO NOT change CSS, JS, class names, IDs, structure, or slide count.\n"
            f"4. Call save_presentation_html(content=<filled HTML>)"
        ),
        max_turns=10,
    )
    print(result2.final_output)

    # ------------------------------------------------------------------
    # Agent 3 - Video Renderer
    # ------------------------------------------------------------------
    print("\n>>> Agent 3 - Video Renderer")
    renderer = create_video_renderer_agent(model)
    result3 = await Runner.run(
        renderer,
        (
            f"Render the presentation to video.\n\n"
            f"Call render_presentation with:\n"
            f"  html_path     = \"output/presentation.html\"\n"
            f"  fps           = {fps}\n"
            f"  template_name = \"{template_name}\"\n"
            f"  wait_override = {wait_override}"
        ),
        max_turns=5,
    )
    print(result3.final_output)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'='*62}")
    print("  Pipeline complete:")
    for label, fpath in [
        ("Research  ", f"presentation_creator/refrence_txt/{research_filename}"),
        ("HTML      ", "output/presentation.html"),
        ("Video     ", "output/reel.mp4"),
    ]:
        mark = "OK     " if Path(fpath).exists() else "MISSING"
        print(f"  [{mark}]  {label}  {fpath}")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_pipeline(args.topic, args.fps, args.wait))
