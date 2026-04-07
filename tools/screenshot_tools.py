import asyncio
from pathlib import Path

from agents import function_tool


@function_tool
def screenshot_presentation(html_path: str, output_dir: str = "output/frames") -> str:
    """
    Screenshot every slide in an HTML presentation using a local Playwright browser.
    Slides must be <section class="slide"> elements stacked vertically (1920x1080 each).
    Saves frames as output_dir/frame_0000.png, frame_0001.png, ...
    Returns the number of frames saved.
    """
    return asyncio.run(_screenshot_presentation(html_path, output_dir))


async def _screenshot_presentation(html_path: str, output_dir: str) -> str:
    from playwright.async_api import async_playwright

    frames_dir = Path(output_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Clear old frames
    for old in frames_dir.glob("frame_*.png"):
        old.unlink()

    file_url = Path(html_path).resolve().as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--allow-file-access-from-files", "--disable-web-security"]
        )
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        await page.goto(file_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(500)  # let fonts/animations settle

        # Count slides
        n = await page.evaluate(
            "document.querySelectorAll('section.slide').length || "
            "document.querySelectorAll('.slide').length"
        )

        if n == 0:
            await browser.close()
            return "ERROR: No slides found. Check that slides use class='slide'."

        for i in range(n):
            await page.evaluate(f"window.scrollTo(0, {i} * 1080)")
            await page.wait_for_timeout(150)
            frame_path = frames_dir / f"frame_{i:04d}.png"
            await page.screenshot(path=str(frame_path), clip={"x": 0, "y": i * 1080, "width": 1920, "height": 1080})

        await browser.close()

    return f"Captured {n} frames → {frames_dir.resolve()}"
