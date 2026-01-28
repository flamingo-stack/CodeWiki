import re
from pathlib import Path
from typing import List, Tuple
import logging
import tiktoken
import traceback


logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# ---------------------- Complexity Check --------------------
# ------------------------------------------------------------

def is_complex_module(components: dict[str, any], core_component_ids: list[str]) -> bool:
    files = set()
    for component_id in core_component_ids:
        if component_id in components:
            files.add(components[component_id].file_path)

    result = len(files) > 1

    return result


# ------------------------------------------------------------
# ---------------------- Token Counting ---------------------
# ------------------------------------------------------------

enc = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text.
    """
    length = len(enc.encode(text))
    # logger.debug(f"Number of tokens: {length}")
    return length


# ------------------------------------------------------------
# ---------------------- Mermaid Validation -----------------
# ------------------------------------------------------------

async def validate_mermaid_diagrams(md_file_path: str, relative_path: str) -> str:
    """
    Validate all Mermaid diagrams in a markdown file.
    
    Args:
        md_file_path: Path to the markdown file to check
        relative_path: Relative path to the markdown file
    Returns:
        "All mermaid diagrams are syntax correct" if all diagrams are valid,
        otherwise returns error message with details about invalid diagrams
    """

    try:
        # Read the markdown file
        file_path = Path(md_file_path)
        if not file_path.exists():
            return f"Error: File '{md_file_path}' does not exist"
        
        content = file_path.read_text(encoding='utf-8')
        
        # Extract all mermaid code blocks
        mermaid_blocks = extract_mermaid_blocks(content)
        
        if not mermaid_blocks:
            return "No mermaid diagrams found in the file"
        
        # Validate each mermaid diagram sequentially to avoid segfaults
        errors = []
        for i, (line_start, diagram_content) in enumerate(mermaid_blocks, 1):
            error_msg = await validate_single_diagram(diagram_content, i, line_start)
            if error_msg:
                errors.append("\n")
                errors.append(error_msg)
        
        if errors:
            logger.warning(f"Mermaid syntax errors found in file: {md_file_path}")
            for error in errors:
                if error.strip():
                    logger.warning(f"  {error.strip()}")

        if errors:
            return "Mermaid syntax errors found in file: " + relative_path + "\n" + "\n".join(errors)
        else:
            return "All mermaid diagrams in file: " + relative_path + " are syntax correct"
            
    except Exception as e:
        return f"Error processing file: {str(e)}"


def extract_mermaid_blocks(content: str) -> List[Tuple[int, str]]:
    """
    Extract all mermaid code blocks from markdown content.
    
    Returns:
        List of tuples containing (line_number, diagram_content)
    """
    mermaid_blocks = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for mermaid code block start
        if line == '```mermaid' or line.startswith('```mermaid'):
            start_line = i + 1
            diagram_lines = []
            i += 1
            
            # Collect lines until we find the closing ```
            while i < len(lines):
                if lines[i].strip() == '```':
                    break
                diagram_lines.append(lines[i])
                i += 1
            
            if diagram_lines:  # Only add non-empty diagrams
                diagram_content = '\n'.join(diagram_lines)
                mermaid_blocks.append((start_line, diagram_content))
        
        i += 1
    
    return mermaid_blocks


async def validate_single_diagram(diagram_content: str, diagram_num: int, line_start: int) -> str:
    """
    Validate a single mermaid diagram.
    
    Args:
        diagram_content: The mermaid diagram content
        diagram_num: Diagram number for error reporting
        line_start: Starting line number in the file
        
    Returns:
        Error message if invalid, empty string if valid
    """
    import sys
    import os
    from io import StringIO

    core_error = ""
    
    try:
        from mermaid_parser.parser import parse_mermaid_py
        # logger.debug("Using mermaid-parser-py to validate mermaid diagrams")
    
        try:
            # Redirect stderr to suppress mermaid parser JavaScript errors
            old_stderr = sys.stderr
            sys.stderr = open(os.devnull, 'w')
            
            try:
                json_output = await parse_mermaid_py(diagram_content)
            finally:
                # Restore stderr
                sys.stderr.close()
                sys.stderr = old_stderr
        except Exception as e:
            error_str = str(e)
            
            # Extract the core error information from the exception message
            # Look for the pattern that contains "Parse error on line X:"
            error_pattern = r"Error:(.*?)(?=Stack Trace:|$)"
            match = re.search(error_pattern, error_str, re.DOTALL)
            
            if match:
                core_error = match.group(0).strip()
                core_error = core_error
            else:
                logger.error(f"No match found for error pattern, fallback to mermaid-py\n{error_str}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise Exception(error_str)

    except Exception as e:
        logger.warning("Using mermaid-py to validate mermaid diagrams")
        try:
            import mermaid as md
            # Create Mermaid object and check response
            render = md.Mermaid(diagram_content)
            core_error = render.svg_response.text
            
        except Exception as e:
            return f"  Diagram {diagram_num}: Exception during validation - {str(e)}"

    # Check if response indicates a parse error
    if core_error:
        # Extract line number from parse error and calculate actual line in markdown file
        line_match = re.search(r'line (\d+)', core_error)
        if line_match:
            error_line_in_diagram = int(line_match.group(1))
            actual_line_in_file = line_start + error_line_in_diagram
            newline = '\n'
            return f"Diagram {diagram_num}: Parse error on line {actual_line_in_file}:{newline}{newline.join(core_error.split(newline)[1:])}"
        else:
            return f"Diagram {diagram_num}: {core_error}"
    
    return ""  # No error


def extract_and_save_mermaid_diagrams(md_file_path: str, diagrams_dir: str) -> list:
    """
    Extract all Mermaid diagrams from a markdown file and save them as separate .mmd files.

    Args:
        md_file_path: Path to the markdown file to process
        diagrams_dir: Directory where .mmd files should be saved

    Returns:
        List of created diagram file paths
    """
    from pathlib import Path
    import os

    file_path = Path(md_file_path)
    if not file_path.exists():
        logger.warning(f"Cannot extract diagrams: File '{md_file_path}' does not exist")
        return []

    content = file_path.read_text(encoding='utf-8')
    mermaid_blocks = extract_mermaid_blocks(content)

    if not mermaid_blocks:
        return []

    # Ensure diagrams directory exists
    os.makedirs(diagrams_dir, exist_ok=True)

    # Base name for diagram files (from the markdown filename)
    base_name = file_path.stem

    created_files = []
    for i, (line_start, diagram_content) in enumerate(mermaid_blocks, 1):
        # Determine diagram type from first line
        first_line = diagram_content.strip().split('\n')[0].lower()

        if 'flowchart' in first_line or 'graph' in first_line:
            diagram_type = 'flowchart'
        elif 'sequencediagram' in first_line or 'sequence' in first_line:
            diagram_type = 'sequence'
        elif 'classdiagram' in first_line or 'class' in first_line:
            diagram_type = 'class'
        elif 'erdiagram' in first_line or 'er' in first_line:
            diagram_type = 'er'
        elif 'statediagram' in first_line or 'state' in first_line:
            diagram_type = 'state'
        elif 'gantt' in first_line:
            diagram_type = 'gantt'
        elif 'pie' in first_line:
            diagram_type = 'pie'
        elif 'journey' in first_line:
            diagram_type = 'journey'
        elif 'gitgraph' in first_line:
            diagram_type = 'gitgraph'
        elif 'c4' in first_line:
            diagram_type = 'c4'
        else:
            diagram_type = 'diagram'

        # Create filename: module_name-diagram_type-N.mmd
        if len(mermaid_blocks) == 1:
            diagram_filename = f"{base_name}-{diagram_type}.mmd"
        else:
            diagram_filename = f"{base_name}-{diagram_type}-{i}.mmd"

        diagram_path = os.path.join(diagrams_dir, diagram_filename)

        try:
            with open(diagram_path, 'w', encoding='utf-8') as f:
                f.write(diagram_content)
            created_files.append(diagram_path)
            logger.info(f"Extracted Mermaid diagram: {diagram_filename}")
        except Exception as e:
            logger.error(f"Failed to save diagram {diagram_filename}: {e}")

    return created_files


def create_diagrams_readme(diagrams_dir: str, diagram_files: list) -> str:
    """
    Create a README.md index file for the diagrams directory.

    Args:
        diagrams_dir: Directory containing the diagram files
        diagram_files: List of diagram file paths

    Returns:
        Path to created README.md
    """
    import os
    from pathlib import Path

    if not diagram_files:
        return None

    readme_path = os.path.join(diagrams_dir, 'README.md')

    # Group diagrams by module
    diagrams_by_module = {}
    for path in diagram_files:
        filename = os.path.basename(path)
        # Extract module name (everything before the diagram type)
        parts = filename.rsplit('-', 2)
        if len(parts) >= 2:
            module_name = parts[0]
        else:
            module_name = 'general'

        if module_name not in diagrams_by_module:
            diagrams_by_module[module_name] = []
        diagrams_by_module[module_name].append(filename)

    # Generate README content
    lines = [
        '# Architecture Diagrams',
        '',
        'This directory contains Mermaid diagrams extracted from the architecture documentation.',
        '',
        '## Diagrams',
        ''
    ]

    for module_name, files in sorted(diagrams_by_module.items()):
        lines.append(f'### {module_name.replace("_", " ").title()}')
        lines.append('')
        for filename in sorted(files):
            lines.append(f'- [{filename}](./{filename})')
        lines.append('')

    lines.extend([
        '## Usage',
        '',
        'These `.mmd` files can be rendered using:',
        '- [Mermaid Live Editor](https://mermaid.live/)',
        '- VS Code with Mermaid extension',
        '- GitHub markdown preview (rename to `.md` and wrap in ```mermaid blocks)',
        ''
    ])

    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        logger.info(f"Created diagrams README: {readme_path}")
        return readme_path
    except Exception as e:
        logger.error(f"Failed to create diagrams README: {e}")
        return None


if __name__ == "__main__":
    # Test with the provided file
    import asyncio
    test_file = "output/docs/SWE_agent-docs/agent_hooks.md"
    result = asyncio.run(validate_mermaid_diagrams(test_file, "agent_hooks.md"))
    print(result)