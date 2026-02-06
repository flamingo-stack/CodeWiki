#!/usr/bin/env python3
"""
Test script to validate clustering validation logic.
Tests the new json.loads() + validation code with various invalid inputs.
"""

import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def simulate_validation(response_content: str, max_id: int):
    """
    Simulates the validation logic from cluster_modules.py (lines 338-369)

    Args:
        response_content: JSON string with component IDs
        max_id: Maximum valid ID

    Returns:
        (success, module_tree or None)
    """
    logger.info("\n" + "="*70)
    logger.info(f"Testing response with max_id={max_id}")
    logger.info(f"Response: {response_content[:200]}")

    # Parse JSON safely (no code execution)
    try:
        module_tree = json.loads(response_content)
        logger.info(f"✅ JSON parsing succeeded")
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in LLM response: {e}")
        logger.error(f"Response excerpt: {response_content[:500]}...")
        return (False, None)

    if not isinstance(module_tree, dict):
        logger.error(f"❌ Invalid module tree format - expected dict, got {type(module_tree)}")
        return (False, None)

    # CRITICAL: Validate all component IDs are integers
    for module_name, module_info in module_tree.items():
        if "components" not in module_info:
            continue

        component_ids = module_info["components"]
        invalid_ids = []

        for comp_id in component_ids:
            # Check if ID is an integer
            if not isinstance(comp_id, int):
                invalid_ids.append(f"{comp_id} (type: {type(comp_id).__name__})")
            # Check if ID is in valid range
            elif comp_id < 0 or comp_id > max_id:
                invalid_ids.append(f"{comp_id} (out of range 0-{max_id})")

        if invalid_ids:
            logger.error(f"❌ Module '{module_name}' contains invalid component IDs:")
            logger.error(f"   Invalid IDs: {invalid_ids}")
            logger.error(f"   Expected: Integers in range 0-{max_id}")
            logger.error(f"   LLM ignored instructions and returned non-integer IDs!")
            return (False, None)

    logger.info(f"✅ LLM response validation passed: All IDs are integers in valid range")
    return (True, module_tree)


# Test cases
test_cases = [
    {
        "name": "Valid - Bare integers",
        "json": '{"auth_module": {"path": "src/auth", "components": [0, 1, 2]}}',
        "max_id": 10,
        "should_pass": True
    },
    {
        "name": "Invalid - Quoted integers",
        "json": '{"auth_module": {"path": "src/auth", "components": ["0", "1", "2"]}}',
        "max_id": 10,
        "should_pass": False
    },
    {
        "name": "Invalid - String class names",
        "json": '{"auth_module": {"path": "src/auth", "components": ["AuthService", "UserService"]}}',
        "max_id": 10,
        "should_pass": False
    },
    {
        "name": "Invalid - Mixed types",
        "json": '{"auth_module": {"path": "src/auth", "components": [0, "1", "AuthService", 2]}}',
        "max_id": 10,
        "should_pass": False
    },
    {
        "name": "Invalid - Out of range ID",
        "json": '{"auth_module": {"path": "src/auth", "components": [0, 1, 999]}}',
        "max_id": 10,
        "should_pass": False
    },
    {
        "name": "Invalid - Negative ID",
        "json": '{"auth_module": {"path": "src/auth", "components": [0, -1, 2]}}',
        "max_id": 10,
        "should_pass": False
    },
    {
        "name": "Valid - Multiple modules",
        "json": '{"auth": {"components": [0, 1]}, "api": {"components": [2, 3, 4]}}',
        "max_id": 10,
        "should_pass": True
    },
    {
        "name": "Invalid - Malformed JSON",
        "json": '{"auth_module": {"components": [0, 1,]}}',  # Trailing comma
        "max_id": 10,
        "should_pass": False
    },
    {
        "name": "Valid - Empty components",
        "json": '{"auth_module": {"path": "src/auth", "components": []}}',
        "max_id": 10,
        "should_pass": True
    },
    {
        "name": "Valid - No components key",
        "json": '{"auth_module": {"path": "src/auth"}}',
        "max_id": 10,
        "should_pass": True
    }
]

def run_tests():
    """Run all test cases and report results."""
    print("\n" + "="*70)
    print("CODEWIKI CLUSTERING VALIDATION TEST SUITE")
    print("="*70)

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'='*70}")

        success, module_tree = simulate_validation(
            test_case['json'],
            test_case['max_id']
        )

        if success == test_case['should_pass']:
            logger.info(f"✅ TEST PASSED: Got expected result (success={success})")
            passed += 1
        else:
            logger.error(f"❌ TEST FAILED: Expected {test_case['should_pass']}, got {success}")
            failed += 1

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests: {len(test_cases)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success rate: {passed/len(test_cases)*100:.1f}%")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Validation logic is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the validation logic.")

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
