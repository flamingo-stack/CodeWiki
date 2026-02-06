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
from io import StringIO

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


def capture_log_warnings(func):
    """Decorator to capture log warnings"""
    def wrapper(*args, **kwargs):
        # Capture logging output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.WARNING)
        logger = logging.getLogger('codewiki.src.be.cluster_modules')
        logger.addHandler(handler)

        try:
            result = func(*args, **kwargs)
            log_output = log_capture.getvalue()
            return result, log_output
        finally:
            logger.removeHandler(handler)

    return wrapper


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
    """Test 2: Valid integer IDs (should pass without warnings)"""
    print("\n[TEST 2] Testing valid integer IDs...")

    try:
        id_to_fqdn, _ = create_component_id_map(SAMPLE_COMPONENTS)

        # Create module tree with valid IDs
        module_tree = {
            "Auth Module": {
                "components": [0, 1, 2],
                "description": "Authentication components"
            }
        }

        # Normalize
        @capture_log_warnings
        def normalize_test():
            return normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

        normalized, log_output = normalize_test()

        # Check for warnings
        if "❌" in log_output or "⚠️" in log_output:
            results.add_test(
                "Valid Integer IDs",
                False,
                f"Unexpected warnings for valid IDs: {log_output}"
            )
            return

        # Verify normalization
        components = normalized["Auth Module"]["components"]
        if len(components) != 3:
            results.add_test(
                "Valid Integer IDs",
                False,
                f"Expected 3 components, got {len(components)}"
            )
            return

        # Verify FQDNs
        for comp in components:
            if not isinstance(comp, str) or "::" not in comp:
                results.add_test(
                    "Valid Integer IDs",
                    False,
                    f"Invalid FQDN format: {comp}"
                )
                return

        print(f"✓ Valid IDs normalized successfully: [0, 1, 2] → 3 FQDNs")
        results.add_test(
            "Valid Integer IDs",
            True,
            f"Correctly normalized {len(components)} valid IDs"
        )

    except Exception as e:
        results.add_test(
            "Valid Integer IDs",
            False,
            f"Exception: {str(e)}"
        )


def test_invalid_quoted_integers(results: TestResults):
    """Test 3: Quoted integer strings (should ACCEPT via int() conversion)"""
    print("\n[TEST 3] Testing quoted integer strings (resilient handling)...")

    try:
        id_to_fqdn, _ = create_component_id_map(SAMPLE_COMPONENTS)

        # Create module tree with quoted integers (Python's int() converts these)
        module_tree = {
            "Auth Module": {
                "components": ["0", "1", "2"],
                "description": "Authentication components"
            }
        }

        # Normalize
        @capture_log_warnings
        def normalize_test():
            return normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

        normalized, log_output = normalize_test()

        # Should NOT have warnings (int("0") works in Python)
        if "❌" in log_output or "⚠️" in log_output:
            results.add_test(
                "Quoted Integers (Resilient)",
                False,
                f"Unexpected warnings for quoted integers: {log_output}"
            )
            return

        # Components should be successfully normalized (3 components)
        components = normalized["Auth Module"]["components"]
        if len(components) != 3:
            results.add_test(
                "Quoted Integers (Resilient)",
                False,
                f"Expected 3 components, got {len(components)}"
            )
            return

        # Verify FQDNs
        for comp in components:
            if not isinstance(comp, str) or "::" not in comp:
                results.add_test(
                    "Quoted Integers (Resilient)",
                    False,
                    f"Invalid FQDN format: {comp}"
                )
                return

        print(f"✓ Quoted integers correctly converted: [\"0\", \"1\", \"2\"] → 3 FQDNs")
        results.add_test(
            "Quoted Integers (Resilient)",
            True,
            "Correctly converted quoted integers to IDs (resilient behavior)"
        )

    except Exception as e:
        results.add_test(
            "Quoted Integers (Resilient)",
            False,
            f"Exception: {str(e)}"
        )


def test_invalid_class_names(results: TestResults):
    """Test 4: Invalid class name strings (should log warnings)"""
    print("\n[TEST 4] Testing invalid class name strings...")

    try:
        id_to_fqdn, _ = create_component_id_map(SAMPLE_COMPONENTS)

        # Create module tree with class names (INVALID)
        module_tree = {
            "Auth Module": {
                "components": ["AuthService", "CountedGenericQueryResult"],
                "description": "Authentication components"
            }
        }

        # Normalize
        @capture_log_warnings
        def normalize_test():
            return normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

        normalized, log_output = normalize_test()

        # Should have warnings
        if "❌" not in log_output:
            results.add_test(
                "Invalid Class Names",
                False,
                "No warnings logged for class names (should warn)"
            )
            return

        # Should have "Non-integer ID" warnings
        if "Non-integer ID" not in log_output:
            results.add_test(
                "Invalid Class Names",
                False,
                f"Missing 'Non-integer ID' warning. Got: {log_output}"
            )
            return

        # Components should be empty (all failed)
        components = normalized["Auth Module"]["components"]
        if len(components) != 0:
            results.add_test(
                "Invalid Class Names",
                False,
                f"Expected 0 components (all failed), got {len(components)}"
            )
            return

        print(f"✓ Class names correctly rejected with warnings")
        results.add_test(
            "Invalid Class Names",
            True,
            "Correctly rejected class names with warnings"
        )

    except Exception as e:
        results.add_test(
            "Invalid Class Names",
            False,
            f"Exception: {str(e)}"
        )


