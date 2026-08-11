"""
Video Test Result Reporter
Handles formatting and printing of test results and summaries.

Copyright 2025 Igalia S.L.

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

from typing import List
from tests.libs.video_test_config_base import TestResult, VideoTestStatus


def get_status_display(status: VideoTestStatus) -> tuple:
    """Get status display string and symbol

    Args:
        status: VideoTestStatus enum value

    Returns:
        Tuple of (status_text, status_symbol)
    """
    if status == VideoTestStatus.SUCCESS:
        return "PASS", "✔️"
    if status == VideoTestStatus.NOT_SUPPORTED:
        return "N/S", "○"
    if status == VideoTestStatus.CRASH:
        return "CRASH", "💥"
    if status == VideoTestStatus.SKIPPED:
        return "SKIP", "⊘"
    return "FAIL", "❌"


def get_status_symbol_from_str(status) -> str:
    """Return the symbol for a status, accepting either a status string
    (e.g. "success") or a VideoTestStatus enum value.
    """
    if isinstance(status, VideoTestStatus):
        status = status.value
    symbols = {
        VideoTestStatus.SUCCESS.value: "✔️",
        VideoTestStatus.NOT_SUPPORTED.value: "○",
        VideoTestStatus.CRASH.value: "💥",
        VideoTestStatus.SKIPPED.value: "⊘",
        VideoTestStatus.ERROR.value: "❌",
    }
    return symbols.get(status, status)


def print_codec_breakdown(codec_results: dict) -> None:
    """Print codec breakdown results

    Args:
        codec_results: Dictionary mapping codec names to count dictionaries
    """
    for codec, counts in codec_results.items():
        skipped = counts.get('skipped', 0)
        skipped_str = f", {skipped:2} skip" if skipped > 0 else ""
        print(
            f"{codec.upper():8} - {counts['pass']:2} pass, "
            f"{counts['not_supported']:2} N/S, "
            f"{counts['crash']:2} crash, "
            f"{counts['fail']:2} fail{skipped_str} ({counts['total']:2} total)"
        )


def print_detailed_results(results: List[TestResult]) -> None:
    """Print detailed test results

    Args:
        results: List of TestResult objects
    """
    for result in results:
        config = result.config
        status, status_symbol = get_status_display(result.status)

        test_name = (config.display_name
                     if hasattr(config, 'display_name')
                     else config.name)
        print(
            f"{status_symbol} {config.codec.value:4} {test_name:35} - "
            f"{status:5} ({result.execution_time:.2f}s)"
        )


def print_final_summary(counts: tuple, test_type: str = "") -> bool:
    """Print final summary and return success status

    Args:
        counts: Tuple of (passed, not_supported, crashed, failed)
        test_type: Type of test (e.g., "decoder", "encoder"). When empty,
                   the type label is omitted from the messages.

    Returns:
        True if all tests passed (or only not supported), False otherwise
    """
    passed, not_supported, crashed, failed = counts
    total_errors = failed + crashed
    label = f"{test_type.upper()} " if test_type else ""

    if total_errors == 0:
        if not_supported > 0:
            print(
                f"\n✔️ ALL TESTS COMPLETED - {passed} passed, "
                f"{not_supported} not supported by hardware/driver"
            )
        else:
            print(f"\n🎉 ALL {label}TESTS PASSED!")
        return True

    if crashed > 0 and failed > 0:
        print(
            f"\n💥 {crashed} {label}TEST(S) CRASHED, "
            f"{failed} FAILED!"
        )
    elif crashed > 0:
        print(f"\n💥 {crashed} {label}TEST(S) CRASHED!")
    else:
        print(f"\n❌ {failed} {label}TEST(S) FAILED!")
    return False


def print_command_output(result: TestResult, max_lines: int = 0) -> None:
    """Print stdout/stderr to aid debugging.

    Args:
        result: TestResult object
        max_lines: Maximum lines to show (0 = unlimited)
    """
    print("   === Command Output ===")
    if result.stdout:
        print("   STDOUT:")
        lines = result.stdout.splitlines()
        if 0 < max_lines < len(lines):
            for line in lines[:max_lines]:
                print(f"     {line}")
            print(f"     ... ({len(lines) - max_lines} more lines)")
        else:
            for line in lines:
                print(f"     {line}")
    if result.stderr:
        print("   STDERR:")
        lines = result.stderr.splitlines()
        if 0 < max_lines < len(lines):
            for line in lines[:max_lines]:
                print(f"     {line}")
            print(f"     ... ({len(lines) - max_lines} more lines)")
        else:
            for line in lines:
                print(f"     {line}")


def count_results_by_status(results: List[TestResult]) -> tuple:
    """Count results by status type"""
    passed = sum(1 for r in results if r.status == VideoTestStatus.SUCCESS)
    not_supported = sum(
        1 for r in results if r.status == VideoTestStatus.NOT_SUPPORTED
    )
    crashed = sum(1 for r in results if r.status == VideoTestStatus.CRASH)
    failed = sum(1 for r in results if r.status == VideoTestStatus.ERROR)
    skipped = sum(
        1 for r in results if r.status == VideoTestStatus.SKIPPED
    )
    return passed, not_supported, crashed, failed, skipped


def group_results_by_codec(results: List[TestResult]) -> dict:
    """Group results by codec with counts"""
    codec_results = {}
    for result in results:
        codec = result.config.codec.value
        if codec not in codec_results:
            codec_results[codec] = {
                "pass": 0, "not_supported": 0, "crash": 0, "fail": 0,
                "skipped": 0, "total": 0
            }

        codec_results[codec]["total"] += 1
        if result.status == VideoTestStatus.SUCCESS:
            codec_results[codec]["pass"] += 1
        elif result.status == VideoTestStatus.NOT_SUPPORTED:
            codec_results[codec]["not_supported"] += 1
        elif result.status == VideoTestStatus.CRASH:
            codec_results[codec]["crash"] += 1
        elif result.status == VideoTestStatus.SKIPPED:
            codec_results[codec]["skipped"] += 1
        else:
            codec_results[codec]["fail"] += 1
    return codec_results


def result_to_dict(result: TestResult, test_type: str) -> dict:
    """Convert a TestResult to a dictionary for JSON export."""
    test_name = (result.config.display_name
                 if hasattr(result.config, 'display_name')
                 else result.config.name)
    result_dict = {
        "name": test_name,
        "codec": result.config.codec.value,
        "test_type": test_type,
        "description": result.config.description,
        "status": result.status.value,
        "success": result.success,
        "returncode": result.returncode,
        "execution_time_ms": round(
            result.execution_time * 1000, 2
        ),
        "warning_found": result.warning_found,
        "warning_message": result.warning_message,
        "error_message": result.error_message,
        "command_line": result.command_line
    }

    if hasattr(result.config, 'full_path'):
        result_dict["input_file"] = str(result.config.full_path)
    elif hasattr(result.config, 'full_yuv_path'):
        result_dict["input_file"] = str(result.config.full_yuv_path)

    if hasattr(result.config, 'profile') and result.config.profile:
        result_dict["profile"] = result.config.profile

    return result_dict
