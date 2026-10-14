#!/usr/bin/env python3
"""
REAL clustering test - enough components to trigger LLM call.
"""

import os, sys, logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', force=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

from codewiki.src.be.cluster_modules import cluster_modules
from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.config import Config


class TestResults:
    def __init__(self):
        self.tests = []

    def add_test(self, name, passed, message=""):
        self.tests.append((name, passed, message))

    def print_summary(self):
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        passed_count = 0
        for name, passed, message in self.tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {name}" + (f": {message}" if message else ""))
            if passed:
                passed_count += 1
        total = len(self.tests)
        print("-" * 80)
        print(f"Total: {passed_count}/{total} passed")
        print("=" * 80)
        return passed_count == total


results = TestResults()

test_repo = os.getenv("TEST_REPO_PATH", os.path.dirname(os.path.abspath(__file__)))

config = Config(
    repo_path=test_repo, output_dir="/tmp/test", dependency_graph_dir="/tmp/test/deps",
    docs_dir="/tmp/test/docs", max_depth=2,
    main_model=os.getenv("MAIN_MODEL", "gpt-4o"),
    cluster_model=os.getenv("CLUSTER_MODEL", "gpt-4o"),
    fallback_model=os.getenv("FALLBACK_MODEL", "claude-opus-4-5-20251101"),
    cluster_api_key=os.getenv("CLUSTER_API_KEY", os.getenv("OPENAI_API_KEY", "")),
    main_api_key=os.getenv("MAIN_API_KEY", os.getenv("OPENAI_API_KEY", "")),
    fallback_api_key=os.getenv("FALLBACK_API_KEY", os.getenv("ANTHROPIC_API_KEY", "")),
    cluster_base_url="https://api.openai.com/v1",
    main_base_url="https://api.openai.com/v1",
    fallback_base_url="https://api.anthropic.com/v1",
    max_token_per_module=5000  # LOWER THRESHOLD to force clustering
)

print(f"🤖 Model: {config.cluster_model}")
print(f"📏 Max tokens per module: {config.max_token_per_module}\n")

# Create 20 components to exceed token limit
components = {}
for i in range(20):
    components[str(i)] = Node(
        id=str(i), name=f"Component{i}", component_type="class",
        file_path=f"{test_repo}/test/Component{i}.java",
        relative_path=f"test/Component{i}.java", language="java"
    )

print(f"📦 Components: {len(components)}\n")
print("🔄 Running clustering...\n")

module_tree = cluster_modules(
    leaf_nodes=list(components.keys()), components=components, config=config,
    current_module_tree={}, current_module_name=None, current_module_path=[]
)

if len(module_tree) == 0:
    print("❌ FAILED - Check LLM response above")
    results.add_test("clustering produced modules", False, "module_tree is empty")
else:
    print(f"✅ SUCCESS: {len(module_tree)} modules")
    for name, info in module_tree.items():
        print(f"   - {name}: {len(info.get('components', []))} components")
    results.add_test("clustering produced modules", True, f"{len(module_tree)} modules")

success = results.print_summary()
sys.exit(0 if success else 1)
