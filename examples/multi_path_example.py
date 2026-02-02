#!/usr/bin/env python3
"""
Example: Multi-Path Repository Analysis

This script demonstrates how to use DependencyParser and RepoAnalyzer
with multiple source directories.
"""

import sys
import os

# Add CodeWiki to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from codewiki.src.be.dependency_analyzer.ast_parser import DependencyParser
from codewiki.src.be.dependency_analyzer.analysis.repo_analyzer import RepoAnalyzer


def example_single_path():
    """Example: Single path (backward compatible)."""
    print("=" * 60)
    print("EXAMPLE 1: Single Path (Backward Compatible)")
    print("=" * 60)

    # Works exactly as before
    parser = DependencyParser(
        "/path/to/my-project",
        include_patterns=["*.py", "*.ts"],
        exclude_patterns=["*test*"]
    )

    components = parser.parse_repository()

    print(f"Found {len(components)} components")
    print("\nSample component IDs:")
    for comp_id in list(components.keys())[:5]:
        print(f"  - {comp_id}")


def example_multiple_paths():
    """Example: Multiple paths with namespacing."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Multiple Paths with Namespacing")
    print("=" * 60)

    # Define multiple repositories to analyze
    repositories = [
        "/path/to/openframe-frontend",
        "/path/to/ui-kit",
        "/path/to/shared-libraries"
    ]

    # Create parser with multiple paths
    parser = DependencyParser(
        repositories,
        include_patterns=["*.py", "*.ts", "*.tsx"],
        exclude_patterns=["*test*", "*spec*", "node_modules/*"]
    )

    # Parse all repositories
    components = parser.parse_repository()

    print(f"\nTotal components: {len(components)}")
    print(f"Total modules: {len(parser.modules)}")

    # Group by namespace
    namespaces = {}
    for comp_id, component in components.items():
        namespace = comp_id.split('.')[0]
        if namespace not in namespaces:
            namespaces[namespace] = []
        namespaces[namespace].append(comp_id)

    print("\nComponents by namespace:")
    for namespace, comp_list in namespaces.items():
        print(f"  {namespace}: {len(comp_list)} components")

    # Show sample namespaced component IDs
    print("\nSample namespaced component IDs:")
    for comp_id in list(components.keys())[:10]:
        print(f"  - {comp_id}")

    # Show cross-namespace dependencies
    print("\nCross-namespace dependencies:")
    for comp_id, component in list(components.items())[:50]:
        comp_namespace = comp_id.split('.')[0]
        cross_deps = [
            dep for dep in component.depends_on
            if dep.split('.')[0] != comp_namespace
        ]
        if cross_deps:
            print(f"  {comp_id} depends on:")
            for dep in cross_deps[:3]:  # Show first 3
                print(f"    → {dep}")
            if len(cross_deps) > 3:
                print(f"    ... and {len(cross_deps) - 3} more")
            break  # Just show first example


def example_repo_analyzer_multi_path():
    """Example: RepoAnalyzer with multiple paths."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: RepoAnalyzer with Multiple Paths")
    print("=" * 60)

    repositories = [
        "/path/to/frontend",
        "/path/to/backend",
        "/path/to/shared"
    ]

    analyzer = RepoAnalyzer(
        include_patterns=["*.py", "*.ts"],
        exclude_patterns=["*test*", "build/*", "dist/*"]
    )

    result = analyzer.analyze_repository_structure(repositories)

    # Display summary
    summary = result["summary"]
    print(f"\nSummary:")
    print(f"  Total files: {summary['total_files']}")
    print(f"  Total size: {summary['total_size_kb']:.2f} KB")
    print(f"  Repositories: {summary['repositories']}")
    print(f"  Namespaces: {', '.join(summary['namespaces'])}")

    # Show file tree structure
    print("\nFile tree structure (top level):")
    file_tree = result["file_tree"]
    for child in file_tree.get("children", [])[:3]:
        namespace = child.get("_namespace", "unknown")
        num_children = len(child.get("children", []))
        print(f"  📁 {namespace}/ ({num_children} items)")


def example_component_details():
    """Example: Accessing component details in multi-path mode."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Component Details in Multi-Path Mode")
    print("=" * 60)

    parser = DependencyParser([
        "/path/to/project-a",
        "/path/to/project-b"
    ])

    components = parser.parse_repository()

    # Find components from each namespace
    for namespace in ["project-a", "project-b"]:
        namespace_components = {
            comp_id: comp for comp_id, comp in components.items()
            if comp_id.startswith(f"{namespace}.")
        }

        if namespace_components:
            print(f"\n{namespace} components:")
            sample_id = list(namespace_components.keys())[0]
            sample_comp = namespace_components[sample_id]

            print(f"  Sample: {sample_id}")
            print(f"    Name: {sample_comp.name}")
            print(f"    Type: {sample_comp.component_type}")
            print(f"    File: {sample_comp.relative_path}")
            print(f"    Lines: {sample_comp.start_line}-{sample_comp.end_line}")
            print(f"    Dependencies: {len(sample_comp.depends_on)}")


def example_saving_output():
    """Example: Saving multi-path analysis to JSON."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Saving Multi-Path Analysis")
    print("=" * 60)

    parser = DependencyParser([
        "/path/to/repo1",
        "/path/to/repo2"
    ])

    components = parser.parse_repository()

    # Save to JSON file
    output_path = "/tmp/multi_path_analysis.json"
    parser.save_dependency_graph(output_path)

    print(f"\nSaved {len(components)} components to:")
    print(f"  {output_path}")
    print("\nJSON structure includes:")
    print("  - Namespaced component IDs")
    print("  - Cross-namespace dependencies")
    print("  - Original file paths preserved")
    print("  - Complete component metadata")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Multi-Path Repository Analysis Examples" + " " * 8 + "║")
    print("╚" + "=" * 58 + "╝")

    try:
        # Note: These examples use placeholder paths
        # Replace with actual repository paths to run

        print("\nNOTE: Examples use placeholder paths.")
        print("Replace with actual paths to execute.\n")

        # Uncomment to run examples:
        # example_single_path()
        # example_multiple_paths()
        # example_repo_analyzer_multi_path()
        # example_component_details()
        # example_saving_output()

        print("\n✅ Examples ready to run (update paths first)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
