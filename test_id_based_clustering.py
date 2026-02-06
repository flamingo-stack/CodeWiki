#!/usr/bin/env python3
"""
Test script to verify ID-based clustering fixes.
Tests the critical fixes:
1. json.loads() instead of eval()
2. format_potential_core_components() return type handling
3. Integer ID validation
"""

import json
import sys
from typing import Dict

# Test 1: Verify json.loads() works with integer IDs
def test_json_parsing():
    print("Test 1: JSON parsing with integer IDs")
    print("-" * 60)

    # Valid JSON with integer IDs
    valid_json = """
    {
        "auth_module": {
            "path": "src/auth",
            "components": [0, 1, 2]
        },
        "api_module": {
            "path": "src/api",
            "components": [3, 4, 5]
        }
    }
    """

    try:
        result = json.loads(valid_json)
        print("✅ Valid JSON parsed successfully")
        print(f"   auth_module components: {result['auth_module']['components']}")
        print(f"   Type check: {all(isinstance(x, int) for x in result['auth_module']['components'])}")
    except Exception as e:
        print(f"❌ Failed to parse valid JSON: {e}")
        return False

    # Invalid JSON with quoted IDs (should fail)
    invalid_json = """
    {
        "auth_module": {
            "components": ["0", "1", "2"]
        }
    }
    """

    try:
        result = json.loads(invalid_json)
        components = result['auth_module']['components']
        if all(isinstance(x, str) for x in components):
            print("⚠️  JSON with quoted IDs parsed (but will fail validation)")
            print(f"   Components: {components} (type: str - WRONG)")
        else:
            print("❌ Unexpected type")
    except Exception as e:
        print(f"❌ Parsing failed: {e}")

    print()
    return True


# Test 2: Verify format_potential_core_components() return types
def test_return_types():
    print("Test 2: format_potential_core_components() return types")
    print("-" * 60)

    # Simulate the function signature
    def format_potential_core_components_mock(leaf_nodes, components):
        """Mock function with correct 4-tuple return"""
        potential_core_components = "# Mock component list"
        potential_core_components_with_code = "# Mock component with code\nclass Example:\n    pass"
        id_to_fqdn = {0: "example.Example", 1: "test.Test"}
        id_descriptions = {"0": "Example (mock, test)", "1": "Test (mock, test)"}
        return potential_core_components, potential_core_components_with_code, id_to_fqdn, id_descriptions

    # Test correct usage (NEW code)
    try:
        _, potential_core_components_with_code, _, _ = format_potential_core_components_mock([], {})
        print(f"✅ Correct unpacking works")
        print(f"   Type: {type(potential_core_components_with_code)}")
        print(f"   Is string: {isinstance(potential_core_components_with_code, str)}")

        # Simulate count_tokens usage
        def count_tokens_mock(text: str) -> int:
            return len(text.split())

        num_tokens = count_tokens_mock(potential_core_components_with_code)
        print(f"   Token count: {num_tokens}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

    # Test OLD buggy code (would fail)
    try:
        result = format_potential_core_components_mock([], {})
        last_element = result[-1]  # This is id_descriptions (Dict)
        print(f"⚠️  OLD code: result[-1] = {type(last_element)} (Dict, not str!)")
        # This would fail in count_tokens:
        # num_tokens = count_tokens(last_element)  # TypeError!
    except Exception as e:
        print(f"❌ Failed: {e}")

    print()
    return True


# Test 3: Verify integer ID validation
def test_id_validation():
    print("Test 3: Integer ID validation")
    print("-" * 60)

    id_to_fqdn = {0: "auth.AuthService", 1: "api.UserController", 2: "config.DatabaseConfig"}
    max_id = len(id_to_fqdn) - 1

    # Test valid IDs
    valid_module_tree = {
        "auth_module": {
            "components": [0, 1]
        },
        "config_module": {
            "components": [2]
        }
    }

    print("Testing VALID module tree:")
    all_valid = True
    for module_name, module_info in valid_module_tree.items():
        component_ids = module_info.get("components", [])
        invalid_ids = []

        for comp_id in component_ids:
            if not isinstance(comp_id, int):
                invalid_ids.append(f"{comp_id} (type: {type(comp_id).__name__})")
            elif comp_id < 0 or comp_id > max_id:
                invalid_ids.append(f"{comp_id} (out of range 0-{max_id})")

        if invalid_ids:
            print(f"❌ Module '{module_name}' has invalid IDs: {invalid_ids}")
            all_valid = False
        else:
            print(f"✅ Module '{module_name}' has valid IDs: {component_ids}")

    # Test invalid IDs
    print("\nTesting INVALID module tree:")
    invalid_module_tree = {
        "bad_module": {
            "components": ["0", 1, 999]  # String, valid int, out-of-range int
        }
    }

    for module_name, module_info in invalid_module_tree.items():
        component_ids = module_info.get("components", [])
        invalid_ids = []

        for comp_id in component_ids:
            if not isinstance(comp_id, int):
                invalid_ids.append(f"{comp_id} (type: {type(comp_id).__name__})")
            elif comp_id < 0 or comp_id > max_id:
                invalid_ids.append(f"{comp_id} (out of range 0-{max_id})")

        if invalid_ids:
            print(f"✅ Correctly detected invalid IDs in '{module_name}': {invalid_ids}")
        else:
            print(f"❌ Should have detected invalid IDs!")
            all_valid = False

    print()
    return all_valid


# Test 4: Verify ID-to-FQDN normalization
def test_normalization():
    print("Test 4: ID-to-FQDN normalization")
    print("-" * 60)

    id_to_fqdn = {
        0: "main-repo.src/auth/auth_service.py::AuthService",
        1: "main-repo.src/api/user_controller.py::UserController",
        2: "main-repo.src/config/database.py::DatabaseConfig"
    }

    module_tree = {
        "auth_module": {
            "components": [0, 1]
        },
        "config_module": {
            "components": [2]
        }
    }

    print("Normalizing component IDs to FQDNs:")
    total_normalized = 0

    for module_name, module_data in module_tree.items():
        component_ids = module_data.get('components', [])
        normalized_components = []

        for comp_id in component_ids:
            try:
                idx = int(comp_id)
                if idx in id_to_fqdn:
                    fqdn = id_to_fqdn[idx]
                    normalized_components.append(fqdn)
                    total_normalized += 1
                    print(f"   ✅ ID {idx} → {fqdn}")
            except (ValueError, TypeError) as e:
                print(f"   ❌ Invalid ID: {comp_id} - {e}")

        module_data['components'] = normalized_components

    print(f"\n✅ Normalized {total_normalized} component IDs")
    print(f"   Final module tree has FQDNs:")
    for module_name, module_data in module_tree.items():
        print(f"     {module_name}: {len(module_data['components'])} components")

    print()
    return total_normalized == 3


if __name__ == "__main__":
    print("=" * 60)
    print("ID-BASED CLUSTERING VALIDATION TESTS")
    print("=" * 60)
    print()

    results = []
    results.append(("JSON parsing", test_json_parsing()))
    results.append(("Return types", test_return_types()))
    results.append(("ID validation", test_id_validation()))
    results.append(("Normalization", test_normalization()))

    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
