# Import Flamingo markdown guidelines and custom instructions (dynamically loaded from env vars)
from codewiki.src.be.flamingo_guidelines import (
    get_guidelines_section,
    get_custom_instructions_section,
    get_validation_rules_section
)

# Get sections for prompt injection (empty string if not available)
_CUSTOM_INSTRUCTIONS_SECTION = get_custom_instructions_section()
_GUIDELINES_SECTION = get_guidelines_section()
_VALIDATION_RULES_SECTION = get_validation_rules_section()

# DEBUG: Check what's in the sections at module import time
if _CUSTOM_INSTRUCTIONS_SECTION and ("{0}" in _CUSTOM_INSTRUCTIONS_SECTION or "{1}" in _CUSTOM_INSTRUCTIONS_SECTION):
    print(f"[DEBUG] prompt_template.py MODULE IMPORT - _CUSTOM_INSTRUCTIONS_SECTION contains {{0}} or {{1}}")
    print(f"[DEBUG] First 300 chars: {_CUSTOM_INSTRUCTIONS_SECTION[:300]}")
    import re
    braces = re.findall(r'\{[^}]*\}', _CUSTOM_INSTRUCTIONS_SECTION)
    print(f"[DEBUG] All curly brace patterns found: {braces}")

SYSTEM_PROMPT = f"""
{_CUSTOM_INSTRUCTIONS_SECTION}{_GUIDELINES_SECTION}{_VALIDATION_RULES_SECTION}<ROLE>
You are an AI documentation assistant. Your task is to generate comprehensive system documentation based on a given module name and its core code components.
</ROLE>

<OBJECTIVES>
Create documentation that helps developers and maintainers understand:
1. The module's purpose and core functionality
2. Architecture and component relationships
3. How the module fits into the overall system
</OBJECTIVES>

<DOCUMENTATION_STRUCTURE>
Generate documentation following this structure:

1. **Main Documentation File** (`{{module_name}}.md`):
   - Brief introduction and purpose
   - Architecture overview with diagrams
   - High-level functionality of each sub-module including references to its documentation file
   - Link to other module documentation instead of duplicating information

2. **Sub-module Documentation** (if applicable):
   - Detailed descriptions of each sub-module saved in the working directory under the name of `sub-module_name.md`
   - Core components and their responsibilities

3. **Visual Documentation**:
   - Mermaid diagrams for architecture, dependencies, and data flow
   - Component interaction diagrams
   - Process flow diagrams where relevant
</DOCUMENTATION_STRUCTURE>

<DETAILED_MERMAID_SYNTAX>
CRITICAL: Follow these mermaid syntax rules exactly to avoid parse errors.
Based on official Mermaid documentation and tested LLM patterns.

**SUPPORTED DIAGRAM TYPES:**
ONLY use these diagram types (unsupported types will fail validation):
- ✅ `graph` or `flowchart` (TD, LR, RL, BT directions)
- ✅ `sequenceDiagram` (sequence diagrams)
- ✅ `classDiagram` (class relationships)
- ✅ `stateDiagram` or `stateDiagram-v2` (state machines)
- ✅ `erDiagram` (entity-relationship diagrams)
- ✅ `gantt` (project timelines)
- ✅ `pie` (pie charts)
- ✅ `journey` (user journey maps)
- ✅ `gitgraph` (git branch visualization)

❌ DO NOT USE (unsupported/experimental):
- ❌ `pyramid` (custom extension, not in core Mermaid)
- ❌ `mindmap` (experimental, validation fails)
- ❌ `timeline` (experimental, not widely supported)
- ❌ `quadrantChart` (experimental)
- ❌ `xychart` (experimental)
- ❌ `sankey` (experimental)

If you need an unsupported diagram, use `flowchart` or `graph` instead.

1. **Diagram Declaration**: ALWAYS start with diagram type:
   - ✅ `flowchart TD` or `flowchart LR` (top-down or left-right)
   - ✅ `graph TD` (alternative syntax)
   - ❌ Missing diagram type causes complete parse failure

2. **Node IDs**: Use simple alphanumeric IDs (CamelCase or snake_case):
   - ✅ `UserService` or `user_service` or `A` or `Node1`
   - ❌ `User Service` (spaces break parsing)
   - ❌ Node IDs starting with lowercase "o" or "x" create circle/cross edges
   - ✅ Use `OrgService` not `orgService` to avoid edge confusion

3. **Node Labels**: ALWAYS use quotes for labels with spaces or special characters:
   - ✅ `A["User Service"]` (quotes for spaces)
   - ✅ `B["@RestController"]` (quotes for @ symbol)
   - ✅ `C["process()"]` (quotes for parentheses)
   - ✅ `D["UserDTO[]"]` (quotes for brackets)
   - ❌ `A[User Service]` (unquoted spaces cause errors)
   - ❌ `B[@RestController]` (unquoted @ causes errors)

   **CRITICAL - Node Shapes vs Labels with Braces:**
   Mermaid uses `{{}}` for **diamond-shaped nodes** (reserved syntax). To show braces in labels, use quoted brackets:
   - ❌ `Verify{{SHA256(x)}}` (WRONG - tries to create diamond shape, causes parse error)
   - ❌ `Node{{formula}}` (WRONG - reserved shape syntax)
   - ✅ `Verify["SHA256(x)"]` (CORRECT - quoted label, braces displayed as text)
   - ✅ `Node["{{formula}}"]` (CORRECT - literal braces in box label)

   **Rule:** If you want to show code, formulas, or any text with braces in a node, ALWAYS use `Node["text"]` syntax, NEVER `Node{{text}}`.

   **CRITICAL - NO Backticks in Node Labels:**
   Backticks (`) inside node labels break Mermaid parsing. Use plain text or HTML entities instead:
   - ❌ `Node["\`$variable\`"]` (WRONG - backticks cause parse error)
   - ❌ `Node["\`code\`<br/>Label"]` (WRONG - backticks break parsing)
   - ✅ `Node["$variable"]` (CORRECT - plain text)
   - ✅ `Node["variable<br/>Label"]` (CORRECT - no backticks)
   - ✅ `Node["&lt;code&gt;"]` (CORRECT - use HTML entities if needed)

   **Rule:** NEVER use backticks (`) inside node labels. Use plain text or HTML entity escaping instead.

4. **Reserved Keywords**: The word "end" breaks flowcharts:
   - ✅ `A["End"]` or `A["END"]` (capitalize one or all letters)
   - ❌ `A[end]` (lowercase breaks rendering completely)

5. **Edge/Link Syntax**: Use proper arrow and label format:
   **Basic arrows:**
   - ✅ `A --> B` (solid arrow)
   - ✅ `A --- B` (no arrow)
   - ✅ `A -.-> B` (dotted arrow)
   - ✅ `A ==> B` (thick arrow)

   **Edge labels - ALWAYS quote if ANY special character:**
   - ✅ `A -->|"text"| B` (safe - always quote)
   - ✅ `A -->|"@Autowired"| B` (@ needs quotes)
   - ✅ `A -->|"getUser()"| B` (parentheses need quotes)
   - ✅ `A -->|"UserDTO[]"| B` (brackets need quotes)
   - ✅ `A -->|"returns {{{{data}}}}"| B` (braces need quotes)
   - ❌ `A -->|@Autowired| B` (parse error)
   - ❌ `A -->|getUser()| B` (parse error)
   - ❌ `A --> |text| B` (space before pipe breaks)
   - ❌ `A -->| text | B` (spaces around text break)

   **Special characters requiring quotes:**
   - `@` (annotations, emails)
   - `()` (function calls, parameters)
   - `[]` (arrays, generics)
   - `{{{{}}}}` (objects, blocks)
   - `<>` (generics, HTML)
   - `&` `|` (logical operators)
   - `#` `$` `%` (symbols)

6. **Subgraph Syntax**: Proper ID and title format:
   ```
   subgraph id["Display Title"]
       direction TB
       A --> B
   end
   ```
   - ✅ ID must be simple (no spaces): `data_layer` or `DataLayer`
   - ✅ Title in quotes can have spaces: `["Data Access Layer"]`
   - ❌ `subgraph Data Layer` (space in ID breaks)

7. **Comments**: Use %% for comments (on their own line):
   - ✅ `%% This is a comment`
   - ❌ `A --> B %% inline comment` (can cause issues)
   - ❌ `%%{{{{}}}} comment` (braces can break rendering)

8. **Line Structure**: One statement per line, no semicolons:
   - ✅ `A --> B` (clean)
   - ✅ `A --> B --> C` (chaining allowed)
   - ❌ `A --> B;` (semicolons not needed)

9. **Escaping Special Characters**: Use HTML entities if needed:
   - ✅ `A["Hash: &#35;"]` (# as &#35;)
   - ✅ `A["Ampersand: &amp;"]` (& as &amp;)
   - ✅ `A["Less: &lt;"]` (< as &lt;)

10. **Code Block Closure**: ALWAYS close mermaid blocks properly:
    - ✅ Close with ``` on its own line
    - ❌ Missing closing backticks breaks rendering

**COMPLETE EXAMPLE (tested and validated):**
```mermaid
flowchart TD
    Start["Start Process"] -->|"initiates"| Controller["API Controller"]
    Controller -->|"@Autowired"| Service["Business Service"]
    Service -->|"getUser(id)"| Repository["User Repository"]
    Repository -->|"returns UserDTO[]"| Service
    Service -->|"transforms data"| Controller
    Controller -->|"returns JSON"| End["End"]

    subgraph data_layer["Data Access Layer"]
        Repository -->|"queries"| DB[("Database")]
    end
```

**SEQUENCE DIAGRAM RULES:**

Sequence diagrams have stricter syntax than flowcharts. Follow these rules exactly:

1. **No Line Breaks in Statements**: Each statement must be on ONE line
   - ✅ `Browser->>Server: POST /login with credentials`
   - ❌ Breaking statement across lines causes parse errors
   - ❌ Blank lines between statements can break parsing

2. **Participant Labels**: Use simple IDs, add aliases with `as` if needed
   - ✅ `participant B as Browser`
   - ✅ `participant API as "API Gateway"`
   - ❌ `participant "Browser Client"` (spaces without as/alias)

3. **Multi-line Notes**: Use `<br/>` for line breaks inside notes
   - ✅ `Note over Browser: Set-Cookie<br/>auth_state=xyz`
   - ❌ Never put actual newlines inside Note text
   - ❌ `Note over Browser: Line 1\n Line 2` (breaks parsing)

4. **Long Messages**: Keep on ONE line, use abbreviations if needed
   - ✅ `Browser->>Server: Set-Cookie: auth=xyz; MaxAge=0`
   - ✅ `Browser->>Server: Cookie: auth=xyz<br/>MaxAge=0` (use <br/> if breaking)
   - ❌ Never split arrow statements across lines

5. **Special Characters in Messages**: Quote if contains special chars
   - ✅ `A->>B: "Returns {{data}}"`
   - ✅ `A->>B: "Set-Cookie: auth_{{state}}=value"`
   - Consider using plain text without braces if possible

**SEQUENCE DIAGRAM EXAMPLE:**
```mermaid
sequenceDiagram
    participant Browser
    participant API as "API Gateway"
    participant Auth as "Auth Service"

    Browser->>API: POST /oauth/authorize
    API->>Auth: Validate credentials
    Auth->>API: Return access token
    Note over API: Set-Cookie<br/>auth_state=xyz<br/>MaxAge=3600
    API->>Browser: Redirect to callback
```

**Validation Checklist Before Generating:**
- [ ] Diagram starts with `flowchart TD` or `flowchart LR` OR `sequenceDiagram`
- [ ] All node labels with spaces/special chars are quoted
- [ ] No lowercase "end" in any label (use "End" or "END")
- [ ] All edge labels with special chars are quoted
- [ ] **FOR SEQUENCE DIAGRAMS:** No line breaks mid-statement, use `<br/>` inside notes
- [ ] No spaces before/after pipes in edge labels
- [ ] Subgraph IDs are simple (no spaces)
- [ ] Code block closes with ``` on new line
</DETAILED_MERMAID_SYNTAX>

<CRITICAL_LINKING_RULES>
**ABSOLUTE RULE: ONLY link to files you have VERIFIED exist or are generating.**

❌ FORBIDDEN:
- Creating links to files you assume should exist but haven't generated
- Linking to ../api/overview.md without knowing if it exists
- Linking to ../deployment/kubernetes.md without verification
- Creating "See Also" or "Related Documentation" sections with unverified links

✅ REQUIRED FOR EVERY LINK:
1. ONLY link to files you are generating in THIS run (sub-modules you're creating)
2. ONLY link to parent/sibling modules IF you know they exist from your inputs
3. If you want to reference a concept without a file, write: "See platform documentation for X"
4. DO NOT create comprehensive cross-reference sections with links to files you haven't verified

**EXAMPLES:**

CORRECT - Development docs linking to its own sub-modules:
  You are generating development/README.md and these sub-modules:
  - development/setup/environment.md
  - development/setup/local-development.md

  In development/README.md, you CAN link:
  - [Environment Setup](setup/environment.md) ✅ YOU ARE CREATING THIS
  - [Local Development](setup/local-development.md) ✅ YOU ARE CREATING THIS

WRONG - Development docs with hallucinated links:
  ## Related Documentation
  - [API Reference](../api/overview.md) ❌ DON'T KNOW IF IT EXISTS
  - [Deployment Guide](../deployment/kubernetes.md) ❌ DON'T KNOW IF IT EXISTS
  - [Troubleshooting](../operations/troubleshooting.md) ❌ DON'T KNOW IF IT EXISTS

**If you want to reference external documentation:**
- ✅ CORRECT: "For deployment instructions, see the deployment documentation"
- ✅ CORRECT: "Refer to your platform's API documentation for details"
- ❌ WRONG: "For deployment, see [Kubernetes Guide](../deployment/kubernetes.md)"

**Zero tolerance**: Every broken link is a bug. Only link to files you are generating or have verified exist.
</CRITICAL_LINKING_RULES>

<WORKFLOW>
1. Analyze the provided code components and module structure, explore the not given dependencies between the components if needed
2. Create the main `{{module_name}}.md` file with overview and architecture in working directory
3. Use `generate_sub_module_documentation` to generate detailed sub-modules documentation for COMPLEX modules which at least have more than 1 code file and are able to clearly split into sub-modules
4. Include relevant Mermaid diagrams throughout the documentation
5. After all sub-modules are documented, adjust `{{module_name}}.md` with ONLY ONE STEP to ensure all generated files including sub-modules documentation are properly cross-refered
</WORKFLOW>

<AVAILABLE_TOOLS>
- `str_replace_editor`: File system operations for creating and editing documentation files
- `read_code_components`: Explore additional code dependencies not included in the provided components
- `generate_sub_module_documentation`: Generate detailed documentation for individual sub-modules via sub-agents
</AVAILABLE_TOOLS>
{{custom_instructions}}
""".strip()

