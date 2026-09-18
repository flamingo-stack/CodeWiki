# CodeWiki Documentation

Welcome to the documentation for **CodeWiki** — an AI-assisted documentation generator that analyzes source repositories, builds dependency graphs, clusters components into logical modules, and uses LLM-backed agents to produce hierarchical Markdown documentation.

## 📚 Table of Contents

### Getting Started

New to CodeWiki? Start here:

- [Introduction](./getting-started/introduction.md) — What CodeWiki is, key features, and target audience
- [Prerequisites](./getting-started/prerequisites.md) — Required software, accounts, and environment variables
- [Quick Start](./getting-started/quick-start.md) — Run the CLI locally or the web app via Docker Compose, and generate your first documentation set
- [First Steps](./getting-started/first-steps.md) — What to explore and configure after your first successful run

### Development

Guides for developing, extending, and contributing to CodeWiki:

- [Development Overview](./development/README.md) — Index of all development documentation
- [Environment Setup](./development/setup/environment.md) — IDE recommendations, required tools, and environment variables
- [Local Development](./development/setup/local-development.md) — Running the CLI and web app from source, hot reload, and debugging
- [Architecture Overview](./development/architecture/README.md) — How CodeWiki's modules fit together and data flow
- [Security Best Practices](./development/security/README.md) — Secret handling, credential storage, and input validation patterns

### Reference

Technical reference documentation generated directly from source code analysis:

**Top-Level Overview**
- [Repository Overview](./reference/architecture/README.md) — End-to-end architecture, generation lifecycle, and module relationships
- [Ecosystem](./reference/architecture/ecosystem.md) — Repository graph and dependency ecosystem

**CLI Core** (`codewiki/cli`) — Terminal workflow, configuration, generation pipeline
- [CLI Core Overview](./reference/architecture/cli-core/cli-core.md)
- [Configuration Management](./reference/architecture/cli-core/configuration_management.md)
- [Job and Generation Models](./reference/architecture/cli-core/job_and_generation_models.md)
- [Generation Pipeline](./reference/architecture/cli-core/generation_pipeline.md)
- [CLI Utilities](./reference/architecture/cli-core/cli_utilities.md)

**Backend Core** (`codewiki/src/be`) — Dependency analysis, clustering, LLM-driven generation
- [Backend Core Overview](./reference/architecture/backend-core/backend-core.md)
- [Documentation and Services](./reference/architecture/backend-core/documentation-and-services/documentation-and-services.md)
- [Agent Orchestration and Tools](./reference/architecture/backend-core/agent-orchestration-and-tools/agent-orchestration-and-tools.md)
- Dependency Analysis:
  - [Dependency Analysis Overview](./reference/architecture/backend-core/dependency-analysis/dependency-analysis.md)
  - [Repository and Call Graph Analysis](./reference/architecture/backend-core/dependency-analysis/repository_and_call_graph_analysis.md)
  - [Language Analyzers](./reference/architecture/backend-core/dependency-analysis/language_analyzers.md)
  - [Python Analyzer](./reference/architecture/backend-core/dependency-analysis/python_analyzer.md)
  - [PHP Analyzer](./reference/architecture/backend-core/dependency-analysis/php_analyzer.md)
  - [Java Analyzer](./reference/architecture/backend-core/dependency-analysis/java_analyzer.md)
  - [C-Family Analyzers](./reference/architecture/backend-core/dependency-analysis/c_family_analyzers.md)
  - [Web Scripting Analyzers](./reference/architecture/backend-core/dependency-analysis/web_scripting_analyzers.md)
  - [Dependency Graph Construction](./reference/architecture/backend-core/dependency-analysis/dependency_graph_construction.md)
  - [Data Models and Utilities](./reference/architecture/backend-core/dependency-analysis/data_models_and_utilities.md)

**Frontend Core** (`codewiki/src/fe`) — FastAPI web application
- [Frontend Core Overview](./reference/architecture/frontend-core/frontend-core.md)
- [Request Handling](./reference/architecture/frontend-core/request_handling.md)
- [Job Processing](./reference/architecture/frontend-core/job_processing.md)
- [GitHub Integration](./reference/architecture/frontend-core/github_integration.md)
- [Configuration and Data Models](./reference/architecture/frontend-core/configuration_and_data_models.md)

**Config Core** (`codewiki/src/config.py`) — Shared runtime configuration
- [Config Core Overview](./reference/architecture/config-core/config-core.md)

**Test Multi Path Core** (`test-multi-path`) — Multi-source-path analysis validation
- [Test Multi Path Core Overview](./reference/architecture/test-multi-path-core/test-multi-path-core.md)
- [Test Fixtures](./reference/architecture/test-multi-path-core/test_fixtures.md)
- [Test Runners](./reference/architecture/test-multi-path-core/test_runners.md)

**Test Clustering Core** (`test_clustering`) — Module clustering validation
- [Test Clustering Core Overview](./reference/architecture/test-clustering-core/test-clustering-core.md)
- [Live Clustering Tests](./reference/architecture/test-clustering-core/live_clustering_tests.md)
- [Validation and Logic Tests](./reference/architecture/test-clustering-core/validation_and_logic_tests.md)

### Diagrams

Visual architecture documentation is available as Mermaid diagram source files:

- Browse diagram files under `./diagrams/architecture/` — includes flowcharts and sequence diagrams for the backend, frontend, CLI, config, dependency-analysis, and test modules covered in the Reference section above.

## 📖 Quick Links

- [Project README](../README.md) — Main project README
- [Contributing](../CONTRIBUTING.md) — How to contribute
- [License](../LICENSE.md) — License information

---
*Documentation generated by [🦩 Flamingo Code Documentation](https://flamingo.run)*
