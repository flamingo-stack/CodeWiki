#!/usr/bin/env python3
"""
Local test script for CodeWiki clustering prompt fix.
Run this to test clustering locally without full workflow.

Usage:
    python3 test_clustering_local.py
"""

import os
import sys
import json

# Add CodeWiki to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from codewiki.src.be.cluster_modules import cluster_modules
from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.config import Config


class TestResults:
    """Simple pass/fail accumulator for standalone integration test scripts."""

    def __init__(self):
        self.results = []

    def add_test(self, name, passed, message=""):
        self.results.append((name, passed, message))

    def print_summary(self):
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        for name, passed, message in self.results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {name}" + (f": {message}" if message else ""))
        total = len(self.results)
        passed_count = sum(1 for _, passed, _ in self.results if passed)
        print(f"\n{passed_count}/{total} tests passed")
        return passed_count == total

def test_clustering(results):
    """Test clustering on a small sample to verify prompt fix."""

    print("=" * 80)
    print("🧪 TESTING CODEWIKI CLUSTERING LOCALLY")
    print("=" * 80)

    # Setup test repo path (override with CODEWIKI_TEST_REPO env var)
    test_repo = os.getenv("CODEWIKI_TEST_REPO")

    if not test_repo or not os.path.exists(test_repo):
        print(f"❌ Test repo not found: {test_repo}")
        print("   Set the CODEWIKI_TEST_REPO environment variable to point to your local repo")
        results.add_test("test_repo_exists", False, f"Test repo not found: {test_repo}")
        return False

    print(f"\n📂 Test repository: {test_repo}")

    # Create minimal config via the required factory method
    config = Config.from_args(
        repo_path=test_repo,
        output_path="/tmp/codewiki_test_output",
        cluster_provider="openai",
        cluster_model="gpt-4o",
        cluster_api_key=os.getenv("OPENAI_API_KEY") or os.getenv("CLUSTER_API_KEY"),
        cluster_base_url="https://api.openai.com/v1",
        main_provider="openai",
        main_model="gpt-4o",  # Use gpt-4o instead of gpt-5.2
        main_api_key=os.getenv("OPENAI_API_KEY") or os.getenv("MAIN_API_KEY"),
        main_base_url="https://api.openai.com/v1",
        fallback_provider="anthropic",
        fallback_model="claude-opus-4-5-20251101",
        fallback_api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("FALLBACK_API_KEY"),
        fallback_base_url="https://api.anthropic.com/v1",
        verbose=True
    )

    print(f"\n🤖 Using model: {config.main_model}")
    print(f"   Provider: {config.main_provider}")

    # Create sample components (minimal test set)
    test_file_1 = os.path.join(test_repo, "openframe/services/openframe-api/src/main/java/com/openframe/api/controller/AuthController.java")
    test_file_2 = os.path.join(test_repo, "openframe/services/openframe-api/src/main/java/com/openframe/api/service/AuthService.java")
    test_file_3 = os.path.join(test_repo, "openframe/services/openframe-api/src/main/java/com/openframe/api/controller/UserController.java")
    test_file_4 = os.path.join(test_repo, "openframe/services/openframe-api/src/main/java/com/openframe/api/service/UserService.java")

    components = {
        "0": Node(
            id="0",
            name="AuthController",
            component_type="class",
            file_path=test_file_1,
            relative_path="openframe/services/openframe-api/src/main/java/com/openframe/api/controller/AuthController.java",
            language="java"
        ),
        "1": Node(
            id="1",
            name="AuthService",
            component_type="class",
            file_path=test_file_2,
            relative_path="openframe/services/openframe-api/src/main/java/com/openframe/api/service/AuthService.java",
            language="java"
        ),
        "2": Node(
            id="2",
            name="UserController",
            component_type="class",
            file_path=test_file_3,
            relative_path="openframe/services/openframe-api/src/main/java/com/openframe/api/controller/UserController.java",
            language="java"
        ),
        "3": Node(
            id="3",
            name="UserService",
            component_type="class",
            file_path=test_file_4,
            relative_path="openframe/services/openframe-api/src/main/java/com/openframe/api/service/UserService.java",
            language="java"
        )
    }

    print(f"\n📦 Test components: {len(components)}")
    for comp_id, comp in components.items():
        print(f"   [{comp_id}] {comp.name}")

    print("\n🔄 Running clustering...")
    print("-" * 80)

    try:
        # Run clustering
        module_tree = cluster_modules(
            leaf_nodes=list(components.keys()),
            components=components,
            config=config,
            current_module_tree={},
            current_module_name=None,
            current_module_path=[]
        )

        print("-" * 80)
        print("\n✅ CLUSTERING RESULT:")
        print(json.dumps(module_tree, indent=2, default=str))

        if len(module_tree) == 0:
            print("\n❌ FAILED: Empty module tree returned")
            print("   This means the LLM did not follow the prompt format")
            print("   Check logs above for 'Invalid LLM response format' error")
            results.add_test("clustering_produces_modules", False, "Empty module tree returned")
            return False
        else:
            print(f"\n✅ SUCCESS: Created {len(module_tree)} modules")
            for module_name, module_info in module_tree.items():
                comp_count = len(module_info.get("components", []))
                print(f"   - {module_name}: {comp_count} components")
            results.add_test("clustering_produces_modules", True, f"Created {len(module_tree)} modules")
            return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        results.add_test("clustering_produces_modules", False, str(e))
        return False

if __name__ == "__main__":
    # Check for API keys
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("MAIN_API_KEY")):
        print("❌ ERROR: OPENAI_API_KEY or MAIN_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)

    test_results = TestResults()
    success = test_clustering(test_results)
    test_results.print_summary()
    sys.exit(0 if success else 1)

