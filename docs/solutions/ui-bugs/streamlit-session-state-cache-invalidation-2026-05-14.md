---
title: Streamlit session state cache must invalidate when input changes
date: 2026-05-14
category: ui-bugs
module: streamlit-session-state
problem_type: ui_bug
component: frontend_stimulus
symptoms:
  - Stale validation results shown after switching from CSV upload to paste input
  - Re-uploading a different CSV file displays results from the previous file
  - Data completeness tab shows CSV column analysis while validation results correspond to pasted GTINs
root_cause: logic_error
resolution_type: code_fix
severity: medium
tags:
  - streamlit
  - session-state
  - cache-invalidation
  - stale-data
---

# Streamlit session state cache must invalidate when input changes

## Problem

When caching expensive computation results (like batch GTIN validation) in `st.session_state`, the cache persisted across input changes. Users switching between CSV upload and paste input, or re-uploading a different CSV, saw stale results from the previous validation.

## Symptoms

- Paste GTINs after validating a CSV → results show CSV validation, not paste validation
- Upload a new CSV while already in upload mode → results show the old CSV's validation
- Data completeness tab shows CSV column analysis even when validation results correspond to pasted GTINs

## What Didn't Work

- Clearing cache only on button clicks (Upload/Sample buttons) — missed the paste form submission and CSV file replacement paths
- Relying on Streamlit's `file_uploader` widget state — the widget holds the file reference but doesn't signal when a new file replaces the old one in a way that's easy to detect from the button handler

## Solution

Two-part fix:

**1. Clear cache on all input paths, not just button clicks:**

```python
# Paste form — clear cache when paste is submitted
if paste_submitted and gtin_input.strip():
    gtins_to_validate = [...]
    uploaded_df = None  # Prevent completeness mismatch
    st.session_state.pop("validation_data_cache", None)
    st.session_state.pop("uploaded_df", None)
```

**2. Compare input before using cache (catches CSV re-upload):**

```python
cached_gtins = st.session_state.get("_cached_gtins")
if "validation_data_cache" not in st.session_state or cached_gtins != gtins_to_validate:
    with st.spinner("Validating..."):
        validation_data = validate_batch(gtins_to_validate)
        st.session_state["validation_data_cache"] = validation_data
        st.session_state["_cached_gtins"] = gtins_to_validate
else:
    validation_data = st.session_state["validation_data_cache"]
```

## Why This Works

Streamlit reruns the entire script top-to-bottom on every interaction. `st.session_state` persists across reruns, making it the natural caching layer. But Streamlit has no built-in "input changed" signal — the cache key must be managed manually.

The root cause was caching the output (`validation_data`) without tracking which input produced it. The input-comparison pattern (`_cached_gtins != gtins_to_validate`) ensures the cache is always consistent with the current input, regardless of which widget or code path populated `gtins_to_validate`.

Clearing `uploaded_df` on paste submission prevents a secondary mismatch where the data completeness analysis (which uses the CSV DataFrame) would show results for a different dataset than the validation tab.

## Prevention

- When caching derived data in `st.session_state`, always store the input alongside the output and compare before reusing
- Every code path that populates input data must either clear the cache or rely on input comparison — audit all input paths, not just the obvious ones
- When multiple related session state keys represent different views of the same data (e.g., `validation_data_cache` and `uploaded_df`), clear them together to prevent cross-tab mismatches

## Related Issues

- Streamlit's execution model documentation: https://docs.streamlit.io/develop/concepts/architecture/session-state
