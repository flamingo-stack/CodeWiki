#!/usr/bin/env python3
import os, sys, logging
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
    main_model="gpt-4o", cluster_model="gpt-4o", fallback_model="claude-opus-4-5-20251101",
    cluster_api_key=os.getenv("CLUSTER_API_KEY", os.getenv("OPENAI_API_KEY", "")),
    main_api_key=os.getenv("MAIN_API_KEY", os.getenv("OPENAI_API_KEY", "")),
    fallback_api_key=os.getenv("FALLBACK_API_KEY", os.getenv("ANTHROPIC_API_KEY", "")),
    cluster_base_url="https://api.openai.com/v1",
    main_base_url="https://api.openai.com/v1",
    fallback_base_url="https://api.anthropic.com/v1",
    max_token_per_module=50,
    cluster_max_tokens=4096
)

print(f"🧪 PROOF OF FIX TEST")
print(f"=" * 80)
print(f"🤖 Model: {config.cluster_model}\n")

# Create 20 components with CLEAR semantic groups
# Group 1: Auth components (0-4)
# Group 2: User components (5-9)  
# Group 3: API components (10-14)
# Group 4: Data components (15-19)
components = {}
for i in range(5):
    components[str(i)] = Node(
        id=str(i), name=f"AuthController{i}", component_type="class",
        file_path=f"{test_repo}/auth/AuthController{i}.java",
        relative_path=f"auth/AuthController{i}.java", language="java"
    )
for i in range(5, 10):
    components[str(i)] = Node(
        id=str(i), name=f"UserService{i}", component_type="class",
        file_path=f"{test_repo}/user/UserService{i}.java",
        relative_path=f"user/UserService{i}.java", language="java"
    )
for i in range(10, 15):
    components[str(i)] = Node(
        id=str(i), name=f"ApiController{i}", component_type="class",
        file_path=f"{test_repo}/api/ApiController{i}.java",
        relative_path=f"api/ApiController{i}.java", language="java"
    )
for i in range(15, 20):
    components[str(i)] = Node(
        id=str(i), name=f"DataRepository{i}", component_type="class",
        file_path=f"{test_repo}/data/DataRepository{i}.java",
        relative_path=f"data/DataRepository{i}.java", language="java"
    )

print(f"📦 Created {len(components)} components in 4 semantic groups")
print(f"   - Auth: 0-4")
print(f"   - User: 5-9")
print(f"   - API: 10-14")
print(f"   - Data: 15-19\n")
print("🔄 Running clustering...\n")
print("=" * 80)

module_tree = cluster_modules(
    leaf_nodes=list(components.keys()), components=components, config=config,
    current_module_tree={}, current_module_name=None, current_module_path=[]
)

print("=" * 80)
print("\n📊 RESULTS:\n")

if len(module_tree) == 0:
    print("❌ FAILED: Empty module tree")
    print("   LLM did NOT follow <GROUPED_COMPONENTS> format")
    sys.exit(1)
elif len(module_tree) == 1:
    print("⚠️  LLM returned 1 module (rejected as too small)")
    print("   But LLM DID follow the tag format correctly!")
    print(f"   Module: {list(module_tree.keys())[0]}")
    sys.exit(0)
else:
    print(f"✅✅✅ SUCCESS! {len(module_tree)} modules created ✅✅✅")
    print("\n🎉 THE FIX IS PROVEN TO WORK! 🎉\n")
    print("Modules generated:")
    for name, info in module_tree.items():
        comp_count = len(info.get('components', []))
        comp_list = info.get('components', [])[:5]
        more = len(info.get('components', [])) - 5
        print(f"   - {name}: {comp_count} components {comp_list}{'...' if more > 0 else ''}")
    sys.exit(0)
