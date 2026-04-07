from pathlib import Path
from agents import function_tool

OUTPUT_DIR = Path("output")
TEMPLATES_DIR = Path("presentation_creator/style-references")


@function_tool
def save_slides_markdown(content: str) -> str:
    """Save the slide outline as output/slides.md."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "slides.md"
    path.write_text(content, encoding="utf-8")
    return f"Saved slides.md ({len(content)} chars) → {path.resolve()}"


@function_tool
def read_slides_markdown() -> str:
    """Read the slide outline from output/slides.md."""
    path = OUTPUT_DIR / "slides.md"
    return path.read_text(encoding="utf-8")


@function_tool
def list_templates() -> list[str]:
    """List all available HTML presentation style templates."""
    return sorted(f.name for f in TEMPLATES_DIR.glob("*.html"))


@function_tool
def read_template(name: str) -> str:
    """Read the contents of a specific HTML template file."""
    path = TEMPLATES_DIR / name
    if not path.exists():
        return f"Template '{name}' not found. Use list_templates() to see available options."
    return path.read_text(encoding="utf-8")


@function_tool
def save_presentation_html(content: str) -> str:
    """Save the final HTML presentation to output/presentation.html."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "presentation.html"
    path.write_text(content, encoding="utf-8")
    return f"Saved presentation.html ({len(content)} chars) → {path.resolve()}"


@function_tool
def save_caption(content: str) -> str:
    """Save the social media caption to output/caption.txt."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "caption.txt"
    path.write_text(content, encoding="utf-8")
    return f"Saved caption.txt → {path.resolve()}"
