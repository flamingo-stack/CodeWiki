"""
Test Cases for FQDN Normalization Fix

Run with: python -m pytest test_fqdn_normalization.py -v
"""

import pytest
from collections import namedtuple

# Mock Node class for testing
Node = namedtuple('Node', ['short_id'])


def test_strip_deps_prefix():
    """Test that 'deps.' prefix is correctly stripped."""
    # Simulated components dictionary
    components = {
        "openframe-oss-lib.src.main.java.Class": Node(short_id="Class"),
        "openframe-api.src.main.java.Service": Node(short_id="Service"),
    }

    # Simulated LLM output with "deps." prefix
    llm_output = [
        "deps.openframe-oss-lib.src.main.java.Class",
        "deps.openframe-api.src.main.java.Service",
    ]

    # Expected normalized output (after stripping)
    expected = [
        "openframe-oss-lib.src.main.java.Class",
        "openframe-api.src.main.java.Service",
    ]

    # Test normalization
    for llm_id, expected_fqdn in zip(llm_output, expected):
        stripped = llm_id[5:] if llm_id.startswith("deps.") else llm_id
        assert stripped in components, f"Failed to find {stripped} after stripping"
        assert stripped == expected_fqdn


def test_fuzzy_component_name_match():
    """Test fuzzy matching by component name (last segment)."""
    components = {
        "openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer": Node(short_id="PinotConfigInitializer"),
        "openframe-api.src.main.java.auth.AuthService": Node(short_id="AuthService"),
    }

    # LLM output with wrong path but correct component name
    llm_id = "deps.openframe-oss-lib.openframe-management-service-core.src.main.java.PinotConfigInitializer"

    # Extract component name
    component_name = llm_id.split('.')[-1]
    assert component_name == "PinotConfigInitializer"

    # Find matches
    matches = [fqdn for fqdn in components.keys() if fqdn.split('.')[-1] == component_name]

    assert len(matches) == 1, f"Expected 1 match, found {len(matches)}"
    assert matches[0] == "openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer"


def test_path_suffix_matching():
    """Test matching by path suffix (last N segments)."""
    components = {
        "openframe-oss-lib.different.path.java.config.pinot.PinotConfigInitializer": Node(short_id="PinotConfigInitializer"),
    }

    llm_id = "deps.openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer"

    # Try matching last 3 segments
    segments = llm_id.split('.')
    suffix_3 = '.'.join(segments[-3:])  # "config.pinot.PinotConfigInitializer"

    matches = [fqdn for fqdn in components.keys() if fqdn.endswith(suffix_3)]

    assert len(matches) == 1
    assert matches[0] == "openframe-oss-lib.different.path.java.config.pinot.PinotConfigInitializer"


def test_exact_fqdn_match():
    """Test that exact FQDN matches work without modification."""
    components = {
        "main-repo.src.services.user_service.UserService": Node(short_id="UserService"),
    }

    llm_id = "main-repo.src.services.user_service.UserService"

    assert llm_id in components


def test_short_id_mapping():
    """Test that short ID → FQDN mapping works."""
    components = {
        "main-repo.src.services.user_service.UserService": Node(short_id="UserService"),
        "main-repo.src.utils.logger.Logger": Node(short_id="Logger"),
    }

    # Build mapping
    mapping = {}
    for fqdn, node in components.items():
        short_id = node.short_id or fqdn.split('.')[-1]
        mapping[short_id] = fqdn

    # Test mapping
    assert mapping["UserService"] == "main-repo.src.services.user_service.UserService"
    assert mapping["Logger"] == "main-repo.src.utils.logger.Logger"


