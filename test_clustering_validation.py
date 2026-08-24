#!/usr/bin/env python3
"""
Test script to validate clustering validation logic.
Tests the new json.loads() + validation code with various invalid inputs.
"""

import json
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "codewiki", "src", "be"))

from cluster_modules import validate_cluster_response


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
    Exercises the real validation logic from cluster_modules.py.

    Args:
        response_content: JSON string with component IDs
        max_id: Maximum valid ID

    Returns:
        (success, module_tree or None)
    """
    logger.info("\n" + "="*70)
    logger.info(f"Testing response with max_id={max_id}")
    logger.info(f"Response: {response_content[:200]}")

    success, module_tree = validate_cluster_response(response_content, max_id)

    if success:
        logger.info(f"✅ LLM response validation passed: All IDs are integers in valid range")
    else:
        logger.error(f"❌ LLM response validation failed")

    return (success, module_tree)


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