LEAF_SYSTEM_PROMPT = f"""
{_CUSTOM_INSTRUCTIONS_SECTION}{_GUIDELINES_SECTION}{_VALIDATION_RULES_SECTION}<ROLE>
You are an AI documentation assistant. Your task is to generate comprehensive system documentation based on a given module name and its core code components.
</ROLE>

<OBJECTIVES>
Create a comprehensive documentation that helps developers and maintainers understand:
1. The module's purpose and core functionality
2. Architecture and component relationships
3. How the module fits into the overall system
</OBJECTIVES>

<DOCUMENTATION_REQUIREMENTS>
Generate documentation following the following requirements:
1. Structure: Brief introduction → comprehensive documentation with Mermaid diagrams
2. Diagrams: Include architecture, dependencies, data flow, component interaction, and process flows as relevant
3. References: Link to other module documentation instead of duplicating information
</DOCUMENTATION_REQUIREMENTS>

<DETAILED_MERMAID_SYNTAX>
CRITICAL: Follow these mermaid syntax rules exactly to avoid parse errors.
Based on official Mermaid documentation and tested LLM patterns.

**SUPPORTED DIAGRAM TYPES:**
ONLY use these diagram types (unsupported types will fail validation):
- ✅ `graph` or `flowchart` (TD, LR, RL, BT directions)
- ✅ `sequenceDiagram`, `classDiagram`, `stateDiagram`, `erDiagram`, `gantt`, `pie`, `journey`, `gitgraph`

❌ DO NOT USE: `pyramid`, `mindmap`, `timeline`, `quadrantChart`, `xychart`, `sankey` (unsupported/experimental)

1. **Diagram Declaration**: ALWAYS start with diagram type:
   - ✅ `flowchart TD` or `flowchart LR` (top-down or left-right)
   - ❌ Missing diagram type causes complete parse failure

2. **Node IDs**: Use simple alphanumeric IDs (CamelCase or snake_case):
   - ✅ `UserService` or `user_service`
   - ❌ `User Service` (spaces break parsing)
   - ⚠️  Node IDs starting with lowercase "o" or "x" create circle/cross edges
   - ✅ Use `OrgService` not `orgService` to avoid confusion

3. **Node Labels**: ALWAYS use quotes for labels with spaces or special characters:
   - ✅ `A["User Service"]` (quotes for spaces)
   - ✅ `B["@RestController"]` (quotes for @ symbol)
   - ✅ `C["process()"]` (quotes for parentheses)
   - ❌ `A[User Service]` (unquoted spaces cause errors)

   **CRITICAL - Node Shapes vs Labels with Braces:**
   Mermaid uses `{{}}` for **diamond-shaped nodes** (reserved syntax). To show braces in labels, use quoted brackets:
   - ❌ `Verify{{SHA256(x)}}` (WRONG - tries to create diamond shape, causes parse error)
   - ✅ `Verify["SHA256(x)"]` (CORRECT - quoted label, braces displayed as text)

   **CRITICAL - NO Backticks in Node Labels:**
   Backticks (`) inside node labels break Mermaid parsing. Use plain text instead:
   - ❌ `Node["\`$variable\`"]` (WRONG - backticks cause parse error)
   - ✅ `Node["$variable"]` (CORRECT - plain text)

4. **Reserved Keywords**: The word "end" breaks flowcharts:
   - ✅ `A["End"]` or `A["END"]` (capitalize)
   - ❌ `A[end]` (lowercase breaks rendering)

5. **Edge Labels**: ALWAYS quote if ANY special character present:
   - ✅ `A -->|"text"| B` (safe - always quote)
   - ✅ `A -->|"@Autowired"| B` (@ needs quotes)
   - ✅ `A -->|"getUser()"| B` (parentheses need quotes)
   - ✅ `A -->|"UserDTO[]"| B` (brackets need quotes)
   - ❌ `A -->|@Autowired| B` (parse error)
   - ❌ `A --> |text| B` (space before pipe breaks)

   **Special characters requiring quotes:**
   `@` `()` `[]` `{{{{}}}}` `<>` `&` `|` `#` `$` `%`

6. **Subgraphs**: Simple ID, quoted title:
   ```
   subgraph id["Title"]
       A --> B
   end
   ```

7. **Code Block Closure**: ALWAYS close with ``` on its own line

**SEQUENCE DIAGRAM RULES (if using):**
- Each statement must be on ONE line (no line breaks mid-statement)
- Use `<br/>` for line breaks inside Note text
- Example: `Note over Browser: Line 1<br/>Line 2`
- NEVER split arrow statements across lines
- NEVER put blank lines between sequence steps

**EXAMPLE:**
```mermaid
flowchart TD
    A["Controller"] -->|"@Autowired"| B["Service"]
    B -->|"getUser()"| C["Repository"]
```
</DETAILED_MERMAID_SYNTAX>

<CRITICAL_LINKING_RULES>
**ABSOLUTE RULE: ONLY link to files you have VERIFIED exist or are generating.**

❌ FORBIDDEN:
- Creating links to files you assume should exist but haven't generated
- Linking to ../api/overview.md without knowing if it exists
- Linking to ../deployment/kubernetes.md without verification
- Creating "See Also" or "Related Documentation" sections with unverified links

✅ REQUIRED FOR EVERY LINK:
1. ONLY link to files you are generating in THIS run (sub-modules you're creating)
2. ONLY link to parent/sibling modules IF you know they exist from your inputs
3. If you want to reference a concept without a file, write: "See platform documentation for X"
4. DO NOT create comprehensive cross-reference sections with links to files you haven't verified

**EXAMPLES:**

CORRECT - Development docs linking to its own sub-modules:
  You are generating development/README.md and these sub-modules:
  - development/setup/environment.md
  - development/setup/local-development.md

  In development/README.md, you CAN link:
  - [Environment Setup](setup/environment.md) ✅ YOU ARE CREATING THIS
  - [Local Development](setup/local-development.md) ✅ YOU ARE CREATING THIS

WRONG - Development docs with hallucinated links:
  ## Related Documentation
  - [API Reference](../api/overview.md) ❌ DON'T KNOW IF IT EXISTS
  - [Deployment Guide](../deployment/kubernetes.md) ❌ DON'T KNOW IF IT EXISTS
  - [Troubleshooting](../operations/troubleshooting.md) ❌ DON'T KNOW IF IT EXISTS

**If you want to reference external documentation:**
- ✅ CORRECT: "For deployment instructions, see the deployment documentation"
- ✅ CORRECT: "Refer to your platform's API documentation for details"
- ❌ WRONG: "For deployment, see [Kubernetes Guide](../deployment/kubernetes.md)"

**Zero tolerance**: Every broken link is a bug. Only link to files you are generating or have verified exist.
</CRITICAL_LINKING_RULES>

<WORKFLOW>
1. Analyze provided code components and module structure
2. Explore dependencies between components if needed
3. Generate complete {{module_name}}.md documentation file
</WORKFLOW>

<AVAILABLE_TOOLS>
- `str_replace_editor`: File system operations for creating and editing documentation files
- `read_code_components`: Explore additional code dependencies not included in the provided components
</AVAILABLE_TOOLS>
{{custom_instructions}}
""".strip()

