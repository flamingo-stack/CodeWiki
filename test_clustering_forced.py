#!/usr/bin/env python3
"""
FORCED clustering test - set max_token_per_module=50 to FORCE LLM call.
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

test_repo = "/Users/michaelassraf/Documents/GitHub/openframe-oss-tenant"

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
    max_token_per_module=50,  # FORCE CLUSTERING (very low threshold)
    cluster_max_tokens=4096   # FIX: Lower max_tokens for gpt-4o
)

print(f"🤖 Model: {config.cluster_model}")
print(f"📏 FORCED max tokens: {config.max_token_per_module} (will force LLM call)\n")

# Create 10 components
components = {}
for i in range(10):
    components[str(i)] = Node(
        id=str(i), name=f"Component{i}", component_type="class",
        file_path=f"{test_repo}/test/Component{i}.java",
        relative_path=f"test/Component{i}.java", language="java"
    )

print(f"📦 Components: {len(components)}\n")
print("🔄 Running clustering (WILL call LLM)...\n")
print("=" * 80)

module_tree = cluster_modules(
    leaf_nodes=list(components.keys()), components=components, config=config,
    current_module_tree={}, current_module_name=None, current_module_path=[]
)

print("=" * 80)
print("\n📊 RESULTS:\n")

if len(module_tree) == 0:
    print("❌ FAILED: Empty module tree")
    print("   This means LLM did NOT follow <GROUPED_COMPONENTS> tag format")
    print("   Check logs above for 'Invalid LLM response format' or 'Invalid JSON'")
    sys.exit(1)
else:
    print(f"✅ SUCCESS: {len(module_tree)} modules created")
    print("\nModules generated:")
    for name, info in module_tree.items():
        comp_count = len(info.get('components', []))
        print(f"   - {name}: {comp_count} components")
    print("\n🎉 THE FIX WORKS! LLM followed the <GROUPED_COMPONENTS> tag format!")
    sys.exit(0)
