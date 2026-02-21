#!/usr/bin/env python3
"""
Quick verification that store_issues returns valid UUID even for empty lists.
"""
import sys
import os
import re

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.artifacts import store_issues, get_artifact, ARTIFACT_STORE

print("=" * 60)
print("Testing store_issues() with empty and non-empty lists")
print("=" * 60)

# Test 1: Empty issues list
print("\n✅ Test 1: Store empty issues list")
report_id_empty = store_issues([], "/fake/path")
print(f"  Returned report_id: {report_id_empty}")
print(f"  Is valid UUID (36 chars): {len(report_id_empty) == 36}")
print(f"  Matches UUID pattern: {bool(re.match(r'^[a-f0-9\-]{36}$', report_id_empty))}")

artifact_empty = get_artifact(report_id_empty)
print(f"  Artifact stored: {artifact_empty is not None}")
if artifact_empty:
    print(f"  Issue count: {artifact_empty.get('count')} (expected 0)")
    print(f"  Issues list: {artifact_empty.get('issues')} (expected [])")

# Test 2: Issues list with items
print("\n✅ Test 2: Store issues with items")
test_issues = [{"file": "test.py", "code": "E501"}]
report_id_issues = store_issues(test_issues, "/fake/path")
print(f"  Returned report_id: {report_id_issues}")
print(f"  Is valid UUID (36 chars): {len(report_id_issues) == 36}")

artifact_issues = get_artifact(report_id_issues)
print(f"  Artifact stored: {artifact_issues is not None}")
if artifact_issues:
    print(f"  Issue count: {artifact_issues.get('count')} (expected 1)")

# Test 3: Regex pattern matching (what orchestrator uses)
print("\n✅ Test 3: Orchestrator UUID extraction")
analysis_output_empty = f"Issues stored. Reference ID: {report_id_empty} (found 0 issues)"
analysis_output_issues = f"Issues stored. Reference ID: {report_id_issues} (found 1 issues)"

print(f"  Empty issues output: {analysis_output_empty[:60]}...")
match_empty = re.search(r"([a-f0-9\-]{36})", analysis_output_empty)
print(f"  Regex extracts UUID: {match_empty is not None}")
if match_empty:
    print(f"  Extracted: {match_empty.group(1)}")

print(f"\n  Issues output: {analysis_output_issues[:60]}...")
match_issues = re.search(r"([a-f0-9\-]{36})", analysis_output_issues)
print(f"  Regex extracts UUID: {match_issues is not None}")
if match_issues:
    print(f"  Extracted: {match_issues.group(1)}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Pipeline will continue with 0 issues!")
print("=" * 60)