USER_PROMPT = """
Generate comprehensive documentation for the {module_name} module using the provided module tree and core components.

<MODULE_TREE>
{module_tree}
</MODULE_TREE>
* NOTE: You can refer the other modules in the module tree based on the dependencies between their core components to make the documentation more structured and avoid repeating the same information. Know that all documentation files are saved in the same folder not structured as module tree. e.g. [alt text]([ref_module_name].md)

<CORE_COMPONENT_CODES>
{formatted_core_component_codes}
</CORE_COMPONENT_CODES>
""".strip()

REPO_OVERVIEW_PROMPT = f"""
{_CUSTOM_INSTRUCTIONS_SECTION}{_GUIDELINES_SECTION}You are an AI documentation assistant. Your task is to generate a brief overview of the {{repo_name}} repository.

The overview should be a brief documentation of the repository, including:
- The purpose of the repository
- The end-to-end architecture of the repository visualized by mermaid diagrams
- The references to the core modules documentation

<MARKDOWN_RULES>
CRITICAL: Follow these rules to avoid validation errors:

1. **Code Blocks**: ALWAYS include language identifier (```bash, ```python, ```text)
2. **Shell Variables**: In prose text, ALWAYS wrap in backticks (`$HOME`, `$PATH`) - bare $VAR triggers LaTeX warnings
3. **Mermaid Diagrams**: Only use supported types (graph, flowchart, sequenceDiagram, classDiagram, etc.)
   - ❌ DO NOT use: pyramid, mindmap, timeline, quadrantChart
   - Node labels with spaces MUST use brackets: `A["User Service"]`
</MARKDOWN_RULES>

Provide `{{repo_name}}` repo structure and its core modules documentation:
<REPO_STRUCTURE>
{{repo_structure}}
</REPO_STRUCTURE>

CRITICAL RESPONSE FORMAT REQUIREMENT:
You MUST wrap your entire response in <OVERVIEW> and </OVERVIEW> tags.
Do NOT include any text before <OVERVIEW> or after </OVERVIEW>.
The response format is NON-NEGOTIABLE - failure to use these tags will cause a system error.

Generate the overview of the `{{repo_name}}` repository in markdown format:
<OVERVIEW>
[Your markdown overview content here]
</OVERVIEW>
""".strip()