def test_mixed_invalid_ids(results: TestResults):
    """Test 5: Mixed valid/invalid IDs (should partially normalize)"""
    print("\n[TEST 5] Testing mixed valid/invalid IDs...")

    try:
        id_to_fqdn, _ = create_component_id_map(SAMPLE_COMPONENTS)

        # Create module tree with mixed IDs
        # Note: "1" will be converted to int(1) successfully by Python
        module_tree = {
            "Auth Module": {
                "components": [0, "1", "AuthService", 999],
                "description": "Mixed components"
            }
        }

        # Normalize
        @capture_log_warnings
        def normalize_test():
            return normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

        normalized, log_output = normalize_test()

        # Should have warnings for invalid IDs (AuthService and 999)
        if "❌" not in log_output:
            results.add_test(
                "Mixed Invalid IDs",
                False,
                "No warnings logged for mixed invalid IDs (should warn)"
            )
            return

        # Should have exactly 2 valid components (ID 0 and "1" converted to 1)
        components = normalized["Auth Module"]["components"]
        if len(components) != 2:
            results.add_test(
                "Mixed Invalid IDs",
                False,
                f"Expected 2 valid components (0 and \"1\"), got {len(components)}"
            )
            return

        # Verify the two valid components are IDs 0 and 1
        expected_fqdns = [id_to_fqdn[0], id_to_fqdn[1]]
        if components != expected_fqdns:
            results.add_test(
                "Mixed Invalid IDs",
                False,
                f"Expected FQDNs for IDs 0 and 1, got {components}"
            )
            return

        print(f"✓ Mixed IDs: 2 valid normalized (0, \"1\"), 2 invalid rejected (AuthService, 999)")
        results.add_test(
            "Mixed Invalid IDs",
            True,
            "Correctly normalized valid IDs and rejected invalid IDs"
        )

    except Exception as e:
        results.add_test(
            "Mixed Invalid IDs",
            False,
            f"Exception: {str(e)}"
        )


def test_out_of_range_ids(results: TestResults):
    """Test 6: Out-of-range valid integer IDs (should log warnings)"""
    print("\n[TEST 6] Testing out-of-range integer IDs...")

    try:
        id_to_fqdn, _ = create_component_id_map(SAMPLE_COMPONENTS)

        # Create module tree with out-of-range IDs
        module_tree = {
            "Auth Module": {
                "components": [0, 1, 999],
                "description": "Out of range components"
            }
        }

        # Normalize
        @capture_log_warnings
        def normalize_test():
            return normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

        normalized, log_output = normalize_test()

        # Should have warnings for out-of-range
        if "❌" not in log_output or "Invalid ID 999" not in log_output:
            results.add_test(
                "Out-of-Range IDs",
                False,
                "Missing warning for out-of-range ID 999"
            )
            return

        # Should have "Valid range" in warning
        if "Valid range" not in log_output:
            results.add_test(
                "Out-of-Range IDs",
                False,
                f"Missing 'Valid range' in warning. Got: {log_output}"
            )
            return

        # Should have 2 valid components (0, 1)
        components = normalized["Auth Module"]["components"]
        if len(components) != 2:
            results.add_test(
                "Out-of-Range IDs",
                False,
                f"Expected 2 valid components, got {len(components)}"
            )
            return

        print(f"✓ Out-of-range ID rejected: 2 valid, 1 rejected")
        results.add_test(
            "Out-of-Range IDs",
            True,
            "Correctly rejected out-of-range ID with warning"
        )

    except Exception as e:
        results.add_test(
            "Out-of-Range IDs",
            False,
            f"Exception: {str(e)}"
        )


