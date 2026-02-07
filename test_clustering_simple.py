#!/usr/bin/env python3
"""
SIMPLE clustering test - just check if the prompt format is followed.
"""

import os
import sys

# Add CodeWiki to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env
from dotenv import load_dotenv
load_dotenv('.env.local')

from codewiki.src.be.cluster_modules import cluster_modules
from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.config import Config

# Test repo
test_repo = "/Users/michaelassraf/Documents/GitHub/openframe-oss-tenant"

# Create simple config with all required fields
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

print(f"🤖 Using model: {config.cluster_model}")
print(f"   API key: {'SET' if config.cluster_api_key else 'MISSING'}")

# Create 4 sample components
components = {
    "0": Node(
        id="0",
        name="AuthController",
        component_type="class",
        file_path=f"{test_repo}/test/AuthController.java",
        relative_path="test/AuthController.java",
        language="java"
    ),
    "1": Node(
        id="1",
        name="AuthService",
        component_type="class",
        file_path=f"{test_repo}/test/AuthService.java",
        relative_path="test/AuthService.java",
        language="java"
    ),
    "2": Node(
        id="2",
        name="UserController",
        component_type="class",
        file_path=f"{test_repo}/test/UserController.java",
        relative_path="test/UserController.java",
        language="java"
    ),
    "3": Node(
        id="3",
        name="UserService",
        component_type="class",
        file_path=f"{test_repo}/test/UserService.java",
        relative_path="test/UserService.java",
        language="java"
    )
}

print(f"\n📦 Test components: {len(components)}")
for comp_id, comp in components.items():
    print(f"   [{comp_id}] {comp.name}")

print("\n🔄 Running clustering...\n")
print("=" * 80)

# Run clustering
module_tree = cluster_modules(
    leaf_nodes=list(components.keys()),
    components=components,
    config=config,
    current_module_tree={},
    current_module_name=None,
    current_module_path=[]
)

print("=" * 80)

if len(module_tree) == 0:
    print("\n❌ FAILED: Empty module tree")
    print("   LLM did not follow the <GROUPED_COMPONENTS> tag format")
    sys.exit(1)
else:
    print(f"\n✅ SUCCESS: {len(module_tree)} modules created")
    for module_name, module_info in module_tree.items():
        comp_count = len(module_info.get("components", []))
        print(f"   - {module_name}: {comp_count} components")
    sys.exit(0)
