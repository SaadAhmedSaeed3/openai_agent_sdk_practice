"""
tools/render_tool.py
--------------------
Wraps render_video.py as a @function_tool subprocess call.
Auto-determines --wait based on template animation complexity.
"""

import subprocess
import sys
from pathlib import Path

from agents import function_tool

TEMPLATES_DIR = Path("presentation_creator/style-references")

_COMPLEX_KEYWORDS = frozenset([
    "particle", "glitch", "pulse", "float", "glow", "shimmer",
    "blur", "wave", "morph", "typewriter", "stagger", "flicker",
])


def _compute_wait_ms(template_name: str) -> int:
    """Read template file and compute appropriate --wait value."""
    path = TEMPLATES_DIR / template_name
    if not path.exists():
        return 1500  # safe default

    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    basic_count = (
        text.count("animation")
        + text.count("keyframes")
        + text.count("transition")
    )
    complex_count = sum(text.count(kw) for kw in _COMPLEX_KEYWORDS)

    if complex_count > 20:
        return 3500
    if complex_count > 5 or basic_count > 25:
        return 2500
    if basic_count >= 15:
        return 1500
    return 800


@function_tool
def render_presentation(
    html_path: str,
    fps: int = 1,
    template_name: str = "",
    wait_override: int = -1,
) -> str:
    """
    Render an HTML carousel presentation to MP4 using render_video.py.
    Automatically chooses --wait based on the template's animation complexity
    unless wait_override >= 0 is supplied.

    Args:
        html_path: Path to the HTML file (e.g. "output/presentation.html").
        fps: Frames per second for the output video (default 1).
        template_name: Name of the template used (e.g. "glassmorphism.html").
                       Used to auto-select the --wait value.
        wait_override: If >= 0, use this value for --wait instead of auto-selecting.
    """
    html = Path(html_path)
    if not html.exists():
        return f"ERROR: HTML file not found: {html_path}"

    wait_ms = wait_override if wait_override >= 0 else _compute_wait_ms(template_name)

    script = Path(__file__).parent.parent / "render_video.py"
    cmd = [
        sys.executable, str(script),
        "--html", str(html),
        "--fps", str(fps),
        "--out", "output/reel.mp4",
        "--wait", str(wait_ms),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return "ERROR: render_video.py timed out after 5 minutes."

    lines = [
        f"Template : {template_name or '(unknown)'}",
        f"--wait   : {wait_ms} ms ({'auto' if wait_override < 0 else 'override'})",
        f"Exit code: {result.returncode}",
    ]
    if result.stdout:
        lines += ["--- stdout ---", result.stdout.strip()]
    if result.stderr and result.returncode != 0:
        lines += ["--- stderr ---", result.stderr[-400:]]
    lines.append("SUCCESS: output/reel.mp4 created." if result.returncode == 0 else "FAILED.")
    return "\n".join(lines)