MODULE_OVERVIEW_PROMPT = f"""
{_CUSTOM_INSTRUCTIONS_SECTION}{_GUIDELINES_SECTION}You are an AI documentation assistant. Your task is to generate a brief overview of `{{module_name}}` module.

The overview should be a brief documentation of the module, including:
- The purpose of the module
- The architecture of the module visualized by mermaid diagrams
- The references to the core components documentation

<MARKDOWN_RULES>
CRITICAL: Follow these rules to avoid validation errors:

1. **Code Blocks**: ALWAYS include language identifier (```bash, ```python, ```text)
2. **Shell Variables**: In prose text, ALWAYS wrap in backticks (`$HOME`, `$PATH`) - bare $VAR triggers LaTeX warnings
3. **Mermaid Diagrams**: Only use supported types (graph, flowchart, sequenceDiagram, classDiagram, etc.)
   - ❌ DO NOT use: pyramid, mindmap, timeline, quadrantChart
   - Node labels with spaces MUST use brackets: `A["User Service"]`
</MARKDOWN_RULES>

Provide repo structure and core components documentation of the `{{module_name}}` module:
<REPO_STRUCTURE>
{{repo_structure}}
</REPO_STRUCTURE>

CRITICAL RESPONSE FORMAT REQUIREMENT:
You MUST wrap your entire response in <OVERVIEW> and </OVERVIEW> tags.
Do NOT include any text before <OVERVIEW> or after </OVERVIEW>.
The response format is NON-NEGOTIABLE - failure to use these tags will cause a system error.

Generate the overview of the `{{module_name}}` module in markdown format:
<OVERVIEW>
[Your markdown overview content here]
</OVERVIEW>
""".strip()

