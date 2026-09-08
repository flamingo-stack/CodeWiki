# CodeWiki Documentation

Welcome to the documentation for **CodeWiki** — an AI-powered documentation generator for source code repositories.

## 📚 Table of Contents

### Getting Started

New to CodeWiki? Start here:

- [Introduction](./getting-started/introduction.md) — What CodeWiki is, key features, and target audience
- [Prerequisites](./getting-started/prerequisites.md) — Required software, versions, and environment setup
- [Quick Start](./getting-started/quick-start.md) — Install CodeWiki and generate your first documentation set in ~5 minutes
- [First Steps](./getting-started/first-steps.md) — Customizing generation, tuning token budgets, and the Git/GitHub Pages workflow

### Development

Contributing to CodeWiki itself:

- [Development Overview](./development/README.md) — Quick navigation for developing, testing, and contributing
- [Environment Setup](./development/setup/environment.md) — IDE recommendations, required tools, and dev environment variables
- [Local Development](./development/setup/local-development.md) — Cloning the repo, editable installs, and running the CLI or web app locally
- [Architecture Overview](./development/architecture/README.md) — High-level module architecture, core components, and data flow

### Reference

Technical reference documentation generated from source-code analysis:

- [Reference Overview](./reference/architecture/README.md) — End-to-end architecture, module relationships, and summary
- [CLI Core](./reference/architecture/cli-core/cli-core.md) — Command-line orchestration, local config, Git integration, HTML generation
- [Backend Core](./reference/architecture/backend-core/backend-core.md) — Repository analysis, dependency graphs, module clustering, LLM agent orchestration
- [Frontend Core](./reference/architecture/frontend-core/frontend-core.md) — FastAPI web application, job processing, caching, doc serving
- [Config Core](./reference/architecture/config-core/config-core.md) — Shared runtime `Config` model for paths, provider settings, and agent instructions
- [Test Multi Path](./reference/architecture/test-multi-path/test-multi-path.md) — Fixtures and checks for multi-root source analysis
- [Test Clustering](./reference/architecture/test-clustering/test-clustering.md) — Diagnostic and validation scripts for LLM-based module clustering

#### Backend Core Subsystems

- [Agent Tools Core](./reference/architecture/backend-core/agent-tools-core/agent-tools-core.md) — Controlled repository inspection and documentation editing tools
- [Dependency Analyzer Core](./reference/architecture/backend-core/dependency-analyzer-core/dependency-analyzer-core.md) — File discovery, AST parsing, call analysis, and graph construction
  - [Graph Construction](./reference/architecture/backend-core/dependency-analyzer-core/graph_construction.md)
  - [Analysis Pipeline](./reference/architecture/backend-core/dependency-analyzer-core/analysis_pipeline.md)
- [Tree Sitter Analyzers](./reference/architecture/backend-core/tree-sitter-analyzers/tree-sitter-analyzers.md) — Language support for C, C++, C#, Java, JavaScript, TypeScript, PHP, and Python
  - [Python Analyzer](./reference/architecture/backend-core/tree-sitter-analyzers/python_analyzer.md)
  - [PHP Analyzer](./reference/architecture/backend-core/tree-sitter-analyzers/php_analyzer.md)
  - [JavaScript/TypeScript Analyzers](./reference/architecture/backend-core/tree-sitter-analyzers/javascript_typescript_analyzers.md)
  - [Java Analyzer](./reference/architecture/backend-core/tree-sitter-analyzers/java_analyzer.md)
  - [C-Family Analyzers](./reference/architecture/backend-core/tree-sitter-analyzers/c_family_analyzers.md)
- [Dependency Analyzer Models](./reference/architecture/backend-core/dependency-analyzer-models/dependency-analyzer-models.md) — Repository, node, relationship, and analysis-result contracts
- [Documentation Generator](./reference/architecture/backend-core/documentation-generator/documentation-generator.md) — Top-level pipeline coordination and documentation output
- [LLM Services](./reference/architecture/backend-core/llm-services/llm-services.md) — Model selection, request counting, and fallback handling
- [Logging Config](./reference/architecture/backend-core/logging-config/logging-config.md) — Shared colorized logging support

#### CLI Core Subsystems

- [Generation](./reference/architecture/cli-core/generation.md) — CLI adapter for staged documentation generation
- [Configuration](./reference/architecture/cli-core/configuration.md) — Persisted settings, keyring-backed credentials, and agent instructions
- [Job Models](./reference/architecture/cli-core/job_models.md) — Generation job status, statistics, and LLM configuration models
- [Git Integration](./reference/architecture/cli-core/git_integration.md) — Clean-tree checks, branch creation, commits, and remote URL handling
- [HTML Generation](./reference/architecture/cli-core/html_generation.md) — Static documentation viewer generation

#### Test Fixtures Reference

- [Test Suites](./reference/architecture/test-multi-path/test_suites.md)
- [Sample Fixtures](./reference/architecture/test-multi-path/sample_fixtures.md)

### Diagrams

Visual documentation — Mermaid architecture diagrams generated from source-code analysis are available in:

- `./diagrams/architecture/` — includes diagrams for the CLI, backend, frontend, config core, dependency analyzers, and test modules

## 📖 Quick Links

- [Project README](../README.md) — Main project README
- [Contributing](../CONTRIBUTING.md) — How to contribute
- [License](../LICENSE.md) — License information

## 💬 Community

CodeWiki does not use GitHub Issues or Discussions. For questions and discussion, join the OpenMSP Slack community: [https://www.openmsp.ai/](https://www.openmsp.ai/) ([join link](https://join.slack.com/t/openmsp/shared_invite/zt-36bl7mx0h-3~U2nFH6nqHqoTPXMaHEHA)).

---
*Documentation generated by [🦩 Flamingo Code Documentation](https://flamingo.run)*
