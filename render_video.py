"""
render_video.py
---------------
Opens a carousel-style HTML presentation (apple-minimal or any JS-driven template),
navigates slide-by-slide using the ArrowRight key, screenshots each slide after
animations settle, then encodes all frames into an MP4.

Usage:
    python render_video.py
    python render_video.py --html output/presentation.html --fps 1 --out output/reel.mp4
"""

import argparse
import asyncio
import subprocess
from pathlib import Path


FRAMES_DIR = Path("output/frames")
DEFAULT_HTML = Path("output/presentation.html")
DEFAULT_OUT = Path("output/reel.mp4")
DEFAULT_FPS = 1
ANIMATION_WAIT_MS = 1200   # ms to wait after each keypress for animations to finish
VIEWPORT_W = 1920
VIEWPORT_H = 1080


async def render(html_path: Path, output_path: Path, fps: int) -> None:
    from playwright.async_api import async_playwright

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    # Clear old frames
    for f in FRAMES_DIR.glob("frame_*.png"):
        f.unlink()

    file_url = html_path.resolve().as_uri()
    print(f"  Opening: {file_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--allow-file-access-from-files", "--disable-web-security"],
        )
        context = await browser.new_context(viewport={"width": VIEWPORT_W, "height": VIEWPORT_H})
        page = await context.new_page()

        await page.goto(file_url, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(500)  # initial render settle

        # Count total slides
        total = await page.evaluate("document.querySelectorAll('.slide').length")
        print(f"  Found {total} slides")

        for i in range(total):
            # Wait for entry animations to finish
            await page.wait_for_timeout(ANIMATION_WAIT_MS)

            frame_path = FRAMES_DIR / f"frame_{i:04d}.png"
            await page.screenshot(path=str(frame_path), full_page=False)
            print(f"  Saved frame {i:04d}  ({frame_path.name})", flush=True)

            # Advance to the next slide (last slide: no more keypress needed)
            if i < total - 1:
                await page.keyboard.press("ArrowRight")

        await browser.close()

    # Encode frames → MP4
    frame_pattern = str(FRAMES_DIR / "frame_%04d.png")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", frame_pattern,
        "-vf", f"scale={VIEWPORT_W}:{VIEWPORT_H}:force_original_aspect_ratio=decrease,"
               f"pad={VIEWPORT_W}:{VIEWPORT_H}:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    print(f"\n  Encoding {total} frames at {fps} fps -> {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error:\n{result.stderr[-600:]}")
    else:
        print(f"  Done -> {output_path.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render HTML presentation to MP4")
    parser.add_argument("--html", default=str(DEFAULT_HTML), help="Path to the HTML file")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help="Frames per second (default 1)")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output MP4 path")
    parser.add_argument(
        "--wait", type=int, default=ANIMATION_WAIT_MS,
        help="Milliseconds to wait per slide for animations (default 1200)",
    )
    args = parser.parse_args()

    html_path = Path(args.html)
    if not html_path.exists():
        print(f"ERROR: HTML file not found: {html_path}")
        return

    asyncio.run(render(html_path, Path(args.out), args.fps))


if __name__ == "__main__":
    main()