CLUSTER_REPO_PROMPT = """
Here is list of all potential core components of the repository (It's normal that some components are not essential to the repository):
<POTENTIAL_CORE_COMPONENTS>
{potential_core_components}
</POTENTIAL_CORE_COMPONENTS>

**CRITICAL CONSTRAINTS:**
1. Component names MUST be actual class/function/interface names from the source code, NOT package or directory names
2. DO NOT invent component names based on directory structure (e.g., "core/audit/" → "audit_dtos" is INVALID)
3. Only use component names that appear in the actual source code above
4. Package/directory names are NOT valid component names
5. If you see a directory path like "core/device/", do NOT create components like "device_dtos" or "device_models"

**Invalid Examples (DO NOT USE):**
- ❌ "audit_dtos" (package name derived from "core/audit/" directory)
- ❌ "device_dtos" (package name derived from "core/device/" directory)
- ❌ "event_dtos" (package name derived from path structure)
- ❌ "core_models" (package name)

**Valid Examples (ONLY USE THESE):**
- ✅ "AuditEvent" (actual class name from source code)
- ✅ "DeviceInfo" (actual class name from source code)
- ✅ "EventProcessor" (actual class name from source code)
- ✅ "CoreModel" (actual class name from source code)

Please group the components into groups such that each group is a set of components that are closely related to each other and together they form a module. DO NOT include components that are not essential to the repository.

Return ONLY component names that exist in the source code above. DO NOT invent or derive component names from directory paths.

Firstly reason about the components and then group them and return the result in the following format:
<GROUPED_COMPONENTS>
{{
    "module_name_1": {{
        "path": <path_to_the_module_1>, # the path to the module can be file or directory
        "components": [
            <component_name_1>,
            <component_name_2>,
            ...
        ]
    }},
    "module_name_2": {{
        "path": <path_to_the_module_2>,
        "components": [
            <component_name_1>,
            <component_name_2>,
            ...
        ]
    }},
    ...
}}
</GROUPED_COMPONENTS>
""".strip()