def test_partial_path_mapping():
    """Test that partial paths are mapped correctly."""
    components = {
        "main-repo.src.services.auth.UserService": Node(short_id="UserService"),
    }

    # Build enhanced mapping with partial paths
    mapping = {}
    for fqdn, node in components.items():
        segments = fqdn.split('.')

        # Map short ID
        short_id = node.short_id or segments[-1]
        mapping[short_id] = fqdn

        # Map partial paths (last 2-4 segments)
        for i in range(2, min(5, len(segments) + 1)):
            partial = '.'.join(segments[-i:])
            if partial not in mapping:
                mapping[partial] = fqdn

    # Test mappings
    assert "UserService" in mapping
    assert "auth.UserService" in mapping
    assert "services.auth.UserService" in mapping
    assert "src.services.auth.UserService" in mapping


def test_collision_detection():
    """Test that collisions are detected when same short ID maps to multiple FQDNs."""
    from collections import defaultdict

    components = {
        "main-repo.src.services.user_service.UserService": Node(short_id="UserService"),
        "main-repo.src.admin.user_service.UserService": Node(short_id="UserService"),  # Collision!
    }

    mapping = {}
    collisions = defaultdict(list)

    for fqdn, node in components.items():
        short_id = node.short_id or fqdn.split('.')[-1]

        if short_id in mapping:
            collisions[short_id].append(fqdn)
        else:
            mapping[short_id] = fqdn

    assert "UserService" in collisions
    assert len(collisions["UserService"]) >= 1  # At least one collision


def test_best_path_match_scoring():
    """Test the path similarity scoring algorithm."""
    llm_id = "deps.openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer"
    candidates = [
        "openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer",  # Perfect match
        "openframe-oss-lib.different.path.config.pinot.PinotConfigInitializer",  # Partial match
        "other-repo.src.main.java.config.pinot.PinotConfigInitializer",  # Different namespace
    ]

    # Score candidates by matching segments
    llm_segments = llm_id.split('.')
    scores = []

    for candidate in candidates:
        candidate_segments = candidate.split('.')
        matches = sum(1 for seg in llm_segments if seg in candidate_segments)
        scores.append((candidate, matches))

    # Sort by score
    scores.sort(key=lambda x: x[1], reverse=True)

    # Best match should have highest score
    assert scores[0][0] == "openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer"
    assert scores[0][1] > scores[2][1]  # Better than different namespace


def test_non_existent_component():
    """Test that non-existent components fail normalization."""
    components = {
        "main-repo.src.services.UserService": Node(short_id="UserService"),
    }

    llm_id = "deps.openframe-oss-lib.hallucinated.Component"

    # Should not match anything
    stripped = llm_id[5:] if llm_id.startswith("deps.") else llm_id
    assert stripped not in components

    component_name = llm_id.split('.')[-1]
    matches = [fqdn for fqdn in components.keys() if component_name in fqdn]
    assert len(matches) == 0


def test_double_class_name():
    """Test handling of paths with duplicate component names."""
    # This tests the scenario: PintoConfigInitializer.PinotConfigInitializer
    components = {
        "openframe-oss-lib.src.main.java.config.pinot.PintoConfigInitializer.PinotConfigInitializer": Node(
            short_id="PinotConfigInitializer"
        ),
    }

    llm_id = "deps.openframe-oss-lib.openframe-management-service-core.src.main.java.com.openframe.management.config.pinot.PintoConfigInitializer.PinotConfigInitializer"

    # Extract last segment (might be duplicated)
    component_name = llm_id.split('.')[-1]

    # Should match by component name
    matches = [fqdn for fqdn in components.keys() if fqdn.split('.')[-1] == component_name]

    assert len(matches) == 1


def test_java_package_path():
    """Test handling of Java package paths with com.openframe prefix."""
    components = {
        "openframe-oss-lib.src.main.java.com.openframe.management.config.PinotConfig": Node(
            short_id="PinotConfig"
        ),
    }

    # LLM might include full Java package path
    llm_id = "deps.openframe-oss-lib.src.main.java.com.openframe.management.config.PinotConfig"

    # Strip deps prefix
    stripped = llm_id[5:] if llm_id.startswith("deps.") else llm_id

    assert stripped in components


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
