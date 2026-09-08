#!/usr/bin/env python3
"""
Test script to validate clustering validation logic.
Tests the new json.loads() + validation code with various invalid inputs.
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class TestResults:
    """Accumulates test results and prints a summary."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []

    def add_test(self, name: str, passed: bool, details: str = ""):
        if passed:
            self.passed += 1
            logger.info(f"✅ TEST PASSED: {name}")
        else:
            self.failed += 1
            self.failures.append((name, details))
            logger.error(f"❌ TEST FAILED: {name} {details}")

    def print_summary(self):
        total = self.passed + self.failed
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        if total:
            print(f"Success rate: {self.passed/total*100:.1f}%")

        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED! Validation logic is working correctly.")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed. Please review the validation logic.")
            for name, details in self.failures:
                print(f"   - {name}: {details}")

    @property
    def success(self):
        return self.failed == 0


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

    results = TestResults()

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'='*70}")

        success, module_tree = simulate_validation(
            test_case['json'],
            test_case['max_id']
        )

        results.add_test(
            test_case['name'],
            success == test_case['should_pass'],
            f"(expected {test_case['should_pass']}, got {success})"
        )

    results.print_summary()

    return results.success

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

