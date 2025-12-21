"""
Flamingo Markdown Guidelines Loader

Loads markdown formatting guidelines from environment variable path.
Single source of truth is the multi-platform-hub API.

Usage:
    from codewiki.src.be.flamingo_guidelines import get_guidelines_section

    # In prompts:
    prompt = f"{get_guidelines_section()}Your actual prompt here..."
"""
import os
from pathlib import Path

GUIDELINES_ENV_VAR = "FLAMINGO_MARKDOWN_GUIDELINES_PATH"


def load_flamingo_guidelines() -> str:
    """
    Load Flamingo markdown guidelines from file path specified in env var.

    Environment Variable:
        FLAMINGO_MARKDOWN_GUIDELINES_PATH: Path to the guidelines markdown file
                                           (downloaded during GitHub Actions workflow)

    Returns:
        Guidelines content string, or empty string if not available.
    """
    guidelines_path = os.environ.get(GUIDELINES_ENV_VAR)

    if not guidelines_path:
        print(f"[CodeWiki] {GUIDELINES_ENV_VAR} not set - continuing without Flamingo guidelines")
        return ""

    try:
        path = Path(guidelines_path)
        if not path.exists():
            print(f"[CodeWiki] Guidelines file not found: {guidelines_path}")
            return ""

        content = path.read_text(encoding='utf-8')
        print(f"[CodeWiki] Loaded Flamingo markdown guidelines ({len(content)} chars)")
        return content
    except Exception as e:
        print(f"[CodeWiki] Failed to load guidelines: {e}")
        return ""


# Load guidelines at module import time
FLAMINGO_MARKDOWN_GUIDELINES = load_flamingo_guidelines()


def get_guidelines_section() -> str:
    """
    Get formatted guidelines section for LLM prompts.

    Returns:
        Formatted section with header, or empty string if no guidelines.

    Example:
        >>> from codewiki.src.be.flamingo_guidelines import get_guidelines_section
        >>> prompt = f'''
        ... {get_guidelines_section()}
        ... Generate documentation for the following code...
        ... '''
    """
    if not FLAMINGO_MARKDOWN_GUIDELINES:
        return ""

    return f"""
## MARKDOWN FORMATTING GUIDELINES (Flamingo Stack)

{FLAMINGO_MARKDOWN_GUIDELINES}

---
"""
