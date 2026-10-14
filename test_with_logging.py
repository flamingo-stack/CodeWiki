#!/usr/bin/env python3
import os
import sys

# Add CodeWiki to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env
from dotenv import load_dotenv
load_dotenv('.env.local')

from codewiki.src.be.cluster_modules import cluster_modules
from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.be.dependency_analyzer.utils.logging_config import setup_logging
from codewiki.src.config import Config


class TestResults:
    def __init__(self):
        self.results = []

    def add_test(self, name, passed, message=""):
        self.results.append((name, passed, message))

    def print_summary(self):
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        failed = 0
        for name, passed, message in self.results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {name}")
            if message:
                print(f"   {message}")
            if not passed:
                failed += 1
        print("=" * 80)
        print(f"Total: {len(self.results)}, Passed: {len(self.results) - failed}, Failed: {failed}")
        return failed == 0


results = TestResults()

# Setup logging FIRST
setup_logging()

# Test repo
test_repo = os.getenv("TEST_REPO_PATH", sys.argv[1] if len(sys.argv) > 1 else "")
if not test_repo:
    print("❌ ERROR: No test repo path provided. Set TEST_REPO_PATH env var or pass it as the first argument.")
    sys.exit(1)

# Create config
config = Config(
    repo_path=test_repo,
    output_dir="/tmp/codewiki_test",
    dependency_graph_dir="/tmp/codewiki_test/deps",
    docs_dir="/tmp/codewiki_test/docs",
    max_depth=2,
    main_model=os.getenv("MAIN_MODEL", "gpt-4o"),
    cluster_model=os.getenv("CLUSTER_MODEL", "gpt-4o"),
    fallback_model=os.getenv("FALLBACK_MODEL", "claude-opus-4-5-20251101"),
    cluster_api_key=os.getenv("CLUSTER_API_KEY", os.getenv("OPENAI_API_KEY", "")),
    main_api_key=os.getenv("MAIN_API_KEY", os.getenv("OPENAI_API_KEY", "")),
    fallback_api_key=os.getenv("FALLBACK_API_KEY", os.getenv("ANTHROPIC_API_KEY", "")),
    cluster_base_url=os.getenv("CLUSTER_BASE_URL", "https://api.openai.com/v1"),
    main_base_url=os.getenv("MAIN_BASE_URL", "https://api.openai.com/v1"),
    fallback_base_url=os.getenv("FALLBACK_BASE_URL", "https://api.anthropic.com/v1")
)

print(f"🤖 Using model: {config.cluster_model}\n")

# Create sample components
components = {
    "0": Node(id="0", name="AuthController", component_type="class",
              file_path=f"{test_repo}/test/AuthController.java",
              relative_path="test/AuthController.java", language="java"),
    "1": Node(id="1", name="AuthService", component_type="class",
              file_path=f"{test_repo}/test/AuthService.java",
              relative_path="test/AuthService.java", language="java"),
    "2": Node(id="2", name="UserController", component_type="class",
              file_path=f"{test_repo}/test/UserController.java",
              relative_path="test/UserController.java", language="java"),
    "3": Node(id="3", name="UserService", component_type="class",
              file_path=f"{test_repo}/test/UserService.java",
              relative_path="test/UserService.java", language="java")
}

print("🔄 Clustering...\n")

# Run clustering
module_tree = cluster_modules(
    leaf_nodes=list(components.keys()),
    components=components,
    config=config,
    current_module_tree={},
    current_module_name=None,
    current_module_path=[]
)

# Show result
if len(module_tree) == 0:
    results.add_test("cluster_modules produces non-empty module tree", False,
                      "Empty module tree. Check the INFO logs above for LLM response")
else:
    detail = ", ".join(f"{name}: {len(info.get('components', []))} components"
                        for name, info in module_tree.items())
    results.add_test("cluster_modules produces non-empty module tree", True,
                      f"{len(module_tree)} modules created - {detail}")

success = results.print_summary()
sys.exit(0 if success else 1)
