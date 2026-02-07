#!/usr/bin/env python3
"""
DEBUG clustering test - show LLM response.
"""

import os
import sys
import json

# Add CodeWiki to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env
from dotenv import load_dotenv
load_dotenv('.env.local')

# Monkey patch cluster_modules to capture the LLM response
original_cluster_modules = None
captured_response = None

def capture_llm_response():
    """Monkey patch to capture LLM response."""
    global captured_response
    from codewiki.src.be import cluster_modules as cm_module
    from codewiki.src.be.llm_services import create_llm_client

    original_create = create_llm_client

    def patched_create(*args, **kwargs):
        client = original_create(*args, **kwargs)
        original_call = client.call

        def patched_call(*call_args, **call_kwargs):
            result = original_call(*call_args, **call_kwargs)
            global captured_response
            captured_response = result
            return result

        client.call = patched_call
        return client

    cm_module.create_llm_client = patched_create

capture_llm_response()

from codewiki.src.be.cluster_modules import cluster_modules
from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.config import Config

# Test repo
test_repo = "/Users/michaelassraf/Documents/GitHub/openframe-oss-tenant"

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

print("\n" + "=" * 80)

# Show captured response
if captured_response:
    print("📝 LLM RESPONSE:")
    print("-" * 80)
    print(captured_response[:2000] if len(captured_response) > 2000 else captured_response)
    if len(captured_response) > 2000:
        print(f"\n... (truncated, total: {len(captured_response)} chars)")
    print("-" * 80)

# Show result
if len(module_tree) == 0:
    print("\n❌ FAILED: Empty module tree")
    if captured_response:
        has_tags = "<GROUPED_COMPONENTS>" in captured_response
        print(f"   Has <GROUPED_COMPONENTS> tag: {has_tags}")
else:
    print(f"\n✅ SUCCESS: {len(module_tree)} modules created")
    print(json.dumps(module_tree, indent=2, default=str))
