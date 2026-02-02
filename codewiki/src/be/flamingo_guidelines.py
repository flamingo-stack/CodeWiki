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


def sanitize_problematic_patterns(text: str) -> str:
    """
    Sanitize problematic patterns WITHOUT escaping for .format().

    This function handles patterns that cause issues in prompts and shell processing:
    1. GitHub Actions syntax: ${{...}} → ${...}
    2. Triple braces: {{{...}}} → {{...}}
    3. Quadruple+ braces: Iteratively reduced to double braces

    This is the ENTRY POINT for all text sanitization. Call this when loading
    text from external sources (environment variables, files, etc.).

    Args:
        text: Raw text that may contain problematic patterns

    Returns:
        Sanitized text with problematic patterns normalized
    """
    import re

    print(f"[DEBUG] sanitize_problematic_patterns called - input length: {len(text)}")

    # Count braces before sanitization
    open_count_before = text.count('{')
    close_count_before = text.count('}')
    print(f"[DEBUG]   BEFORE: {{ count={open_count_before}, }} count={close_count_before}")

    # 1. GitHub Actions syntax: ${{...}} → ${...}
    # Use iterative approach for robustness with nested braces
    max_github_iterations = 10
    for _ in range(max_github_iterations):
        prev = text
        # Match ${{ followed by anything, then }}
        text = re.sub(r'\$\{\{(.*?)\}\}', r'${\1}', text)
        if text == prev:
            break

    # 2. Iteratively reduce excessive braces (handles all nesting levels)
    # This handles: {{{...}}} → {{...}}, {{{{...}}}} → {{...}}, etc.
    # Algorithm: Keep reducing 3+ consecutive braces to 2 until stable
    max_iterations = 100  # Prevent infinite loops
    iteration = 0
    while iteration < max_iterations:
        prev_text = text

        # Reduce triple opening braces: {{{ → {{
        text = text.replace('{{{', '{{')
        # Reduce triple closing braces: }}} → }}
        text = text.replace('}}}', '}}')

        # Reduce quadruple opening braces: {{{{ → {{
        text = text.replace('{{{{', '{{')
        # Reduce quadruple closing braces: }}}} → }}
        text = text.replace('}}}}', '}}')

        # Check for convergence
        if text == prev_text:
            break
        iteration += 1

    if iteration >= max_iterations:
        print(f"[WARNING] Sanitization exceeded max iterations ({max_iterations})")

    # Count braces after sanitization
    open_count_after = text.count('{')
    close_count_after = text.count('}')
    print(f"[DEBUG]   AFTER: {{ count={open_count_after}, }} count={close_count_after}")
    print(f"[DEBUG]   Sample (first 200 chars): {text[:200]}")

    return text


def sanitize_and_escape_format_braces(text: str) -> str:
    """
    Sanitize problematic patterns and escape curly braces for use with Python's str.format().

    This prevents KeyError when guidelines contain patterns like {Decision}, {Component}
    that would be interpreted as format placeholders.

    IMPORTANT: Numeric placeholders like {0}, {1}, {2} are PRESERVED as literal text,
    not escaped, because they appear in guidelines content and are NOT format placeholders
    for .format() (which only receives named arguments like module_name, custom_instructions).

    CRITICAL: Content goes through ONE formatting operation:
    - F-string substitution does NOT process braces in variables (f"{var}" → var as-is)
    - Only .format() call processes braces: {{ → {
    Therefore we need DOUBLE (2x) braces to produce literal braces in final output.

    Flow for non-numeric braces:
    - Original: {Decision}
    - After escape: {{Decision}}  (2 braces each side)
    - After f-string in SYSTEM_PROMPT: {{Decision}}  (no change - braces in substituted text not processed)
    - After .format(): {Decision}  (literal in output)

    Flow for numeric braces (PRESERVED):
    - Original: {0}
    - After escape: {0}  (NO CHANGE - left as-is)
    - After f-string in SYSTEM_PROMPT: {0}  (no change)
    - After .format(): {0}  (literal in output - .format() doesn't try to use as positional arg)

    Args:
        text: Text that may contain curly braces (preferably pre-sanitized)

    Returns:
        Sanitized text with curly braces doubled EXCEPT numeric placeholders like {0}, {1}
    """
    import re

    print(f"[DEBUG] sanitize_and_escape_format_braces called - input length: {len(text)}")

    # STEP 1: SANITIZATION (if not already done)
    # This ensures problematic patterns are normalized before we escape braces
    text = sanitize_problematic_patterns(text)

    # STEP 2: PRESERVE NUMERIC PLACEHOLDERS
    # Temporarily replace {0}, {1}, {2}, etc. with unique markers
    # These are LITERAL TEXT in guidelines, not format() placeholders
    numeric_placeholders = {}
    def preserve_numeric(match):
        placeholder = match.group(0)  # e.g., "{0}"
        marker = f"__NUMERIC_PLACEHOLDER_{len(numeric_placeholders)}__"
        numeric_placeholders[marker] = placeholder
        return marker

    # Replace all {digit} patterns with markers
    text = re.sub(r'\{(\d+)\}', preserve_numeric, text)
    print(f"[DEBUG]   Preserved {len(numeric_placeholders)} numeric placeholders: {list(numeric_placeholders.values())}")

    # STEP 3: ESCAPE ALL REMAINING BRACES
    # Now escape ALL braces (non-numeric content like {Decision}, {Component})
    result = text.replace("{", "{{").replace("}", "}}")

    # STEP 4: RESTORE NUMERIC PLACEHOLDERS AS DOUBLE-ESCAPED
    # Put back {0} as {{0}} so .format() converts it to {0} in final output
    # Flow: {{0}} → (after .format()) → {0} (literal in final text)
    for marker, placeholder in numeric_placeholders.items():
        escaped_placeholder = placeholder.replace('{', '{{').replace('}', '}}')
        result = result.replace(marker, escaped_placeholder)

    # Count braces after escaping
    open_count_after = result.count('{')
    close_count_after = result.count('}')
    print(f"[DEBUG]   AFTER ESCAPING: {{ count={open_count_after}, }} count={close_count_after}")
    print(f"[DEBUG]   Sample (first 200 chars): {result[:200]}")

    return result


