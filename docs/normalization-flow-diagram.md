# Short ID Normalization Flow Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Clustering Pipeline                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Components Dictionary (In Memory)                              │
├─────────────────────────────────────────────────────────────────┤
│  Key: "openframe-auth.com.openframe.config.AuthServerConfig"   │
│  Value: Node(short_id="AuthServerConfig", ...)                  │
│                                                                   │
│  Key: "main-repo.src/auth/manager.py::AuthManager"              │
│  Value: Node(short_id="AuthManager", ...)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LLM Clustering Request                                          │
├─────────────────────────────────────────────────────────────────┤
│  Prompt: "Group these components..."                            │
│  Input: Full FQDNs + code snippets                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LLM Response (Short IDs!)                                       │
├─────────────────────────────────────────────────────────────────┤
│  {                                                               │
│    "Authentication": {                                           │
│      "components": [                                             │
│        "AuthServerConfig",     ← Short ID                       │
│        "AuthManager"           ← Short ID                       │
│      ]                                                           │
│    }                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ⭐ NEW: Build Reverse Mapping                                   │
├─────────────────────────────────────────────────────────────────┤
│  build_short_id_to_fqdn_map(components)                         │
│                                                                   │
│  Result:                                                         │
│  {                                                               │
│    "AuthServerConfig" →                                          │
│      "openframe-auth.com.openframe.config.AuthServerConfig",    │
│    "AuthManager" →                                               │
│      "main-repo.src/auth/manager.py::AuthManager"               │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ⭐ NEW: Normalize Component IDs                                 │
├─────────────────────────────────────────────────────────────────┤
│  For each comp_id in LLM response:                              │
│                                                                   │
│  1. Try exact FQDN match in components                          │
│     ↓ (not found)                                               │
│                                                                   │
│  2. Try short_id → FQDN mapping                                 │
│     ✅ "AuthServerConfig" → "openframe-auth.com..."             │
│     ↓ (found!)                                                  │
│                                                                   │
│  3. Replace short ID with FQDN                                  │
│                                                                   │
│  Result:                                                         │
│  {                                                               │
│    "Authentication": {                                           │
│      "components": [                                             │
│        "openframe-auth.com.openframe.config.AuthServerConfig",  │
│        "main-repo.src/auth/manager.py::AuthManager"             │
│      ]                                                           │
│    }                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Validation & Sub-Module Clustering                             │
├─────────────────────────────────────────────────────────────────┤
│  Now all component IDs are valid FQDNs!                         │
│  ✅ Validation succeeds                                          │
│  ✅ Sub-module clustering proceeds                               │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Normalization Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│  Input: comp_id from LLM response                               │
│         Example: "AuthServerConfig"                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ comp_id in components dict?   │
              └───────────────────────────────┘
                    │                   │
                   YES                 NO
                    │                   │
                    ▼                   ▼
        ┌───────────────────┐   ┌──────────────────────┐
        │ Use comp_id       │   │ comp_id in           │
        │ (already FQDN)    │   │ short_to_fqdn map?   │
        └───────────────────┘   └──────────────────────┘
                    │                   │           │
                    │                  YES         NO
                    │                   │           │
                    │                   ▼           ▼
                    │       ┌──────────────────┐  ┌──────────────────┐
                    │       │ fqdn =           │  │ Log warning with │
                    │       │ short_to_fqdn[   │  │ available similar│
                    │       │   comp_id]       │  │ short IDs        │
                    │       └──────────────────┘  └──────────────────┘
                    │                   │                   │
                    │                   ▼                   │
                    │       ┌──────────────────┐            │
                    │       │ Use fqdn         │            │
                    │       │ (normalized)     │            │
                    │       └──────────────────┘            │
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        │
                                        ▼
                            ┌─────────────────────┐
                            │ Final normalized    │
                            │ component ID        │
                            └─────────────────────┘
```

## Collision Detection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Building short_id → FQDN Mapping                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              For each FQDN in components dict:
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │ Extract short_id                         │
        │                                          │
        │ Priority:                                │
        │   1. node.short_id (if exists)          │
        │   2. Last segment after "::"            │
        │   3. Last segment after "."             │
        └──────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ short_id already in mapping?  │
              └───────────────────────────────┘
                    │                   │
                   YES                 NO
                    │                   │
                    ▼                   ▼
        ┌───────────────────┐   ┌──────────────────┐
        │ 🔀 COLLISION!     │   │ Add to mapping:  │
        │                   │   │ short_id → FQDN  │
        │ Log warning:      │   └──────────────────┘
        │ • Both FQDNs      │
        │ • Keep first      │
        └───────────────────┘
                    │
                    ▼
        ┌───────────────────┐
        │ Track collision   │
        │ for debugging     │
        └───────────────────┘
```

## Example Walkthrough

### Input Components Dictionary

```python
components = {
    "openframe-auth.com.openframe.config.AuthorizationServerConfig": Node(
        short_id="AuthorizationServerConfig",
        ...
    ),
    "openframe-api.com.openframe.service.UserService": Node(
        short_id="UserService",
        ...
    ),
}
```

### Step 1: Build Mapping

```python
short_to_fqdn = {
    "AuthorizationServerConfig": "openframe-auth.com.openframe.config.AuthorizationServerConfig",
    "UserService": "openframe-api.com.openframe.service.UserService"
}
```

### Step 2: LLM Returns Short IDs

```python
module_tree = {
    "Authentication": {
        "components": ["AuthorizationServerConfig", "UserService"]
    }
}
```

### Step 3: Normalize

```python
for comp_id in ["AuthorizationServerConfig", "UserService"]:
    # comp_id not in components (not exact FQDN)
    # comp_id in short_to_fqdn (found in mapping!)

    fqdn = short_to_fqdn[comp_id]
    # "openframe-auth.com.openframe.config.AuthorizationServerConfig"

    normalized_components.append(fqdn)
```

### Step 4: Result

```python
module_tree = {
    "Authentication": {
        "components": [
            "openframe-auth.com.openframe.config.AuthorizationServerConfig",
            "openframe-api.com.openframe.service.UserService"
        ]
    }
}
```

### Step 5: Validation Succeeds ✅

All component IDs are now valid FQDNs and found in `components` dictionary.

## Logging Output Example

```
🗂️  Module Clustering Operation
   ├─ Current module: (repository level)
   ├─ Leaf nodes to cluster: 150
   └─ Components dictionary size: 150 components

🤖 Calling clustering LLM
   └─ Prompt assembled via format_cluster_prompt()

   ✅ Clustering LLM response received
   ├─ Response length: 2453 chars
   └─ Preview: <GROUPED_COMPONENTS>...

🔄 Normalizing component IDs in clustering response
📋 Built short_id → FQDN mapping: 150 entries

   ✅ Normalized 'AuthorizationServerConfig' → 'openframe-auth.com.openframe.config.AuthorizationServerConfig'
   ✅ Normalized 'UserService' → 'openframe-api.com.openframe.service.UserService'
   ✅ Normalized 'AuthManager' → 'main-repo.src/auth/manager.py::AuthManager'

   ✅ Normalized 15 short IDs to FQDNs

📊 Sub-module 'Authentication': 15 valid nodes, 0 skipped
```

## Error Scenario

```
   ❌ Failed to normalize 'NonExistentClass' in module 'Core Services'
      ├─ Not found as exact FQDN in components
      ├─ Not found in short_id → FQDN mapping
      └─ Available similar short IDs: ['NonExistentService', 'ExistentClass']

   ⚠️  Failed to normalize 1 component IDs
```

## Performance Characteristics

| Operation | Complexity | Typical Time |
|-----------|------------|--------------|
| Build mapping | O(n) | < 10ms for 1000 components |
| Normalize IDs | O(m) | < 5ms for 100 IDs |
| Memory overhead | O(n) | ~100KB for 1000 components |

**Total Impact:** Negligible (< 0.1% of LLM call time)

## Summary

1. **Before Normalization:** LLM returns short IDs → validation fails
2. **Build Mapping:** Extract short IDs from all components
3. **Normalize:** Convert short IDs to FQDNs
4. **After Normalization:** All IDs are valid FQDNs → validation succeeds

**Result:** Robust clustering pipeline that accepts LLM behavior as-is
