#!/usr/bin/env python3
"""Debug script to check if parser finds files."""

import sys
import os
from pathlib import Path

# Add CodeWiki to path
CODEWIKI_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CODEWIKI_ROOT))

from codewiki.src.be.dependency_analyzer.ast_parser import DependencyParser

# Test paths
main_path = Path(__file__).parent / "main"
deps_path = Path(__file__).parent / "deps"

print(f"Main path: {main_path}")
print(f"Deps path: {deps_path}")
print(f"Main exists: {main_path.exists()}")
print(f"Deps exists: {deps_path.exists()}")

print("\nFiles in main:")
for f in main_path.glob("*.py"):
    print(f"  - {f.name}")

print("\nFiles in deps:")
for f in deps_path.glob("*.py"):
    print(f"  - {f.name}")

print("\n" + "="*70)
print("Testing single path parser...")
print("="*70)

parser_single = DependencyParser(str(main_path))
components_single = parser_single.parse_repository()
print(f"\nSingle path found {len(components_single)} components")
for comp_id, comp in list(components_single.items())[:5]:
    print(f"  - {comp_id}: {comp.component_type}")

print("\n" + "="*70)
print("Testing multi-path parser...")
print("="*70)

parser_multi = DependencyParser([str(main_path), str(deps_path)])
components_multi = parser_multi.parse_repository()
print(f"\nMulti-path found {len(components_multi)} components")
for comp_id, comp in list(components_multi.items())[:10]:
    print(f"  - {comp_id}: {comp.component_type}")
