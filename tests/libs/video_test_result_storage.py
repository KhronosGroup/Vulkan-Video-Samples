"""
Video Test Result Storage
Handles saving test results by hardware and comparing against previous runs
to detect regressions and improvements.

Copyright 2026 Igalia S.L.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from tests.libs.video_test_config_base import TestResult, VideoTestStatus
from tests.libs.video_test_driver_detect import SystemInfo

RESULTS_FILENAME = "vvs_test_results.json"

_REGRESSION_MARK = "\u274C"
_IMPROVEMENT_MARK = "\U0001F389"
_NO_REGRESSION_MARK = "\u2714\uFE0F"
_STATE_CHANGED_MARK = "\U0001F504"

# Severity ordering: lower is worse. Transitions to a lower severity
# are regressions, transitions to a higher severity are improvements.
_SEVERITY = {
    VideoTestStatus.CRASH.value: 0,
    VideoTestStatus.ERROR.value: 1,
    VideoTestStatus.NOT_SUPPORTED.value: 2,
    VideoTestStatus.SKIPPED.value: 2,
    VideoTestStatus.SUCCESS.value: 3,
}

_STATE_CHANGED_PAIRS = frozenset({
    (VideoTestStatus.NOT_SUPPORTED.value, VideoTestStatus.SKIPPED.value),
    (VideoTestStatus.SKIPPED.value, VideoTestStatus.NOT_SUPPORTED.value),
})


def sanitize_hardware_key(gpu_name: str, vendor_id: str = "",
                          device_id: str = "") -> str:
    """Convert GPU name, vendor ID, and device ID to a safe JSON key.

    Combines all identifiers to distinguish the same GPU across
    different platforms (e.g. Linux vs Windows).
    """
    parts = [gpu_name]
    if vendor_id:
        parts.append(vendor_id)
    if device_id:
        parts.append(device_id)
    raw = "_".join(parts)
    key = re.sub(r'[^a-zA-Z0-9]+', '_', raw)
    return key.strip('_')


def _build_current_results(results: List[TestResult]) -> Dict[str, str]:
    """Build a flat name -> status map from TestResult objects."""
    current = {}
    for result in results:
        name = (result.config.display_name
                if hasattr(result.config, 'display_name')
                else result.config.name)
        current[name] = result.status.value
    return current


def _classify_results(
    previous: Dict[str, str],
    current: Dict[str, str],
) -> dict:
    """Classify test results into regressions, improvements, state changes,
    new, and removed tests.

    Uses a severity ordering (success > not_supported > error > crash)
    to determine regressions (downward) and improvements (upward).
    Transitions between not_supported and skipped are neutral state changes.
    """
    regressions = []
    improvements = []
    state_changes = []
    new_tests = []
    unchanged = 0

    for name, cur_status in sorted(current.items()):
        prev_status = previous.get(name)
        if prev_status is None:
            new_tests.append(name)
        elif prev_status == cur_status:
            unchanged += 1
        elif (prev_status, cur_status) in _STATE_CHANGED_PAIRS:
            state_changes.append((name, prev_status, cur_status))
        elif _SEVERITY.get(cur_status, -1) < _SEVERITY.get(prev_status, -1):
            regressions.append((name, prev_status, cur_status))
        elif _SEVERITY.get(cur_status, -1) > _SEVERITY.get(prev_status, -1):
            improvements.append((name, prev_status, cur_status))

    removed = [n for n in sorted(previous) if n not in current]

    return {
        "regressions": regressions,
        "improvements": improvements,
        "state_changes": state_changes,
        "new_tests": new_tests,
        "removed_tests": removed,
        "unchanged": unchanged,
    }


def _print_comparison(diff: dict, hardware_key: str,
                      previous_timestamp: str) -> None:
    """Print the comparison report."""
    print(f"\n=== Results Comparison ({hardware_key}) ===")
    print(f"Previous run: {previous_timestamp}")

    sections = [
        (f"{_REGRESSION_MARK} Regressions",
         diff["regressions"], True),
        (f"{_IMPROVEMENT_MARK} Improvements",
         diff["improvements"], True),
        (f"{_STATE_CHANGED_MARK} State changes",
         diff["state_changes"], True),
        ("New tests", diff["new_tests"], False),
        ("Removed tests", diff["removed_tests"], False),
    ]
    for header, items, has_transition in sections:
        if not items:
            continue
        print(f"\n{header}:")
        for item in items:
            if has_transition:
                name, prev, cur = item
                print(f"  {name}: {prev} -> {cur}")
            else:
                print(f"  {item}")

    parts = [f"{diff['unchanged']} unchanged"]
    for label, key in [("improvement(s)", "improvements"),
                       ("regression(s)", "regressions"),
                       ("state change(s)", "state_changes"),
                       ("new", "new_tests"),
                       ("removed", "removed_tests")]:
        if diff[key]:
            parts.append(f"{len(diff[key])} {label}")
    if diff["regressions"]:
        prefix = _REGRESSION_MARK
    else:
        prefix = _NO_REGRESSION_MARK
    print(f"\n{prefix} Summary: {', '.join(parts)}")


def compare_and_print(
    previous: Dict[str, str],
    current: Dict[str, str],
    hardware_key: str,
    previous_timestamp: str,
) -> bool:
    """Compare previous and current results, print diff.

    Returns False if regressions are found, True otherwise.
    """
    diff = _classify_results(previous, current)
    _print_comparison(diff, hardware_key, previous_timestamp)
    return len(diff["regressions"]) == 0


def save_results(
    filepath: Path,
    hardware_key: str,
    system_info: SystemInfo,
    results: List[TestResult],
) -> None:
    """Save current results to the JSON file under the hardware key.

    Loads any existing data, updates the entry for hardware_key, and
    writes back. Returns True on success.
    """
    data = {}
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

    current_map = _build_current_results(results)

    data[hardware_key] = {
        "system_info": {
            "gpu_name": system_info.gpu_name,
            "vendor_id": system_info.vendor_id,
            "device_id": system_info.device_id,
            "driver_name": system_info.driver_name,
            "driver_version": system_info.driver_version,
            "os_name": system_info.os_name,
        },
        "last_run": datetime.now().isoformat(timespec='seconds'),
        "results": current_map,
    }

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"Results saved to {filepath} (key: {hardware_key})")


def handle_compare_results(
    system_info: SystemInfo,
    results: List[TestResult],
    results_file: Path,
    save_to_file: bool,
) -> bool:
    """High-level entry point: compare against previous run, then save.

    Returns False if regressions are detected, True otherwise.
    """
    if not system_info.gpu_name:
        print("Cannot save results: GPU name not detected")
        return True

    hardware_key = sanitize_hardware_key(system_info.gpu_name,
                                         system_info.vendor_id,
                                         system_info.device_id)

    no_regression = True
    if results_file.exists():
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        previous_entry = data.get(hardware_key)
        if previous_entry:
            current_map = _build_current_results(results)
            no_regression = compare_and_print(
                previous_entry["results"],
                current_map,
                hardware_key,
                previous_entry.get("last_run", "unknown"),
            )
    if save_to_file:
        save_results(results_file, hardware_key, system_info, results)
    return no_regression