def escape_format_braces(text: str) -> str:
    """
    Escape curly braces for use with Python's str.format().

    DEPRECATED: Use sanitize_and_escape_format_braces() instead.
    This is kept for backward compatibility but delegates to the new function.

    Args:
        text: Raw text that may contain curly braces

    Returns:
        Sanitized and escaped text with curly braces doubled
    """
    return sanitize_and_escape_format_braces(text)


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

    # Use string concatenation (no f-string needed here)
    # Escaped braces will be processed only once by .format() in prompt_template.py
    return (
        "\n## MARKDOWN FORMATTING GUIDELINES (Flamingo Stack)\n\n" +
        escaped_guidelines +
        "\n\n---\n"
    )


def load_custom_instructions() -> str:
    """
    Load repository-specific custom instructions from environment variable.

    CRITICAL: Sanitizes ALL problematic patterns on input:
    - GitHub Actions syntax: ${{...}} → ${...}
    - Triple braces: {{{...}}} → {{...}}
    - Quadruple+ braces: Iteratively reduced to double braces

    This ensures that raw text from the environment is safe before being
    used in prompts. Shell scripts should pass raw text without any
    preprocessing - ALL sanitization happens here in Python.

    Environment Variable:
        CUSTOM_REPO_INSTRUCTIONS: Custom instructions text (passed directly, not a file path)

    Returns:
        Sanitized custom instructions content string, or empty string if not available.
    """
    custom_instructions = os.environ.get(CUSTOM_INSTRUCTIONS_ENV_VAR, "")

    if not custom_instructions:
        print(f"[CodeWiki] {CUSTOM_INSTRUCTIONS_ENV_VAR} not set - continuing without custom instructions")
        return ""

    print(f"[CodeWiki] Loaded custom repo instructions ({len(custom_instructions)} chars)")

    # CRITICAL: Sanitize on input - this is the ONLY place text sanitization should happen
    # Shell scripts pass raw text, and we handle all sanitization here in Python
    # This prevents double-sanitization and ensures consistent behavior
    sanitized = sanitize_problematic_patterns(custom_instructions)
    print(f"[CodeWiki] Sanitized custom instructions ({len(sanitized)} chars after sanitization)")

    return sanitized


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

    # CUSTOM_REPO_INSTRUCTIONS is already sanitized during load via sanitize_problematic_patterns()
    # Here we escape curly braces using the proper function that preserves numeric placeholders
    # Use sanitize_and_escape_format_braces() instead of naive .replace() to handle {0}, {1}, etc.
    escaped_instructions = sanitize_and_escape_format_braces(CUSTOM_REPO_INSTRUCTIONS)

    # Use string concatenation (no f-string needed here)
    # Escaped braces will be processed only once by .format() in prompt_template.py
    return (
        "\n## REPOSITORY-SPECIFIC INSTRUCTIONS\n\n" +
        "The following instructions are specific to this repository and MUST be followed:\n\n" +
        escaped_instructions +
        "\n\n---\n"
    )
