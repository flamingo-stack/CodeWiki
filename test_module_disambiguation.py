#!/usr/bin/env python3
"""
Test demonstrating the module-context disambiguation fix for CodeWiki.

This test shows how the enhanced _find_best_path_match() function now uses
module name context to resolve ambiguous component matches like DeviceController.
"""

import sys
import logging
from typing import List, Optional

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def _find_best_path_match_original(llm_id: str, candidates: List[str]) -> Optional[str]:
    """Original implementation WITHOUT module context."""
    llm_segments = llm_id.split('.')

    scores = []
    for candidate in candidates:
        candidate_segments = candidate.split('.')
        matches = 0
        for i, llm_seg in enumerate(llm_segments):
            if llm_seg in candidate_segments:
                try:
                    candidate_idx = candidate_segments.index(llm_seg)
                    position_diff = abs(i - candidate_idx)
                    matches += 1 + (1.0 / (1 + position_diff))
                except ValueError:
                    pass
        scores.append((candidate, matches))

    scores.sort(key=lambda x: x[1], reverse=True)

    if len(scores) > 1 and scores[0][1] > scores[1][1]:
        logger.debug(f"Original - Best match score: {scores[0][1]:.2f} vs next: {scores[1][1]:.2f}")
        return scores[0][0]

    return None


def _find_best_path_match_enhanced(llm_id: str, candidates: List[str], module_name: str = None) -> Optional[str]:
    """Enhanced implementation WITH module context."""
    llm_segments = llm_id.split('.')

    module_segments = []
    if module_name:
        module_segments = module_name.replace('_', '-').split('-')
        module_segments = [seg.lower() for seg in module_segments if seg]

    scores = []
    for candidate in candidates:
        candidate_segments = candidate.split('.')
        matches = 0
        for i, llm_seg in enumerate(llm_segments):
            if llm_seg in candidate_segments:
                try:
                    candidate_idx = candidate_segments.index(llm_seg)
                    position_diff = abs(i - candidate_idx)
                    matches += 1 + (1.0 / (1 + position_diff))
                except ValueError:
                    pass

        # Module context boost
        if module_segments:
            candidate_lower = candidate.lower()
            candidate_path_parts = candidate_lower.replace('.', '-').replace('_', '-').split('-')

            module_boost = 0
            extra_segments_penalty = 0

            # Try to find exact consecutive match
            for i in range(len(candidate_path_parts) - len(module_segments) + 1):
                window = candidate_path_parts[i:i + len(module_segments)]
                if window == module_segments:
                    module_boost = len(module_segments) * 3.0
                    logger.debug(
                        f"Enhanced - EXACT module match for '{candidate}': "
                        f"segments {module_segments} at position {i}, +{module_boost:.1f} points"
                    )
                    break

            # If no exact match, count individual segments with penalty
            if module_boost == 0:
                matched_segments = []
                for module_seg in module_segments:
                    if module_seg in candidate_path_parts:
                        matched_segments.append(module_seg)
                        module_boost += 1.5

                if matched_segments:
                    extra_segments = [seg for seg in candidate_path_parts if seg not in module_segments]
                    if len(extra_segments) > 10:
                        extra_segments_penalty = len(extra_segments) * 0.3
                    module_boost -= extra_segments_penalty

                    logger.debug(
                        f"Enhanced - Partial module match for '{candidate}': "
                        f"{len(matched_segments)}/{len(module_segments)} segments, "
                        f"penalty -{extra_segments_penalty:.1f}, net +{module_boost:.1f} points"
                    )

            matches += module_boost

        scores.append((candidate, matches))

    scores.sort(key=lambda x: x[1], reverse=True)

    if len(scores) > 1 and scores[0][1] > scores[1][1]:
        logger.debug(
            f"Enhanced - Winner: {scores[0][0]} (score: {scores[0][1]:.2f}) "
            f"vs runner-up: {scores[1][0]} (score: {scores[1][1]:.2f})"
        )
        return scores[0][0]

    return None


def test_device_controller_disambiguation():
    """Test the exact scenario from the production bug."""
    print("\n" + "="*80)
    print("TEST: DeviceController Disambiguation")
    print("="*80)

    # Real data from production logs
    llm_id = "DeviceController"
    module_name = "openframe-api-service"
    candidates = [
        "deps.openframe-oss-lib.openframe-api-service-core.src.main.java.com.openframe.api.controller.DeviceController.DeviceController",
        "deps.openframe-oss-lib.openframe-external-api-service-core.src.main.java.com.openframe.external.controller.DeviceController.DeviceController"
    ]

    print(f"\nContext:")
    print(f"  LLM returned: '{llm_id}'")
    print(f"  Module: '{module_name}'")
    print(f"  Candidates:")
    for i, c in enumerate(candidates, 1):
        print(f"    {i}. {c}")

    # Test original implementation (should fail)
    print(f"\n{'-'*80}")
    print("ORIGINAL Implementation (no module context):")
    print(f"{'-'*80}")
    original_result = _find_best_path_match_original(llm_id, candidates)
    if original_result is None:
        print("❌ Result: None (AMBIGUOUS - failed to resolve)")
    else:
        print(f"✅ Result: {original_result}")

    # Test enhanced implementation (should succeed)
    print(f"\n{'-'*80}")
    print("ENHANCED Implementation (with module context):")
    print(f"{'-'*80}")
    enhanced_result = _find_best_path_match_enhanced(llm_id, candidates, module_name)
    if enhanced_result is None:
        print("❌ Result: None (AMBIGUOUS)")
    else:
        print(f"✅ Result: {enhanced_result}")

        # Verify correct match
        expected = candidates[0]  # Should match openframe-api-service, not openframe-external-api-service
        if enhanced_result == expected:
            print("✅ CORRECT: Matched to openframe-api-service variant (expected)")
        else:
            print("❌ WRONG: Matched to openframe-external-api-service variant (unexpected)")

    return original_result, enhanced_result


