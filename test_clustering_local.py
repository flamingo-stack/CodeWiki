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
from codewiki.src.be.cluster_modules import cluster_modules
from codewiki.src.be.file_manager import FileManager
from codewiki.src.be.dependency_analyzer.models.node import Node
from codewiki.src.be.config import Config

def test_clustering():
    """Test clustering on a small sample to verify prompt fix."""

    print("=" * 80)
    print("🧪 TESTING CODEWIKI CLUSTERING LOCALLY")
    print("=" * 80)

    # Setup test repo path
    test_repo = "/Users/michaelassraf/Documents/GitHub/openframe-oss-tenant"

    if not os.path.exists(test_repo):
        print(f"❌ Test repo not found: {test_repo}")
        print("   Update test_repo variable to point to your local repo")
        return

    print(f"\n📂 Test repository: {test_repo}")

    # Create minimal config
    config = Config(
        repo_path=test_repo,
        output_path="/tmp/codewiki_test_output",
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
    components = {
        "0": Node(
            id="0",
            fqdn="test.auth.AuthService",
            file_path=os.path.join(test_repo, "test/auth/AuthService.java"),
            relative_path="test/auth/AuthService.java"
        ),
        "1": Node(
            id="1",
            fqdn="test.auth.AuthController",
            file_path=os.path.join(test_repo, "test/auth/AuthController.java"),
            relative_path="test/auth/AuthController.java"
        ),
        "2": Node(
            id="2",
            fqdn="test.api.UserService",
            file_path=os.path.join(test_repo, "test/api/UserService.java"),
            relative_path="test/api/UserService.java"
        ),
        "3": Node(
            id="3",
            fqdn="test.api.UserController",
            file_path=os.path.join(test_repo, "test/api/UserController.java"),
            relative_path="test/api/UserController.java"
        )
    }

    print(f"\n📦 Test components: {len(components)}")
    for comp_id, comp in components.items():
        print(f"   [{comp_id}] {comp.fqdn}")

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
        print(json.dumps(module_tree, indent=2))

        if len(module_tree) == 0:
            print("\n❌ FAILED: Empty module tree returned")
            print("   This means the LLM did not follow the prompt format")
            print("   Check logs above for 'Invalid LLM response format' error")
            return False
        else:
            print(f"\n✅ SUCCESS: Created {len(module_tree)} modules")
            for module_name, module_info in module_tree.items():
                comp_count = len(module_info.get("components", []))
                print(f"   - {module_name}: {comp_count} components")
            return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check for API keys
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("MAIN_API_KEY")):
        print("❌ ERROR: OPENAI_API_KEY or MAIN_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)

    success = test_clustering()
    sys.exit(0 if success else 1)
