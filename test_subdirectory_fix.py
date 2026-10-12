#!/usr/bin/env python3
"""
Test to verify that ALL modules now create subdirectories.
"""

import os
import sys

# Add CodeWiki to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from codewiki.src.be.documentation_generator import DocumentationGenerator
from codewiki.src.config import Config


class TestResults:
    def __init__(self):
        self.tests = []

    def add_test(self, name, passed, details=None):
        self.tests.append({"name": name, "passed": passed, "details": details})

    def print_summary(self):
        print("\n" + "=" * 80)
        all_passed = all(t["passed"] for t in self.tests)
        for t in self.tests:
            status = "✅ PASS" if t["passed"] else "❌ FAIL"
            print(f"{status}: {t['name']}")
        if all_passed:
            print("\n✅✅✅ ALL TESTS PASSED ✅✅✅")
            print("\n🎉 The fix works! Root-level modules now create subdirectories!")
            print("\nExample structure:")
            print("   docs/reference/architecture/")
            print("   ├── gateway_service_core/")
            print("   │   └── gateway_service_core.md")
            print("   ├── api_endpoints/")
            print("   │   └── api_endpoints.md")
            print("   └── Backend/")
            print("       └── Authentication/")
            print("           └── JWT/")
            print("               └── JWT.md")
        else:
            print("\n❌ SOME TESTS FAILED")
        return all_passed


# Create minimal config
config = Config(
    cluster_api_key=os.getenv("CLUSTER_API_KEY", os.getenv("OPENAI_API_KEY", "")),
    main_api_key=os.getenv("MAIN_API_KEY", os.getenv("OPENAI_API_KEY", "")),
    fallback_api_key=os.getenv("FALLBACK_API_KEY", os.getenv("ANTHROPIC_API_KEY", "")),
    repo_path="/tmp/test",
    output_dir="/tmp/test_output",
    dependency_graph_dir="/tmp/test_output/deps",
    docs_dir="/tmp/test_output/docs",
    max_depth=2,
    main_model="gpt-4o",
    cluster_model="gpt-4o",
    fallback_model="claude-opus-4-5-20251101",
    cluster_base_url="https://api.openai.com/v1",
    main_base_url="https://api.openai.com/v1",
    fallback_base_url="https://api.anthropic.com/v1"
)

# Create generator instance
generator = DocumentationGenerator(config)

# Test cases
base_dir = "/tmp/test_docs"
test_cases = [
    {
        "name": "Root-level module",
        "module_path": ["gateway_service_core"],
        "expected": "/tmp/test_docs/gateway_service_core"
    },
    {
        "name": "Single nested module",
        "module_path": ["Backend", "Authentication"],
        "expected": "/tmp/test_docs/Backend/Authentication"
    },
    {
        "name": "Deep nested module",
        "module_path": ["Backend", "Authentication", "JWT"],
        "expected": "/tmp/test_docs/Backend/Authentication/JWT"
    },
    {
        "name": "Empty path (repository overview)",
        "module_path": [],
        "expected": "/tmp/test_docs"
    }
]

print("Testing subdirectory creation logic...")
print("=" * 80)

results = TestResults()
for test in test_cases:
    result = generator._get_nested_working_dir(base_dir, test["module_path"])
    expected = os.path.abspath(test["expected"])
    passed = result == expected

    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}: {test['name']}")
    print(f"   Module path: {test['module_path']}")
    print(f"   Expected:    {expected}")
    print(f"   Got:         {result}")

    results.add_test(
        test["name"],
        passed,
        {"module_path": test["module_path"], "expected": expected, "got": result}
    )

all_passed = results.print_summary()
sys.exit(0 if all_passed else 1)
