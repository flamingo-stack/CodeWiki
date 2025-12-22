"""
Flamingo Markdown Guidelines Loader

Loads markdown formatting guidelines from environment variable path.
Single source of truth is the multi-platform-hub API.

Also loads repository-specific custom instructions from environment variable.

Usage:
    from codewiki.src.be.flamingo_guidelines import get_guidelines_section, get_custom_instructions_section

    # In prompts:
    prompt = f"{get_custom_instructions_section()}{get_guidelines_section()}Your actual prompt here..."
"""
import os
from pathlib import Path

GUIDELINES_ENV_VAR = "FLAMINGO_MARKDOWN_GUIDELINES_PATH"
CUSTOM_INSTRUCTIONS_ENV_VAR = "CUSTOM_REPO_INSTRUCTIONS"


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


def escape_format_braces(text: str) -> str:
    """
    Escape curly braces for use with Python's str.format().

    This prevents KeyError when guidelines contain patterns like {Decision}, {Component}
    that would be interpreted as format placeholders.

    Args:
        text: Raw text that may contain curly braces

    Returns:
        Text with curly braces doubled ({{ and }})
    """
    # Double all curly braces to escape them for .format()
    return text.replace("{", "{{").replace("}", "}}")


def get_guidelines_section() -> str:
    """
    Get formatted guidelines section for LLM prompts.

    Returns:
        Formatted section with header, or empty string if no guidelines.

    Note:
        Curly braces in guidelines are escaped ({{ }}) to prevent KeyError
        when the prompt template is used with .format(module_name=...).

    Example:
        >>> from codewiki.src.be.flamingo_guidelines import get_guidelines_section
        >>> prompt = f'''
        ... {get_guidelines_section()}
        ... Generate documentation for the following code...
        ... '''
    """
    if not FLAMINGO_MARKDOWN_GUIDELINES:
        return ""

    # Escape curly braces to prevent KeyError in .format() calls
    # This is critical because guidelines may contain Mermaid diagrams,
    # code examples, or other content with {placeholder} patterns
    escaped_guidelines = escape_format_braces(FLAMINGO_MARKDOWN_GUIDELINES)

    return f"""
## MARKDOWN FORMATTING GUIDELINES (Flamingo Stack)

{escaped_guidelines}

---
"""


def load_custom_instructions() -> str:
    """
    Load repository-specific custom instructions from environment variable.

    Environment Variable:
        CUSTOM_REPO_INSTRUCTIONS: Custom instructions text (passed directly, not a file path)

    Returns:
        Custom instructions content string, or empty string if not available.
    """
    custom_instructions = os.environ.get(CUSTOM_INSTRUCTIONS_ENV_VAR, "")

    if not custom_instructions:
        print(f"[CodeWiki] {CUSTOM_INSTRUCTIONS_ENV_VAR} not set - continuing without custom instructions")
        return ""

    print(f"[CodeWiki] Loaded custom repo instructions ({len(custom_instructions)} chars)")
    return custom_instructions


# Load custom instructions at module import time
CUSTOM_REPO_INSTRUCTIONS = load_custom_instructions()


def get_custom_instructions_section() -> str:
    """
    Get formatted custom instructions section for LLM prompts.

    Returns:
        Formatted section with header, or empty string if no custom instructions.

    Note:
        Curly braces in instructions are escaped ({{ }}) to prevent KeyError
        when the prompt template is used with .format(module_name=...).

    Example:
        >>> from codewiki.src.be.flamingo_guidelines import get_custom_instructions_section
        >>> prompt = f'''
        ... {get_custom_instructions_section()}
        ... {get_guidelines_section()}
        ... Generate documentation for the following code...
        ... '''
    """
    if not CUSTOM_REPO_INSTRUCTIONS:
        return ""

    # Escape curly braces to prevent KeyError in .format() calls
    escaped_instructions = escape_format_braces(CUSTOM_REPO_INSTRUCTIONS)

    return f"""
## REPOSITORY-SPECIFIC INSTRUCTIONS

The following instructions are specific to this repository and MUST be followed:

{escaped_instructions}

---
"""
