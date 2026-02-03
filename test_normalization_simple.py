#!/usr/bin/env python3
"""
Standalone test for short ID to FQDN normalization logic

This tests the core normalization algorithm without requiring full imports.
"""

from collections import defaultdict


def build_short_id_to_fqdn_map(components):
    """
    Build mapping from short component IDs to FQDNs.
    Simplified version without logging for testing.
    """
    mapping = {}
    collisions = defaultdict(list)

    for fqdn, node_data in components.items():
        # Extract short ID from node or derive from FQDN
        short_id = node_data.get('short_id')

        if not short_id:
            # Fallback: extract from FQDN
            if '::' in fqdn:
                short_id = fqdn.split('::')[-1]
            else:
                short_id = fqdn.split('.')[-1]

        # Track collisions for debugging
        if short_id in mapping:
            collisions[short_id].append(fqdn)
            if mapping[short_id] not in collisions[short_id]:
                collisions[short_id].insert(0, mapping[short_id])
        else:
            mapping[short_id] = fqdn

    # Report collisions
    if collisions:
        print("🔀 Short ID collisions detected:")
        for short_id, fqdns in collisions.items():
            print(f"   ├─ '{short_id}' maps to {len(fqdns)} components:")
            for fqdn in fqdns:
                print(f"   │  └─ {fqdn}")
        print(f"   └─ Using first match for each collision\n")

    return mapping


def test_normalization():
    """Test the normalization logic"""

    print("🧪 Testing Short ID to FQDN Normalization\n")
    print("=" * 70)

    # Mock components dictionary
    components = {
        "openframe-auth.com.openframe.config.AuthorizationServerConfig": {
            "short_id": "AuthorizationServerConfig",
            "namespace": "openframe-auth",
        },
        "openframe-api.com.openframe.service.UserService": {
            "short_id": "UserService",
            "namespace": "openframe-api",
        },
        "main-repo.src/auth/auth_manager.py::AuthManager": {
            "short_id": "AuthManager",
            "namespace": "main-repo",
        },
        "deps/lib-auth.auth.handlers::LoginHandler": {
            "short_id": "LoginHandler",
            "namespace": "deps/lib-auth",
        },
        # Component without short_id (should derive from FQDN)
        "main-repo.utils.helper::format_date": {
            "namespace": "main-repo",
        },
    }

    print(f"📦 Components dictionary: {len(components)} entries")
    for fqdn in components.keys():
        short_id = components[fqdn].get('short_id', 'DERIVED')
        print(f"   └─ {fqdn} (short_id: {short_id})")
    print()

    # Build mapping
    print("🔨 Building short_id → FQDN mapping...")
    short_to_fqdn = build_short_id_to_fqdn_map(components)
    print()

    print(f"✅ Mapping built: {len(short_to_fqdn)} entries")
    for short_id, fqdn in sorted(short_to_fqdn.items()):
        print(f"   └─ '{short_id}' → '{fqdn}'")
    print()

    # Test normalization
    print("🧪 Testing normalization scenarios:")
    print("-" * 70)

    test_cases = [
        ("AuthorizationServerConfig", True),
        ("UserService", True),
        ("AuthManager", True),
        ("LoginHandler", True),
        ("format_date", True),  # Derived from FQDN
        ("openframe-auth.com.openframe.config.AuthorizationServerConfig", True),  # Full FQDN
        ("NonExistentClass", False),
    ]

    passed = 0
    failed = 0

    for comp_id, should_succeed in test_cases:
        print(f"\n{'✅' if should_succeed else '❌'} Test: '{comp_id}'")

        # Normalization logic
        if comp_id in components:
            result = comp_id
            status = "EXACT"
        elif comp_id in short_to_fqdn:
            result = short_to_fqdn[comp_id]
            status = "MAPPED"
        else:
            result = None
            status = "FAILED"

        success = bool(result) == should_succeed

        if success:
            print(f"   Status: {status}")
            if result:
                print(f"   Result: '{result}'")
            passed += 1
        else:
            print(f"   Status: {status} (UNEXPECTED)")
            failed += 1

    print()
    print("=" * 70)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(test_normalization())