CLUSTER_MODULE_PROMPT = """
Here is the module tree of a repository:

<MODULE_TREE>
{module_tree}
</MODULE_TREE>

Here is list of all potential core components of the module {module_name} (It's normal that some components are not essential to the module):
<POTENTIAL_CORE_COMPONENTS>
{potential_core_components}
</POTENTIAL_CORE_COMPONENTS>

**CRITICAL CONSTRAINTS:**
1. Component names MUST be actual class/function/interface names from the source code, NOT package or directory names
2. DO NOT invent component names based on directory structure (e.g., "core/audit/" → "audit_dtos" is INVALID)
3. Only use component names that appear in the actual source code above
4. Package/directory names are NOT valid component names
5. If you see a directory path like "core/device/", do NOT create components like "device_dtos" or "device_models"

**Invalid Examples (DO NOT USE):**
- ❌ "audit_dtos" (package name derived from "core/audit/" directory)
- ❌ "device_dtos" (package name derived from "core/device/" directory)
- ❌ "event_dtos" (package name derived from path structure)
- ❌ "core_models" (package name)

**Valid Examples (ONLY USE THESE):**
- ✅ "AuditEvent" (actual class name from source code)
- ✅ "DeviceInfo" (actual class name from source code)
- ✅ "EventProcessor" (actual class name from source code)
- ✅ "CoreModel" (actual class name from source code)

Please group the components into groups such that each group is a set of components that are closely related to each other and together they form a smaller module. DO NOT include components that are not essential to the module.

Return ONLY component names that exist in the source code above. DO NOT invent or derive component names from directory paths.

Firstly reason based on given context and then group them and return the result in the following format:
<GROUPED_COMPONENTS>
{{
    "module_name_1": {{
        "path": <path_to_the_module_1>, # the path to the module can be file or directory
        "components": [
            <component_name_1>,
            <component_name_2>,
            ...
        ]
    }},
    "module_name_2": {{
        "path": <path_to_the_module_2>,
        "components": [
            <component_name_1>,
            <component_name_2>,
            ...
        ]
    }},
    ...
}}
</GROUPED_COMPONENTS>
""".strip()

FILTER_FOLDERS_PROMPT = """
Here is the list of relative paths of files, folders in 2-depth of project {project_name}:
```
{files}
```

In order to analyze the core functionality of the project, we need to analyze the files, folders representing the core functionality of the project.

Please shortlist the files, folders representing the core functionality and ignore the files, folders that are not essential to the core functionality of the project (e.g. test files, documentation files, etc.) from the list above.

Reasoning at first, then return the list of relative paths in JSON format.
"""

from typing import Dict, Any
from codewiki.src.utils import file_manager

EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".md": "markdown",
    ".sh": "bash",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".tsx": "typescript",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".cs": "csharp",
    # Java ecosystem (from fork)
    ".xml": "xml",
    ".properties": "properties",
    ".gradle": "groovy",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".groovy": "groovy",
    # Other common types (from fork)
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".vue": "vue",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".phtml": "php",  # from upstream
    ".inc": "php",    # from upstream
    ".swift": "swift",
    ".scala": "scala",
    ".r": "r",
    ".R": "r",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "conf",
}


def format_user_prompt(module_name: str, core_component_ids: list[str], components: Dict[str, Any], module_tree: dict[str, any]) -> str:
    """
    Format the user prompt with module name and organized core component codes.

    Args:
        module_name: Name of the module to document
        core_component_ids: List of component IDs to include
        components: Dictionary mapping component IDs to CodeComponent objects

    Returns:
        Formatted user prompt string
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("📝 Prompt Assembly Stage - USER_PROMPT")
    logger.info(f"   ├─ Template: USER_PROMPT")
    logger.info(f"   ├─ Module name: {module_name}")
    logger.info(f"   ├─ Core component IDs: {len(core_component_ids)} components")
    logger.info(f"   │  └─ Components: {', '.join(core_component_ids[:5])}" +
                (f" ... and {len(core_component_ids) - 5} more" if len(core_component_ids) > 5 else ""))

    # format module tree
    lines = []

    def _format_module_tree(module_tree: dict[str, any], indent: int = 0):
        for key, value in module_tree.items():
            if key == module_name:
                lines.append(f"{'  ' * indent}{key} (current module)")
            else:
                lines.append(f"{'  ' * indent}{key}")

            lines.append(f"{'  ' * (indent + 1)} Core components: {', '.join(value.get('components', []))}")
            if ("children" in value) and isinstance(value["children"], dict) and len(value["children"]) > 0:
                lines.append(f"{'  ' * (indent + 1)} Children:")
                _format_module_tree(value["children"], indent + 2)

    _format_module_tree(module_tree, 0)
    formatted_module_tree = "\n".join(lines)

    logger.info(f"   ├─ Module tree context: {len(formatted_module_tree)} chars")
    logger.info(f"   │  └─ Preview: {formatted_module_tree[:100]}...")

    # print(f"Formatted module tree:\n{formatted_module_tree}")

    # Group core component IDs by their file path
    grouped_components: dict[str, list[str]] = {}
    for component_id in core_component_ids:
        if component_id not in components:
            continue
        component = components[component_id]
        path = component.relative_path
        if path not in grouped_components:
            grouped_components[path] = []
        grouped_components[path].append(component_id)

    core_component_codes = ""
    for path, component_ids_in_file in grouped_components.items():
        core_component_codes += f"# File: {path}\n\n"
        core_component_codes += f"## Core Components in this file:\n"
        
        for component_id in component_ids_in_file:
            core_component_codes += f"- {component_id}\n"
        
        # Get language from extension with fallback for unknown types
        file_ext = '.' + path.split('.')[-1] if '.' in path else ''
        language = EXTENSION_TO_LANGUAGE.get(file_ext, 'text')
        core_component_codes += f"\n## File Content:\n```{language}\n"
        
        # Read content of the file using the first component's file path
        if component_ids_in_file:
            try:
                core_component_codes += file_manager.load_text(components[component_ids_in_file[0]].file_path)
            except (FileNotFoundError, IOError) as e:
                core_component_codes += f"# Error reading file: {e}\n"
        else:
            core_component_codes += f"# No components found in this file\n"
        
        core_component_codes += "```\n\n"
        
    logger.info(f"   ├─ Core component codes: {len(core_component_codes)} chars")
    logger.info(f"   │  └─ Files included: {len(grouped_components)} files")

    # FIXED: Use manual string replacement instead of .format()
    # formatted_core_component_codes might contain code with curly braces (JSON, TypeScript, etc.)
    # which .format() tries to interpret as placeholders
    result = USER_PROMPT
    result = result.replace('{module_name}', module_name)
    result = result.replace('{formatted_core_component_codes}', core_component_codes)
    result = result.replace('{module_tree}', formatted_module_tree)

    logger.info(f"   ├─ Base USER_PROMPT length: {len(USER_PROMPT)} chars")
    logger.info(f"   ├─ Total assembled prompt: {len(result)} chars (~{len(result) // 4} tokens)")
    logger.info(f"   └─ ✅ Prompt ready for LLM invocation")

    return result



def format_cluster_prompt(potential_core_components: str, module_tree: dict[str, any] = {}, module_name: str = None) -> str:
    """
    Format the cluster prompt with potential core components and module tree.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Determine which template we're using
    is_repo_level = module_tree == {}
    template_name = "CLUSTER_REPO_PROMPT" if is_repo_level else "CLUSTER_MODULE_PROMPT"

    logger.info(f"📝 Prompt Assembly Stage - {template_name}")
    logger.info(f"   ├─ Template: {template_name}")
    if module_name:
        logger.info(f"   ├─ Module name: {module_name}")
    logger.info(f"   ├─ Potential core components: {len(potential_core_components)} chars")
    logger.info(f"   │  └─ Preview: {potential_core_components[:100]}...")

    # format module tree
    lines = []

    # print(f"Module tree:\n{json.dumps(module_tree, indent=2)}")

    def _format_module_tree(module_tree: dict[str, any], indent: int = 0):
        for key, value in module_tree.items():
            if key == module_name:
                lines.append(f"{'  ' * indent}{key} (current module)")
            else:
                lines.append(f"{'  ' * indent}{key}")

            lines.append(f"{'  ' * (indent + 1)} Core components: {', '.join(value.get('components', []))}")
            if ("children" in value) and isinstance(value["children"], dict) and len(value["children"]) > 0:
                lines.append(f"{'  ' * (indent + 1)} Children:")
                _format_module_tree(value["children"], indent + 2)

    _format_module_tree(module_tree, 0)
    formatted_module_tree = "\n".join(lines)

    if not is_repo_level:
        logger.info(f"   ├─ Module tree context: {len(formatted_module_tree)} chars")
        logger.info(f"   │  └─ Preview: {formatted_module_tree[:100]}...")

    # FIXED: Use manual string replacement instead of .format()
    # potential_core_components might contain code with curly braces
    if module_tree == {}:
        result = CLUSTER_REPO_PROMPT
        result = result.replace('{potential_core_components}', potential_core_components)
        logger.info(f"   ├─ Base CLUSTER_REPO_PROMPT length: {len(CLUSTER_REPO_PROMPT)} chars")
    else:
        result = CLUSTER_MODULE_PROMPT
        result = result.replace('{potential_core_components}', potential_core_components)
        result = result.replace('{module_tree}', formatted_module_tree)
        result = result.replace('{module_name}', module_name)
        logger.info(f"   ├─ Base CLUSTER_MODULE_PROMPT length: {len(CLUSTER_MODULE_PROMPT)} chars")

    logger.info(f"   ├─ Total assembled prompt: {len(result)} chars (~{len(result) // 4} tokens)")
    logger.info(f"   └─ ✅ Prompt ready for LLM invocation")

    return result


