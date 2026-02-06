#!/usr/bin/env python3
"""
Comprehensive integration tests for CodeWiki ID-based clustering system.
Tests validation fixes, normalization, and error handling.
"""

import json
import sys
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add CodeWiki to path
sys.path.insert(0, str(Path(__file__).parent))

from codewiki.src.be.cluster_modules import (
    create_component_id_map,
    normalize_component_ids_by_lookup,
)

# Configure logging to capture warnings
logging.basicConfig(level=logging.WARNING, format='%(message)s')


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_test(self, name: str, passed: bool, details: str = ""):
        self.tests.append({
            "name": name,
            "passed": passed,
            "details": details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        for test in self.tests:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            print(f"{status}: {test['name']}")
            if test["details"]:
                print(f"  → {test['details']}")
        print("="*80)
        print(f"FINAL SCORE: {self.passed}/{self.passed + self.failed} tests passed")
        print("="*80)
        return self.failed == 0


# Sample OpenFrame data structure (mimicking Node objects)
# create_component_id_map expects Dict[str, Node], so we use FQDNs as keys
class MockNode:
    """Mock Node object for testing"""
    def __init__(self, fqdn, name, file_path):
        self.fqdn = fqdn
        self.name = name
        self.file_path = file_path

SAMPLE_COMPONENTS = {
    "openframe.auth.service::AuthService": MockNode(
        "openframe.auth.service::AuthService",
        "AuthService",
        "auth/service.py"
    ),
    "openframe.api.models::CountedGenericQueryResult": MockNode(
        "openframe.api.models::CountedGenericQueryResult",
        "CountedGenericQueryResult",
        "api/models.py"
    ),
    "openframe.controllers.user::UserController": MockNode(
        "openframe.controllers.user::UserController",
        "UserController",
        "controllers/user.py"
    ),
    "openframe.db.connection::DatabaseConnection": MockNode(
        "openframe.db.connection::DatabaseConnection",
        "DatabaseConnection",
        "db/connection.py"
    ),
    "openframe.middleware.logging::LoggingMiddleware": MockNode(
        "openframe.middleware.logging::LoggingMiddleware",
        "LoggingMiddleware",
        "middleware/logging.py"
    )
}


def test_component_id_map_creation(results: TestResults):
    """Test 1: Create component ID map from real data"""
    print("\n[TEST 1] Creating component ID map from real data...")

    try:
        id_to_fqdn, id_descriptions = create_component_id_map(SAMPLE_COMPONENTS)

        # Verify map structure
        if not isinstance(id_to_fqdn, dict):
            results.add_test(
                "Component ID Map Creation",
                False,
                f"Expected dict for id_to_fqdn, got {type(id_to_fqdn)}"
            )
            return

        # Verify all components are mapped
        if len(id_to_fqdn) != len(SAMPLE_COMPONENTS):
            results.add_test(
                "Component ID Map Creation",
                False,
                f"Expected {len(SAMPLE_COMPONENTS)} components, got {len(id_to_fqdn)}"
            )
            return

        # Verify IDs are sequential
        expected_ids = set(range(len(SAMPLE_COMPONENTS)))
        actual_ids = set(id_to_fqdn.keys())
        if expected_ids != actual_ids:
            results.add_test(
                "Component ID Map Creation",
                False,
                f"IDs not sequential: expected {expected_ids}, got {actual_ids}"
            )
            return

        # Verify FQDNs
        expected_fqdns = set(SAMPLE_COMPONENTS.keys())
        actual_fqdns = set(id_to_fqdn.values())
        if expected_fqdns != actual_fqdns:
            results.add_test(
                "Component ID Map Creation",
                False,
                f"FQDN mismatch"
            )
            return

        print(f"✓ Created map with {len(id_to_fqdn)} components")
        print(f"  Sample mapping: 0 → {id_to_fqdn[0]}")
        print(f"  Description: {id_descriptions.get('0', 'N/A')}")
        results.add_test(
            "Component ID Map Creation",
            True,
            f"Successfully created map with {len(id_to_fqdn)} components"
        )

    except Exception as e:
        results.add_test(
            "Component ID Map Creation",
            False,
            f"Exception: {str(e)}"
        )


def test_valid_integer_ids(results: TestResults):
    """Test 2: Valid integer IDs (should pass)"""
    print("\n[TEST 2] Testing valid integer IDs...")

    try:
        id_map = create_component_id_map(SAMPLE_COMPONENTS)
        valid_ids = [0, 1, 2]

        # Validate
        is_valid = validate_component_ids_against_map(valid_ids, id_map)

        if not is_valid:
            results.add_test(
                "Valid Integer IDs",
                False,
                f"Validation failed for valid IDs: {valid_ids}"
            )
            return

        # Normalize
        normalized = normalize_component_ids_by_lookup(valid_ids, id_map)

        if normalized != valid_ids:
            results.add_test(
                "Valid Integer IDs",
                False,
                f"Normalization changed valid IDs: {valid_ids} → {normalized}"
            )
            return

        print(f"✓ Valid IDs passed: {valid_ids}")
        results.add_test(
            "Valid Integer IDs",
            True,
            f"Correctly validated and preserved: {valid_ids}"
        )

    except Exception as e:
        results.add_test(
            "Valid Integer IDs",
            False,
            f"Exception: {str(e)}"
        )


def test_invalid_quoted_integers(results: TestResults):
    """Test 3: Invalid quoted integer strings (should fail validation)"""
    print("\n[TEST 3] Testing invalid quoted integer strings...")

    try:
        id_map = create_component_id_map(SAMPLE_COMPONENTS)
        invalid_ids = ["0", "1", "2"]

        # Validate - should FAIL
        is_valid = validate_component_ids_against_map(invalid_ids, id_map)

        if is_valid:
            results.add_test(
                "Invalid Quoted Integers",
                False,
                f"Validation PASSED for invalid quoted IDs (should fail): {invalid_ids}"
            )
            return

        print(f"✓ Validation correctly rejected quoted integers: {invalid_ids}")

        # Try to normalize - should raise ValueError
        try:
            normalized = normalize_component_ids_by_lookup(invalid_ids, id_map)
            results.add_test(
                "Invalid Quoted Integers",
                False,
                f"Normalization succeeded for invalid IDs (should fail): {invalid_ids} → {normalized}"
            )
        except ValueError as ve:
            print(f"✓ Normalization correctly raised ValueError: {str(ve)}")
            results.add_test(
                "Invalid Quoted Integers",
                True,
                f"Correctly rejected quoted integers: {invalid_ids}"
            )

    except Exception as e:
        results.add_test(
            "Invalid Quoted Integers",
            False,
            f"Unexpected exception: {str(e)}"
        )


def test_invalid_class_names(results: TestResults):
    """Test 4: Invalid class name strings (should fail validation)"""
    print("\n[TEST 4] Testing invalid class name strings...")

    try:
        id_map = create_component_id_map(SAMPLE_COMPONENTS)
        invalid_ids = ["AuthService", "CountedGenericQueryResult"]

        # Validate - should FAIL
        is_valid = validate_component_ids_against_map(invalid_ids, id_map)

        if is_valid:
            results.add_test(
                "Invalid Class Names",
                False,
                f"Validation PASSED for invalid class names (should fail): {invalid_ids}"
            )
            return

        print(f"✓ Validation correctly rejected class names: {invalid_ids}")

        # Try to normalize - should raise ValueError
        try:
            normalized = normalize_component_ids_by_lookup(invalid_ids, id_map)
            results.add_test(
                "Invalid Class Names",
                False,
                f"Normalization succeeded for invalid IDs (should fail): {invalid_ids} → {normalized}"
            )
        except ValueError as ve:
            print(f"✓ Normalization correctly raised ValueError: {str(ve)}")
            results.add_test(
                "Invalid Class Names",
                True,
                f"Correctly rejected class names: {invalid_ids}"
            )

    except Exception as e:
        results.add_test(
            "Invalid Class Names",
            False,
            f"Unexpected exception: {str(e)}"
        )


def test_mixed_invalid_ids(results: TestResults):
    """Test 5: Mixed valid/invalid IDs (should fail validation)"""
    print("\n[TEST 5] Testing mixed valid/invalid IDs...")

    try:
        id_map = create_component_id_map(SAMPLE_COMPONENTS)
        mixed_ids = [0, "1", "AuthService", 999]

        # Validate - should FAIL
        is_valid = validate_component_ids_against_map(mixed_ids, id_map)

        if is_valid:
            results.add_test(
                "Mixed Invalid IDs",
                False,
                f"Validation PASSED for mixed invalid IDs (should fail): {mixed_ids}"
            )
            return

        print(f"✓ Validation correctly rejected mixed invalid IDs: {mixed_ids}")

        # Try to normalize - should raise ValueError
        try:
            normalized = normalize_component_ids_by_lookup(mixed_ids, id_map)
            results.add_test(
                "Mixed Invalid IDs",
                False,
                f"Normalization succeeded for invalid IDs (should fail): {mixed_ids} → {normalized}"
            )
        except ValueError as ve:
            print(f"✓ Normalization correctly raised ValueError: {str(ve)}")
            results.add_test(
                "Mixed Invalid IDs",
                True,
                f"Correctly rejected mixed invalid IDs: {mixed_ids}"
            )

    except Exception as e:
        results.add_test(
            "Mixed Invalid IDs",
            False,
            f"Unexpected exception: {str(e)}"
        )


def test_out_of_range_ids(results: TestResults):
    """Test 6: Out-of-range valid integer IDs (should fail validation)"""
    print("\n[TEST 6] Testing out-of-range integer IDs...")

    try:
        id_map = create_component_id_map(SAMPLE_COMPONENTS)
        out_of_range_ids = [0, 1, 999]  # 999 is out of range

        # Validate - should FAIL
        is_valid = validate_component_ids_against_map(out_of_range_ids, id_map)

        if is_valid:
            results.add_test(
                "Out-of-Range IDs",
                False,
                f"Validation PASSED for out-of-range IDs (should fail): {out_of_range_ids}"
            )
            return

        print(f"✓ Validation correctly rejected out-of-range IDs: {out_of_range_ids}")

        # Try to normalize - should raise ValueError
        try:
            normalized = normalize_component_ids_by_lookup(out_of_range_ids, id_map)
            results.add_test(
                "Out-of-Range IDs",
                False,
                f"Normalization succeeded for invalid IDs (should fail): {out_of_range_ids} → {normalized}"
            )
        except ValueError as ve:
            print(f"✓ Normalization correctly raised ValueError: {str(ve)}")
            results.add_test(
                "Out-of-Range IDs",
                True,
                f"Correctly rejected out-of-range IDs: {out_of_range_ids}"
            )

    except Exception as e:
        results.add_test(
            "Out-of-Range IDs",
            False,
            f"Unexpected exception: {str(e)}"
        )


def test_json_loads_normalization(results: TestResults):
    """Test 7: JSON string parsing with json.loads() approach"""
    print("\n[TEST 7] Testing JSON string parsing with json.loads()...")

    try:
        id_map = create_component_id_map(SAMPLE_COMPONENTS)

        # Simulate LLM response as JSON string
        json_string = "[0, 1, 2]"

        # Parse with json.loads
        parsed_ids = json.loads(json_string)

        # Validate
        is_valid = validate_component_ids_against_map(parsed_ids, id_map)

        if not is_valid:
            results.add_test(
                "JSON Loads Normalization",
                False,
                f"Validation failed for JSON-parsed IDs: {parsed_ids}"
            )
            return

        # Normalize
        normalized = normalize_component_ids_by_lookup(parsed_ids, id_map)

        if normalized != [0, 1, 2]:
            results.add_test(
                "JSON Loads Normalization",
                False,
                f"Normalization failed: {json_string} → {normalized}"
            )
            return

        print(f"✓ JSON string correctly parsed and validated: {json_string} → {normalized}")
        results.add_test(
            "JSON Loads Normalization",
            True,
            f"JSON string correctly parsed: {json_string} → {normalized}"
        )

    except Exception as e:
        results.add_test(
            "JSON Loads Normalization",
            False,
            f"Exception: {str(e)}"
        )


def test_empty_list(results: TestResults):
    """Test 8: Empty component list (edge case)"""
    print("\n[TEST 8] Testing empty component list...")

    try:
        empty_ids = []
        id_map = create_component_id_map(SAMPLE_COMPONENTS)

        # Validate - should PASS (empty list is valid)
        is_valid = validate_component_ids_against_map(empty_ids, id_map)

        if not is_valid:
            results.add_test(
                "Empty List",
                False,
                "Validation failed for empty list (should pass)"
            )
            return

        # Normalize
        normalized = normalize_component_ids_by_lookup(empty_ids, id_map)

        if normalized != []:
            results.add_test(
                "Empty List",
                False,
                f"Normalization failed for empty list: got {normalized}"
            )
            return

        print(f"✓ Empty list correctly handled")
        results.add_test(
            "Empty List",
            True,
            "Empty list correctly validated and normalized"
        )

    except Exception as e:
        results.add_test(
            "Empty List",
            False,
            f"Exception: {str(e)}"
        )


def test_duplicate_ids(results: TestResults):
    """Test 9: Duplicate IDs in list (should pass validation)"""
    print("\n[TEST 9] Testing duplicate IDs...")

    try:
        id_map = create_component_id_map(SAMPLE_COMPONENTS)
        duplicate_ids = [0, 1, 1, 2]

        # Validate - should PASS (duplicates are allowed)
        is_valid = validate_component_ids_against_map(duplicate_ids, id_map)

        if not is_valid:
            results.add_test(
                "Duplicate IDs",
                False,
                f"Validation failed for duplicate IDs (should pass): {duplicate_ids}"
            )
            return

        # Normalize
        normalized = normalize_component_ids_by_lookup(duplicate_ids, id_map)

        if normalized != duplicate_ids:
            results.add_test(
                "Duplicate IDs",
                False,
                f"Normalization changed duplicate IDs: {duplicate_ids} → {normalized}"
            )
            return

        print(f"✓ Duplicate IDs correctly handled: {duplicate_ids}")
        results.add_test(
            "Duplicate IDs",
            True,
            f"Duplicate IDs correctly preserved: {duplicate_ids}"
        )

    except Exception as e:
        results.add_test(
            "Duplicate IDs",
            False,
            f"Exception: {str(e)}"
        )


def test_negative_ids(results: TestResults):
    """Test 10: Negative IDs (should fail validation)"""
    print("\n[TEST 10] Testing negative IDs...")

    try:
        id_map = create_component_id_map(SAMPLE_COMPONENTS)
        negative_ids = [-1, 0, 1]

        # Validate - should FAIL
        is_valid = validate_component_ids_against_map(negative_ids, id_map)

        if is_valid:
            results.add_test(
                "Negative IDs",
                False,
                f"Validation PASSED for negative IDs (should fail): {negative_ids}"
            )
            return

        print(f"✓ Validation correctly rejected negative IDs: {negative_ids}")

        # Try to normalize - should raise ValueError
        try:
            normalized = normalize_component_ids_by_lookup(negative_ids, id_map)
            results.add_test(
                "Negative IDs",
                False,
                f"Normalization succeeded for invalid IDs (should fail): {negative_ids} → {normalized}"
            )
        except ValueError as ve:
            print(f"✓ Normalization correctly raised ValueError: {str(ve)}")
            results.add_test(
                "Negative IDs",
                True,
                f"Correctly rejected negative IDs: {negative_ids}"
            )

    except Exception as e:
        results.add_test(
            "Negative IDs",
            False,
            f"Unexpected exception: {str(e)}"
        )


def main():
    print("="*80)
    print("CodeWiki ID-Based Clustering System - Integration Tests")
    print("="*80)
    print(f"Testing with {len(SAMPLE_COMPONENTS)} sample components")
    print(f"Component names: {[c['name'] for c in SAMPLE_COMPONENTS]}")

    results = TestResults()

    # Run all tests
    test_component_id_map_creation(results)
    test_valid_integer_ids(results)
    test_invalid_quoted_integers(results)
    test_invalid_class_names(results)
    test_mixed_invalid_ids(results)
    test_out_of_range_ids(results)
    test_json_loads_normalization(results)
    test_empty_list(results)
    test_duplicate_ids(results)
    test_negative_ids(results)

    # Print summary
    success = results.print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
