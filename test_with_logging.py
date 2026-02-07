#!/usr/bin/env python3
import os
import sys
import logging

# Setup logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    force=True
)

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

# Show result
if len(module_tree) == 0:
    print("❌ FAILED: Empty module tree")
    print("   Check the INFO logs above for LLM response")
else:
    print(f"✅ SUCCESS: {len(module_tree)} modules created")
    for name, info in module_tree.items():
        print(f"   - {name}: {len(info.get('components', []))} components")