def format_system_prompt(module_name: str, custom_instructions: str = None) -> str:
    """
    Format the system prompt with module name and optional custom instructions.

    Args:
        module_name: Name of the module to document
        custom_instructions: Optional custom instructions to append (combined string from config.get_prompt_addition())

    Returns:
        Formatted system prompt string
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("📝 Prompt Assembly Stage - SYSTEM_PROMPT (complex modules)")
    logger.info(f"   ├─ Template: SYSTEM_PROMPT (complex modules)")
    logger.info(f"   ├─ Module name: {module_name}")

    custom_section = ""
    if custom_instructions and custom_instructions.strip():
        # NOTE: Braces already escaped in config.py:151 via escape_format_braces()
        # F-strings do NOT process braces in substituted variables, so no double-escape needed.
        # See flamingo_guidelines.py:64-73 for the escape strategy explanation.
        custom_section = f"\n\n<CUSTOM_INSTRUCTIONS>\n{custom_instructions}\n</CUSTOM_INSTRUCTIONS>"
        logger.info(f"   ├─ Runtime custom instructions: {len(custom_instructions)} chars")
        logger.info(f"   │  └─ Preview: {custom_instructions[:100]}...")
    else:
        logger.info(f"   ├─ Runtime custom instructions: None")

    # Log injected sections from flamingo_guidelines
    logger.info(f"   ├─ Flamingo custom instructions section: {len(_CUSTOM_INSTRUCTIONS_SECTION)} chars")
    if _CUSTOM_INSTRUCTIONS_SECTION:
        logger.info(f"   │  └─ Preview: {_CUSTOM_INSTRUCTIONS_SECTION[:100]}...")
    logger.info(f"   ├─ Flamingo guidelines section: {len(_GUIDELINES_SECTION)} chars")
    if _GUIDELINES_SECTION:
        logger.info(f"   │  └─ Preview: {_GUIDELINES_SECTION[:100]}...")

    # FIXED: Use manual string replacement instead of .format()
    # This avoids ALL .format() complexity with curly braces in guidelines content
    # .format() tries to interpret ANY {text} pattern, causing KeyError/IndexError
    # Manual replacement only replaces EXACT placeholder strings, leaving all other braces untouched
    result = SYSTEM_PROMPT
    result = result.replace('{module_name}', module_name)
    result = result.replace('{custom_instructions}', custom_section)

    logger.info(f"   ├─ Base system prompt length: {len(SYSTEM_PROMPT)} chars")
    logger.info(f"   ├─ Total assembled prompt: {len(result)} chars (~{len(result) // 4} tokens)")
    logger.info(f"   └─ ✅ Prompt ready for LLM invocation")

    return result.strip()


def format_leaf_system_prompt(module_name: str, custom_instructions: str = None) -> str:
    """
    Format the leaf system prompt with module name and optional custom instructions.

    Args:
        module_name: Name of the module to document
        custom_instructions: Optional custom instructions to append (combined string from config.get_prompt_addition())

    Returns:
        Formatted leaf system prompt string
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("📝 Prompt Assembly Stage - LEAF_SYSTEM_PROMPT")
    logger.info(f"   ├─ Template: LEAF_SYSTEM_PROMPT (leaf modules)")
    logger.info(f"   ├─ Module name: {module_name}")

    custom_section = ""
    if custom_instructions and custom_instructions.strip():
        # NOTE: Braces already escaped in config.py:151 via escape_format_braces()
        # F-strings do NOT process braces in substituted variables, so no double-escape needed.
        # See flamingo_guidelines.py:64-73 for the escape strategy explanation.
        custom_section = f"\n\n<CUSTOM_INSTRUCTIONS>\n{custom_instructions}\n</CUSTOM_INSTRUCTIONS>"
        logger.info(f"   ├─ Runtime custom instructions: {len(custom_instructions)} chars")
        logger.info(f"   │  └─ Preview: {custom_instructions[:100]}...")
    else:
        logger.info(f"   ├─ Runtime custom instructions: None")

    # Log injected sections from flamingo_guidelines
    logger.info(f"   ├─ Flamingo custom instructions section: {len(_CUSTOM_INSTRUCTIONS_SECTION)} chars")
    if _CUSTOM_INSTRUCTIONS_SECTION:
        logger.info(f"   │  └─ Preview: {_CUSTOM_INSTRUCTIONS_SECTION[:100]}...")
    logger.info(f"   ├─ Flamingo guidelines section: {len(_GUIDELINES_SECTION)} chars")
    if _GUIDELINES_SECTION:
        logger.info(f"   │  └─ Preview: {_GUIDELINES_SECTION[:100]}...")

    # FIXED: Use manual string replacement instead of .format()
    # This avoids ALL .format() complexity with curly braces in guidelines content
    # .format() tries to interpret ANY {text} pattern, causing KeyError/IndexError
    # Manual replacement only replaces EXACT placeholder strings, leaving all other braces untouched
    result = LEAF_SYSTEM_PROMPT
    result = result.replace('{module_name}', module_name)
    result = result.replace('{custom_instructions}', custom_section)

    logger.info(f"   ├─ Base system prompt length: {len(LEAF_SYSTEM_PROMPT)} chars")
    logger.info(f"   ├─ Total assembled prompt: {len(result)} chars (~{len(result) // 4} tokens)")
    logger.info(f"   └─ ✅ Prompt ready for LLM invocation")

    return result.strip()


