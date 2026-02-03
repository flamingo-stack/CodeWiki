#!/usr/bin/env python3
"""
Test script for short ID to FQDN normalization in cluster_modules.py

This simulates the scenario where LLM returns short component names
instead of full FQDNs, and verifies that normalization converts them correctly.
"""

import sys
from pathlib import Path

# Add codewiki to path
sys.path.insert(0, str(Path(__file__).parent))

from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.be.cluster_modules import build_short_id_to_fqdn_map


def test_short_id_normalization():
    """Test the short_id → FQDN mapping functionality"""

    print("🧪 Testing Short ID to FQDN Normalization\n")
    print("=" * 70)

    # Create mock components dictionary (simulating what we have in memory)
    components = {
        "openframe-auth.com.openframe.config.AuthorizationServerConfig": Node(
            id="openframe-auth.com.openframe.config.AuthorizationServerConfig",
            name="AuthorizationServerConfig",
            short_id="AuthorizationServerConfig",
            namespace="openframe-auth",
            component_type="class",
            file_path="/path/to/AuthorizationServerConfig.java",
            relative_path="com/openframe/config/AuthorizationServerConfig.java"
        ),
        "openframe-api.com.openframe.service.UserService": Node(
            id="openframe-api.com.openframe.service.UserService",
            name="UserService",
            short_id="UserService",
            namespace="openframe-api",
            component_type="class",
            file_path="/path/to/UserService.java",
            relative_path="com/openframe/service/UserService.java"
        ),
        "main-repo.src/auth/auth_manager.py::AuthManager": Node(
            id="main-repo.src/auth/auth_manager.py::AuthManager",
            name="AuthManager",
            short_id="AuthManager",
            namespace="main-repo",
            component_type="class",
            file_path="/path/to/auth_manager.py",
            relative_path="src/auth/auth_manager.py"
        ),
        "deps/lib-auth.auth.handlers::LoginHandler": Node(
            id="deps/lib-auth.auth.handlers::LoginHandler",
            name="LoginHandler",
            short_id="LoginHandler",
            namespace="deps/lib-auth",
            component_type="class",
            file_path="/path/to/handlers.py",
            relative_path="auth/handlers.py",
            is_from_deps=True
        ),
    }

    print(f"📦 Components dictionary: {len(components)} entries")
    for fqdn in components.keys():
        print(f"   └─ {fqdn}")
    print()

    # Build the mapping
    print("🔨 Building short_id → FQDN mapping...")
    short_to_fqdn = build_short_id_to_fqdn_map(components)
    print()

    print(f"✅ Mapping built: {len(short_to_fqdn)} entries")
    for short_id, fqdn in short_to_fqdn.items():
        print(f"   └─ '{short_id}' → '{fqdn}'")
    print()

    # Test normalization scenarios
    print("🧪 Testing normalization scenarios:")
    print("-" * 70)

    test_cases = [
        ("AuthorizationServerConfig", True, "Short ID from Java component"),
        ("UserService", True, "Short ID from service component"),
        ("AuthManager", True, "Short ID from Python component"),
        ("LoginHandler", True, "Short ID from dependency component"),
        ("openframe-auth.com.openframe.config.AuthorizationServerConfig", True, "Full FQDN (already normalized)"),
        ("NonExistentClass", False, "Component that doesn't exist"),
    ]

    passed = 0
    failed = 0

    for comp_id, should_succeed, description in test_cases:
        print(f"\nTest: {description}")
        print(f"   Input: '{comp_id}'")

        # Simulate normalization logic
        if comp_id in components:
            result = comp_id
            status = "✅ EXACT"
        elif comp_id in short_to_fqdn:
            result = short_to_fqdn[comp_id]
            status = "✅ MAPPED"
        else:
            result = None
            status = "❌ FAILED"

        if should_succeed and result:
            print(f"   Result: {status} → '{result}'")
            passed += 1
        elif not should_succeed and not result:
            print(f"   Result: {status} (expected)")
            passed += 1
        else:
            print(f"   Result: {status} (unexpected)")
            failed += 1

    print()
    print("=" * 70)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print()

    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(test_short_id_normalization())
