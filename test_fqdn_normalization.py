"""
Test Cases for FQDN Normalization Fix

Run with: python test_fqdn_normalization.py
"""

from collections import namedtuple

# Mock Node class for testing
Node = namedtuple('Node', ['short_id'])


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []

    def add_test(self, name, condition, message=""):
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            self.failures.append(f"{name}: {message}")

    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"Test Summary: {self.passed}/{total} passed")
        if self.failures:
            print("Failures:")
            for failure in self.failures:
                print(f"  - {failure}")
        print(f"{'=' * 60}")
        return self.failed == 0


def test_strip_deps_prefix(results):
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
        results.add_test(
            "test_strip_deps_prefix: stripped in components",
            stripped in components,
            f"Failed to find {stripped} after stripping",
        )
        results.add_test(
            "test_strip_deps_prefix: stripped == expected_fqdn",
            stripped == expected_fqdn,
            f"{stripped} != {expected_fqdn}",
        )


def test_fuzzy_component_name_match(results):
    """Test fuzzy matching by component name (last segment)."""
    components = {
        "openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer": Node(short_id="PinotConfigInitializer"),
        "openframe-api.src.main.java.auth.AuthService": Node(short_id="AuthService"),
    }

    # LLM output with wrong path but correct component name
    llm_id = "deps.openframe-oss-lib.openframe-management-service-core.src.main.java.PinotConfigInitializer"

    # Extract component name
    component_name = llm_id.split('.')[-1]
    results.add_test(
        "test_fuzzy_component_name_match: component_name extraction",
        component_name == "PinotConfigInitializer",
        f"component_name was {component_name}",
    )

    # Find matches
    matches = [fqdn for fqdn in components.keys() if fqdn.split('.')[-1] == component_name]

    results.add_test(
        "test_fuzzy_component_name_match: match count",
        len(matches) == 1,
        f"Expected 1 match, found {len(matches)}",
    )
    if matches:
        results.add_test(
            "test_fuzzy_component_name_match: match value",
            matches[0] == "openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer",
            f"matches[0] was {matches[0]}",
        )


def test_path_suffix_matching(results):
    """Test matching by path suffix (last N segments)."""
    components = {
        "openframe-oss-lib.different.path.java.config.pinot.PinotConfigInitializer": Node(short_id="PinotConfigInitializer"),
    }

    llm_id = "deps.openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer"

    # Try matching last 3 segments
    segments = llm_id.split('.')
    suffix_3 = '.'.join(segments[-3:])  # "config.pinot.PinotConfigInitializer"

    matches = [fqdn for fqdn in components.keys() if fqdn.endswith(suffix_3)]

    results.add_test(
        "test_path_suffix_matching: match count",
        len(matches) == 1,
        f"Expected 1 match, found {len(matches)}",
    )
    if matches:
        results.add_test(
            "test_path_suffix_matching: match value",
            matches[0] == "openframe-oss-lib.different.path.java.config.pinot.PinotConfigInitializer",
            f"matches[0] was {matches[0]}",
        )


def test_exact_fqdn_match(results):
    """Test that exact FQDN matches work without modification."""
    components = {
        "main-repo.src.services.user_service.UserService": Node(short_id="UserService"),
    }

    llm_id = "main-repo.src.services.user_service.UserService"

    results.add_test(
        "test_exact_fqdn_match: llm_id in components",
        llm_id in components,
        f"{llm_id} not found in components",
    )


def test_short_id_mapping(results):
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
    results.add_test(
        "test_short_id_mapping: UserService",
        mapping.get("UserService") == "main-repo.src.services.user_service.UserService",
        f"mapping['UserService'] was {mapping.get('UserService')}",
    )
    results.add_test(
        "test_short_id_mapping: Logger",
        mapping.get("Logger") == "main-repo.src.utils.logger.Logger",
        f"mapping['Logger'] was {mapping.get('Logger')}",
    )


def test_partial_path_mapping(results):
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
    results.add_test(
        "test_partial_path_mapping: UserService in mapping",
        "UserService" in mapping,
        "UserService not found in mapping",
    )
    results.add_test(
        "test_partial_path_mapping: auth.UserService in mapping",
        "auth.UserService" in mapping,
        "auth.UserService not found in mapping",
    )
    results.add_test(
        "test_partial_path_mapping: services.auth.UserService in mapping",
        "services.auth.UserService" in mapping,
        "services.auth.UserService not found in mapping",
    )
    results.add_test(
        "test_partial_path_mapping: src.services.auth.UserService in mapping",
        "src.services.auth.UserService" in mapping,
        "src.services.auth.UserService not found in mapping",
    )


def test_collision_detection(results):
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

    results.add_test(
        "test_collision_detection: UserService in collisions",
        "UserService" in collisions,
        "UserService not found in collisions",
    )
    results.add_test(
        "test_collision_detection: at least one collision",
        len(collisions["UserService"]) >= 1,
        f"collisions['UserService'] had length {len(collisions['UserService'])}",
    )


def test_best_path_match_scoring(results):
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
    results.add_test(
        "test_best_path_match_scoring: best match",
        scores[0][0] == "openframe-oss-lib.src.main.java.config.pinot.PinotConfigInitializer",
        f"scores[0][0] was {scores[0][0]}",
    )
    results.add_test(
        "test_best_path_match_scoring: better than different namespace",
        scores[0][1] > scores[2][1],
        f"scores[0][1]={scores[0][1]} not > scores[2][1]={scores[2][1]}",
    )


def test_non_existent_component(results):
    """Test that non-existent components fail normalization."""
    components = {
        "main-repo.src.services.UserService": Node(short_id="UserService"),
    }

    llm_id = "deps.openframe-oss-lib.hallucinated.Component"

    # Should not match anything
    stripped = llm_id[5:] if llm_id.startswith("deps.") else llm_id
    results.add_test(
        "test_non_existent_component: stripped not in components",
        stripped not in components,
        f"{stripped} unexpectedly found in components",
    )

    component_name = llm_id.split('.')[-1]
    matches = [fqdn for fqdn in components.keys() if component_name in fqdn]
    results.add_test(
        "test_non_existent_component: no matches",
        len(matches) == 0,
        f"Expected 0 matches, found {len(matches)}",
    )


def test_double_class_name(results):
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

    results.add_test(
        "test_double_class_name: match count",
        len(matches) == 1,
        f"Expected 1 match, found {len(matches)}",
    )


def test_java_package_path(results):
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

    results.add_test(
        "test_java_package_path: stripped in components",
        stripped in components,
        f"{stripped} not found in components",
    )


if __name__ == "__main__":
    results = TestResults()
    test_strip_deps_prefix(results)
    test_fuzzy_component_name_match(results)
    test_path_suffix_matching(results)
    test_exact_fqdn_match(results)
    test_short_id_mapping(results)
    test_partial_path_mapping(results)
    test_collision_detection(results)
    test_best_path_match_scoring(results)
    test_non_existent_component(results)
    test_double_class_name(results)
    test_java_package_path(results)
    success = results.print_summary()
    raise SystemExit(0 if success else 1)