def test_json_loads_normalization(results: TestResults):
    """Test 7: JSON string parsing with json.loads() approach"""
    print("\n[TEST 7] Testing JSON string parsing with json.loads()...")

    try:
        id_to_fqdn, _ = create_component_id_map(SAMPLE_COMPONENTS)

        # Simulate LLM response as JSON string
        json_string = "[0, 1, 2]"
        parsed_ids = json.loads(json_string)

        # Create module tree with parsed IDs
        module_tree = {
            "Auth Module": {
                "components": parsed_ids,
                "description": "JSON parsed components"
            }
        }

        # Normalize
        @capture_log_warnings
        def normalize_test():
            return normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

        normalized, log_output = normalize_test()

        # Should NOT have warnings
        if "❌" in log_output or "⚠️" in log_output:
            results.add_test(
                "JSON Loads Normalization",
                False,
                f"Unexpected warnings: {log_output}"
            )
            return

        # Should have 3 valid components
        components = normalized["Auth Module"]["components"]
        if len(components) != 3:
            results.add_test(
                "JSON Loads Normalization",
                False,
                f"Expected 3 components, got {len(components)}"
            )
            return

        print(f"✓ JSON string correctly parsed and normalized")
        results.add_test(
            "JSON Loads Normalization",
            True,
            f"JSON string successfully parsed: {json_string} → 3 FQDNs"
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
        id_to_fqdn, _ = create_component_id_map(SAMPLE_COMPONENTS)

        # Create module tree with empty components
        module_tree = {
            "Empty Module": {
                "components": [],
                "description": "No components"
            }
        }

        # Normalize
        @capture_log_warnings
        def normalize_test():
            return normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

        normalized, log_output = normalize_test()

        # Should NOT have warnings
        if "❌" in log_output:
            results.add_test(
                "Empty List",
                False,
                f"Unexpected warnings for empty list: {log_output}"
            )
            return

        # Components should still be empty
        components = normalized["Empty Module"]["components"]
        if len(components) != 0:
            results.add_test(
                "Empty List",
                False,
                f"Expected 0 components, got {len(components)}"
            )
            return

        print(f"✓ Empty list correctly handled")
        results.add_test(
            "Empty List",
            True,
            "Empty list correctly handled without warnings"
        )

    except Exception as e:
        results.add_test(
            "Empty List",
            False,
            f"Exception: {str(e)}"
        )


def test_duplicate_ids(results: TestResults):
    """Test 9: Duplicate IDs in list (should allow duplicates)"""
    print("\n[TEST 9] Testing duplicate IDs...")

    try:
        id_to_fqdn, _ = create_component_id_map(SAMPLE_COMPONENTS)

        # Create module tree with duplicate IDs
        module_tree = {
            "Duplicate Module": {
                "components": [0, 1, 1, 2],
                "description": "Duplicate components"
            }
        }

        # Normalize
        @capture_log_warnings
        def normalize_test():
            return normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

        normalized, log_output = normalize_test()

        # Should NOT have warnings
        if "❌" in log_output or "⚠️" in log_output:
            results.add_test(
                "Duplicate IDs",
                False,
                f"Unexpected warnings for duplicates: {log_output}"
            )
            return

        # Should have 4 components (duplicates preserved)
        components = normalized["Duplicate Module"]["components"]
        if len(components) != 4:
            results.add_test(
                "Duplicate IDs",
                False,
                f"Expected 4 components (with duplicates), got {len(components)}"
            )
            return

        # Verify duplicate FQDN
        fqdn_1 = id_to_fqdn[1]
        if components.count(fqdn_1) != 2:
            results.add_test(
                "Duplicate IDs",
                False,
                f"Expected 2 instances of FQDN for ID 1, got {components.count(fqdn_1)}"
            )
            return

        print(f"✓ Duplicate IDs correctly preserved")
        results.add_test(
            "Duplicate IDs",
            True,
            "Duplicate IDs correctly preserved in normalization"
        )

    except Exception as e:
        results.add_test(
            "Duplicate IDs",
            False,
            f"Exception: {str(e)}"
        )


def test_negative_ids(results: TestResults):
    """Test 10: Negative IDs (should log warnings)"""
    print("\n[TEST 10] Testing negative IDs...")

    try:
        id_to_fqdn, _ = create_component_id_map(SAMPLE_COMPONENTS)

        # Create module tree with negative IDs
        module_tree = {
            "Negative Module": {
                "components": [-1, 0, 1],
                "description": "Negative IDs"
            }
        }

        # Normalize
        @capture_log_warnings
        def normalize_test():
            return normalize_component_ids_by_lookup(module_tree, id_to_fqdn)

        normalized, log_output = normalize_test()

        # Should have warnings for negative ID
        if "❌" not in log_output or "Invalid ID -1" not in log_output:
            results.add_test(
                "Negative IDs",
                False,
                "Missing warning for negative ID -1"
            )
            return

        # Should have 2 valid components (0, 1)
        components = normalized["Negative Module"]["components"]
        if len(components) != 2:
            results.add_test(
                "Negative IDs",
                False,
                f"Expected 2 valid components, got {len(components)}"
            )
            return

        print(f"✓ Negative ID rejected: 2 valid, 1 rejected")
        results.add_test(
            "Negative IDs",
            True,
            "Correctly rejected negative ID with warning"
        )

    except Exception as e:
        results.add_test(
            "Negative IDs",
            False,
            f"Exception: {str(e)}"
        )


def main():
    print("="*80)
    print("CodeWiki ID-Based Clustering System - Integration Tests")
    print("="*80)
    print(f"Testing with {len(SAMPLE_COMPONENTS)} sample components")
    print(f"Component names: {[SAMPLE_COMPONENTS[k].name for k in sorted(SAMPLE_COMPONENTS.keys())]}")

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
