"""
FQDN Normalization Fix - Enhanced Component ID Resolution

This file contains the proposed fix for cluster_modules.py to handle:
1. LLM-added "deps." prefixes
2. Fuzzy substring matching for nested paths
3. Enhanced debugging and logging
4. Partial path matching for complex Java packages

Replace the normalization loop in cluster_modules.py:212-233 with this code.
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def normalize_component_ids_enhanced(
    module_tree: Dict,
    components: Dict,
    short_to_fqdn: Dict[str, str]
) -> tuple[int, int]:
    """
    Enhanced component ID normalization with multiple fallback strategies.

    Args:
        module_tree: Module tree with component IDs from LLM
        components: Dictionary of actual components (FQDN → Node)
        short_to_fqdn: Mapping of short IDs to FQDNs

    Returns:
        Tuple of (total_normalized, total_failed)
    """
    total_normalized = 0
    total_failed = 0

    for module_name, module_data in module_tree.items():
        original_components = module_data.get('components', [])
        normalized_components = []

        for comp_id in original_components:
            # Strategy 1: Exact FQDN match
            if comp_id in components:
                normalized_components.append(comp_id)
                logger.debug(f"   ✅ Exact match: '{comp_id}'")
                continue

            # Strategy 2: Short ID mapping
            if comp_id in short_to_fqdn:
                fqdn = short_to_fqdn[comp_id]
                normalized_components.append(fqdn)
                total_normalized += 1
                logger.debug(f"   ✅ Mapped '{comp_id}' → '{fqdn}'")
                continue

            # Strategy 3: Strip "deps." prefix and retry
            stripped_id = comp_id
            if comp_id.startswith("deps."):
                stripped_id = comp_id[5:]  # Remove "deps." prefix
                logger.debug(f"   🔧 Stripping 'deps.' prefix: '{comp_id}' → '{stripped_id}'")

                # Try exact match with stripped ID
                if stripped_id in components:
                    normalized_components.append(stripped_id)
                    total_normalized += 1
                    logger.info(
                        f"   ✅ Found after stripping 'deps.' prefix:\n"
                        f"      LLM returned: '{comp_id}'\n"
                        f"      Actual FQDN:  '{stripped_id}'"
                    )
                    continue

                # Try short_id mapping with stripped ID
                if stripped_id in short_to_fqdn:
                    fqdn = short_to_fqdn[stripped_id]
                    normalized_components.append(fqdn)
                    total_normalized += 1
                    logger.info(
                        f"   ✅ Mapped after stripping prefix:\n"
                        f"      LLM returned: '{comp_id}'\n"
                        f"      Stripped to:  '{stripped_id}'\n"
                        f"      Mapped to:    '{fqdn}'"
                    )
                    continue

            # Strategy 4: Fuzzy substring matching on component name
            # Extract the likely component name (last segment)
            component_name = comp_id.split('.')[-1]

            # Search for FQDNs ending with this component name
            fuzzy_matches = [
                fqdn for fqdn in components.keys()
                if fqdn.split('.')[-1] == component_name
            ]

            if len(fuzzy_matches) == 1:
                # Unique match found
                normalized_components.append(fuzzy_matches[0])
                total_normalized += 1
                logger.info(
                    f"   ✅ Fuzzy matched by component name:\n"
                    f"      LLM returned:  '{comp_id}'\n"
                    f"      Component:     '{component_name}'\n"
                    f"      Matched FQDN:  '{fuzzy_matches[0]}'"
                )
                continue
            elif len(fuzzy_matches) > 1:
                # Multiple matches - try to find best match by path similarity
                best_match = _find_best_path_match(comp_id, fuzzy_matches)
                if best_match:
                    normalized_components.append(best_match)
                    total_normalized += 1
                    logger.info(
                        f"   ✅ Best fuzzy match from {len(fuzzy_matches)} candidates:\n"
                        f"      LLM returned: '{comp_id}'\n"
                        f"      Matched FQDN: '{best_match}'"
                    )
                    continue
                else:
                    logger.warning(
                        f"   ⚠️  Multiple ambiguous fuzzy matches for '{comp_id}':\n"
                        f"      Component: '{component_name}'\n"
                        f"      Candidates:\n" +
                        '\n'.join(f"        - {m}" for m in fuzzy_matches[:5]) +
                        (f"\n        ... and {len(fuzzy_matches) - 5} more" if len(fuzzy_matches) > 5 else "")
                    )

            # Strategy 5: Try matching by suffix path (last N segments)
            # This handles cases where LLM includes partial path
            # Example: "deps.openframe-oss-lib.src.main.java.Class"
            #          should match "openframe-oss-lib.different.path.java.Class"
            if '.' in comp_id:
                # Try matching last 2-4 segments
                segments = comp_id.split('.')
                for n in range(2, min(5, len(segments) + 1)):
                    suffix = '.'.join(segments[-n:])
                    suffix_matches = [
                        fqdn for fqdn in components.keys()
                        if fqdn.endswith(suffix)
                    ]
                    if len(suffix_matches) == 1:
                        normalized_components.append(suffix_matches[0])
                        total_normalized += 1
                        logger.info(
                            f"   ✅ Matched by path suffix:\n"
                            f"      LLM returned: '{comp_id}'\n"
                            f"      Suffix:       '{suffix}'\n"
                            f"      Matched FQDN: '{suffix_matches[0]}'"
                        )
                        break
                else:
                    # No suffix match worked
                    pass
                if suffix_matches and len(suffix_matches) == 1:
                    continue

            # All strategies failed - keep original (will fail validation)
            normalized_components.append(comp_id)
            total_failed += 1

            # Enhanced failure logging
            similar_short_ids = [
                k for k in short_to_fqdn.keys()
                if component_name.lower() in k.lower()
            ][:5]

            possible_fqdns = [
                fqdn for fqdn in components.keys()
                if component_name.lower() in fqdn.lower()
            ][:5]

            logger.warning(
                f"   ❌ Failed to normalize '{comp_id}' in module '{module_name}'\n"
                f"      ├─ Original ID:      '{comp_id}'\n"
                f"      ├─ Stripped ID:      '{stripped_id}'\n"
                f"      ├─ Component name:   '{component_name}'\n"
                f"      ├─ Fuzzy matches:    {len(fuzzy_matches)}\n"
                f"      ├─ Similar short IDs: {similar_short_ids if similar_short_ids else 'None'}\n"
                f"      ├─ Possible FQDNs:   {possible_fqdns if possible_fqdns else 'None'}\n"
                f"      └─ Reason: Component not found in any normalization strategy\n"
                f"         This could indicate:\n"
                f"         • Component filtered during parsing\n"
                f"         • LLM hallucination (non-existent component)\n"
                f"         • FQDN format mismatch requiring new normalization strategy"
            )

        module_data['components'] = normalized_components

    return total_normalized, total_failed


def _find_best_path_match(llm_id: str, candidates: List[str]) -> str | None:
    """
    Find the best matching FQDN from candidates based on path similarity.

    Args:
        llm_id: Component ID returned by LLM
        candidates: List of potential FQDN matches

    Returns:
        Best matching FQDN or None if ambiguous
    """
    llm_segments = llm_id.split('.')

    # Score each candidate by number of matching path segments
    scores = []
    for candidate in candidates:
        candidate_segments = candidate.split('.')
        # Count matching segments in order
        matches = 0
        for i, llm_seg in enumerate(llm_segments):
            if llm_seg in candidate_segments:
                # Bonus points if segments are in same relative position
                try:
                    candidate_idx = candidate_segments.index(llm_seg)
                    position_diff = abs(i - candidate_idx)
                    matches += 1 + (1.0 / (1 + position_diff))  # Weight by position similarity
                except ValueError:
                    pass
        scores.append((candidate, matches))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    # Return best match if it's clearly better than alternatives
    if len(scores) > 1 and scores[0][1] > scores[1][1]:
        logger.debug(f"      Best match score: {scores[0][1]:.2f} vs next: {scores[1][1]:.2f}")
        return scores[0][0]

    return None


def build_short_id_to_fqdn_map_enhanced(components: Dict) -> Dict[str, str]:
    """
    Enhanced version of build_short_id_to_fqdn_map with partial path support.

    Maps both:
    - Short component names (e.g., "UserService")
    - Partial paths (e.g., "auth.UserService", "services.auth.UserService")

    This helps match LLM outputs that include partial directory paths.
    """
    from collections import defaultdict

    mapping = {}
    collisions = defaultdict(list)

    for fqdn, node in components.items():
        # Strategy 1: Use node's short_id if available
        short_id = node.short_id

        if not short_id:
            # Fallback: extract from FQDN
            if '::' in fqdn:
                short_id = fqdn.split('::')[-1]
            else:
                short_id = fqdn.split('.')[-1]

        # Map short_id → FQDN
        if short_id in mapping:
            collisions[short_id].append(fqdn)
        else:
            mapping[short_id] = fqdn

        # Strategy 2: Map partial paths (last 2-4 segments)
        # This helps match LLM outputs like "services.auth.UserService"
        # when the full FQDN is "main-repo.src.services.auth.UserService"
        segments = fqdn.split('.')
        if len(segments) > 2:
            # Map progressively longer suffixes
            for i in range(2, min(5, len(segments) + 1)):  # Last 2-4 segments
                partial_id = '.'.join(segments[-i:])

                # Only map if unique
                if partial_id not in mapping:
                    mapping[partial_id] = fqdn
                elif mapping[partial_id] != fqdn:
                    # Collision detected
                    if partial_id not in collisions:
                        collisions[partial_id].append(mapping[partial_id])
                    collisions[partial_id].append(fqdn)

    # Log collisions for debugging
    if collisions:
        logger.warning(f"   ⚠️  Found {len(collisions)} short ID collisions:")
        for short_id, fqdns in list(collisions.items())[:5]:
            logger.warning(f"      '{short_id}' → {fqdns[:3]}")

    logger.info(f"   ✅ Built short_id → FQDN mapping with {len(mapping)} entries")
    logger.debug(f"      ({len(collisions)} collisions detected)")

    return mapping


# Example usage in cluster_modules.py:
"""
Replace lines 200-241 with:

# Build reverse mapping: short_id → FQDN (enhanced version)
logger.info(f"🔄 Normalizing component IDs in clustering response")
short_to_fqdn = build_short_id_to_fqdn_map_enhanced(components)

# Normalize all component IDs in module_tree (enhanced version)
total_normalized, total_failed = normalize_component_ids_enhanced(
    module_tree,
    components,
    short_to_fqdn
)

if total_normalized > 0:
    logger.info(f"   ✅ Normalized {total_normalized} short IDs to FQDNs")
if total_failed > 0:
    logger.warning(f"   ⚠️  Failed to normalize {total_failed} component IDs")
logger.info("")
"""
