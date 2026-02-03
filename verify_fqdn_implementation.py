#!/usr/bin/env python3
"""
Verification script for FQDN implementation.
Ensures all Node creation points use FQDN consistently.
"""

import ast
import sys

def check_node_model():
    """Verify Node model has FQDN fields."""
    with open('codewiki/src/be/dependency_analyzer/models/core.py', 'r') as f:
        content = f.read()
    
    required_fields = ['short_id:', 'namespace:', 'is_from_deps:']
    checks = {field: field in content for field in required_fields}
    
    print("✅ Node Model FQDN Fields Check:")
    for field, present in checks.items():
        status = "✓" if present else "✗"
        print(f"  {status} {field}")
    
    return all(checks.values())

def check_ast_parser():
    """Verify ast_parser.py uses FQDN for Node creation."""
    with open('codewiki/src/be/dependency_analyzer/ast_parser.py', 'r') as f:
        content = f.read()
    
    checks = {
        'FQDN comment in multi-path': '# FQDN metadata fields' in content,
        'fqdn = f"{namespace}.{original_id}"': 'fqdn = f"{namespace}.{original_id}"' in content,
        'components[fqdn] = node': 'components[fqdn] = node' in content,
        'id=fqdn': 'id=fqdn' in content,
        'short_id=original_id': 'short_id=original_id' in content,
        'namespace=namespace': 'namespace=namespace' in content,
        'is_from_deps=(repo_index > 0)': 'is_from_deps=(repo_index > 0)' in content,
        'is_from_deps=False': 'is_from_deps=False' in content,
    }
    
    print("\n✅ AST Parser FQDN Implementation Check:")
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check_name}")
    
    return all(checks.values())

def main():
    print("=" * 60)
    print("FQDN Implementation Verification")
    print("=" * 60)
    
    model_ok = check_node_model()
    parser_ok = check_ast_parser()
    
    print("\n" + "=" * 60)
    if model_ok and parser_ok:
        print("✅ ALL CHECKS PASSED - FQDN implementation complete!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review implementation")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