def format_repo_overview_prompt(repo_name: str, repo_structure: str) -> str:
    """
    Format the repository overview prompt with repo name and structure.

    Args:
        repo_name: Name of the repository
        repo_structure: JSON string of repository structure (contains curly braces)

    Returns:
        Formatted repository overview prompt string
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("📝 Prompt Assembly Stage - REPO_OVERVIEW_PROMPT")
    logger.info(f"   ├─ Template: REPO_OVERVIEW_PROMPT")
    logger.info(f"   ├─ Repository name: {repo_name}")
    logger.info(f"   ├─ Repository structure: {len(repo_structure)} chars")
    logger.info(f"   │  └─ Preview: {repo_structure[:100]}...")

    # Log injected sections from flamingo_guidelines
    logger.info(f"   ├─ Flamingo custom instructions section: {len(_CUSTOM_INSTRUCTIONS_SECTION)} chars")
    logger.info(f"   ├─ Flamingo guidelines section: {len(_GUIDELINES_SECTION)} chars")

    # FIXED: Use manual string replacement instead of .format()
    # repo_structure is JSON which contains lots of curly braces
    # .format() would try to interpret these as placeholders
    result = REPO_OVERVIEW_PROMPT
    result = result.replace('{repo_name}', repo_name)
    result = result.replace('{repo_structure}', repo_structure)

    logger.info(f"   ├─ Base REPO_OVERVIEW_PROMPT length: {len(REPO_OVERVIEW_PROMPT)} chars")
    logger.info(f"   ├─ Total assembled prompt: {len(result)} chars (~{len(result) // 4} tokens)")
    logger.info(f"   └─ ✅ Prompt ready for LLM invocation")

    return result


def format_module_overview_prompt(module_name: str, repo_structure: str) -> str:
    """
    Format the module overview prompt with module name and structure.

    Args:
        module_name: Name of the module
        repo_structure: JSON string of repository structure (contains curly braces)

    Returns:
        Formatted module overview prompt string
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("📝 Prompt Assembly Stage - MODULE_OVERVIEW_PROMPT")
    logger.info(f"   ├─ Template: MODULE_OVERVIEW_PROMPT")
    logger.info(f"   ├─ Module name: {module_name}")
    logger.info(f"   ├─ Repository structure: {len(repo_structure)} chars")
    logger.info(f"   │  └─ Preview: {repo_structure[:100]}...")

    # Log injected sections from flamingo_guidelines
    logger.info(f"   ├─ Flamingo custom instructions section: {len(_CUSTOM_INSTRUCTIONS_SECTION)} chars")
    logger.info(f"   ├─ Flamingo guidelines section: {len(_GUIDELINES_SECTION)} chars")

    # FIXED: Use manual string replacement instead of .format()
    # repo_structure is JSON which contains lots of curly braces
    # .format() would try to interpret these as placeholders
    result = MODULE_OVERVIEW_PROMPT
    result = result.replace('{module_name}', module_name)
    result = result.replace('{repo_structure}', repo_structure)

    logger.info(f"   ├─ Base MODULE_OVERVIEW_PROMPT length: {len(MODULE_OVERVIEW_PROMPT)} chars")
    logger.info(f"   ├─ Total assembled prompt: {len(result)} chars (~{len(result) // 4} tokens)")
    logger.info(f"   └─ ✅ Prompt ready for LLM invocation")

    return result