def test_external_api_disambiguation():
    """Test disambiguation for openframe-external-api-service module."""
    print("\n" + "="*80)
    print("TEST: DeviceController for External API Service")
    print("="*80)

    llm_id = "DeviceController"
    module_name = "openframe-external-api-service"
    candidates = [
        "deps.openframe-oss-lib.openframe-api-service-core.src.main.java.com.openframe.api.controller.DeviceController.DeviceController",
        "deps.openframe-oss-lib.openframe-external-api-service-core.src.main.java.com.openframe.external.controller.DeviceController.DeviceController"
    ]

    print(f"\nContext:")
    print(f"  LLM returned: '{llm_id}'")
    print(f"  Module: '{module_name}'")

    print(f"\n{'-'*80}")
    print("ENHANCED Implementation (should match external variant):")
    print(f"{'-'*80}")
    enhanced_result = _find_best_path_match_enhanced(llm_id, candidates, module_name)
    if enhanced_result is None:
        print("❌ Result: None (AMBIGUOUS)")
    else:
        print(f"✅ Result: {enhanced_result}")

        # Verify correct match
        expected = candidates[1]  # Should match openframe-external-api-service
        if enhanced_result == expected:
            print("✅ CORRECT: Matched to openframe-external-api-service variant (expected)")
        else:
            print("❌ WRONG: Matched to openframe-api-service variant (unexpected)")

    return enhanced_result


def test_security_config_disambiguation():
    """Test disambiguation for SecurityConfig (another common ambiguous case)."""
    print("\n" + "="*80)
    print("TEST: SecurityConfig Disambiguation")
    print("="*80)

    llm_id = "SecurityConfig"
    module_name = "openframe-gateway-service"
    candidates = [
        "deps.openframe-oss-lib.openframe-gateway-service-core.src.main.java.com.openframe.gateway.config.SecurityConfig.SecurityConfig",
        "deps.openframe-oss-lib.openframe-api-service-core.src.main.java.com.openframe.api.config.SecurityConfig.SecurityConfig",
        "deps.openframe-oss-lib.openframe-auth-service-core.src.main.java.com.openframe.auth.config.SecurityConfig.SecurityConfig"
    ]

    print(f"\nContext:")
    print(f"  LLM returned: '{llm_id}'")
    print(f"  Module: '{module_name}'")
    print(f"  Candidates:")
    for i, c in enumerate(candidates, 1):
        print(f"    {i}. {c}")

    print(f"\n{'-'*80}")
    print("ENHANCED Implementation:")
    print(f"{'-'*80}")
    enhanced_result = _find_best_path_match_enhanced(llm_id, candidates, module_name)
    if enhanced_result is None:
        print("❌ Result: None (AMBIGUOUS)")
    else:
        print(f"✅ Result: {enhanced_result}")

        # Verify correct match
        expected = candidates[0]  # Should match openframe-gateway-service
        if enhanced_result == expected:
            print("✅ CORRECT: Matched to openframe-gateway-service variant (expected)")
        else:
            print("❌ WRONG: Did not match gateway variant")

    return enhanced_result


def main():
    print("\n" + "="*80)
    print("CodeWiki Module Disambiguation Enhancement Test")
    print("="*80)
    print("\nThis test demonstrates the fix for ambiguous component resolution")
    print("by using module name context to disambiguate candidates.")

    # Run all tests
    tests_passed = 0
    tests_failed = 0

    # Test 1: DeviceController for openframe-api-service
    orig_result, enh_result = test_device_controller_disambiguation()
    if orig_result is None and enh_result is not None:
        tests_passed += 1
        print("\n✅ Test 1 PASSED: Original failed (ambiguous), Enhanced succeeded")
    else:
        tests_failed += 1
        print("\n❌ Test 1 FAILED")

    # Test 2: DeviceController for openframe-external-api-service
    ext_result = test_external_api_disambiguation()
    if ext_result and "external" in ext_result:
        tests_passed += 1
        print("\n✅ Test 2 PASSED: Correctly matched external variant")
    else:
        tests_failed += 1
        print("\n❌ Test 2 FAILED")

    # Test 3: SecurityConfig for openframe-gateway-service
    sec_result = test_security_config_disambiguation()
    if sec_result and "gateway" in sec_result:
        tests_passed += 1
        print("\n✅ Test 3 PASSED: Correctly matched gateway variant")
    else:
        tests_failed += 1
        print("\n❌ Test 3 FAILED")

    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    print(f"✅ Passed: {tests_passed}/3")
    print(f"❌ Failed: {tests_failed}/3")

    if tests_failed == 0:
        print("\n🎉 All tests passed! Module disambiguation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
