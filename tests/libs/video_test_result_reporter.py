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
from tests.libs.video_test_config_base import TestResult, TestStatus


def get_status_display(status: TestStatus) -> tuple:
    """Get status display string and symbol

    Args:
        status: TestStatus enum value

    Returns:
        Tuple of (status_text, status_symbol)
    """
    if status == TestStatus.SUCCESS:
        return "PASS", "✓"
    if status == TestStatus.NOT_SUPPORTED:
        return "N/S", "○"
    if status == TestStatus.CRASH:
        return "CRASH", "💥"
    return "FAIL", "✗"


def print_codec_breakdown(codec_results: dict) -> None:
    """Print codec breakdown results

    Args:
        codec_results: Dictionary mapping codec names to count dictionaries
    """
    for codec, counts in codec_results.items():
        print(
            f"{codec.upper():8} - {counts['pass']:2} pass, "
            f"{counts['not_supported']:2} N/S, "
            f"{counts['crash']:2} crash, "
            f"{counts['fail']:2} fail ({counts['total']:2} total)"
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


def print_final_summary(counts: tuple, test_type: str) -> bool:
    """Print final summary and return success status

    Args:
        counts: Tuple of (passed, not_supported, crashed, failed)
        test_type: Type of test (e.g., "decoder", "encoder")

    Returns:
        True if all tests passed (or only not supported), False otherwise
    """
    passed, not_supported, crashed, failed = counts
    total_errors = failed + crashed
    test_type_upper = test_type.upper()

    if total_errors == 0:
        if not_supported > 0:
            print(
                f"\n✓ ALL TESTS COMPLETED - {passed} passed, "
                f"{not_supported} not supported by hardware/driver"
            )
        else:
            print(f"\n🎉 ALL {test_type_upper} TESTS PASSED!")
        return True

    if crashed > 0 and failed > 0:
        print(
            f"\n💥 {crashed} {test_type_upper} TEST(S) CRASHED, "
            f"{failed} FAILED!"
        )
    elif crashed > 0:
        print(f"\n💥 {crashed} {test_type_upper} TEST(S) CRASHED!")
    else:
        print(f"\n✗ {failed} {test_type_upper} TEST(S) FAILED!")
    return False


def print_command_output(result: TestResult, preview_lines: int = 20) -> None:
    """Print limited stdout/stderr to aid debugging when verbose is on.

    Args:
        result: TestResult object
        preview_lines: Number of lines to preview from output
    """
    print("   === Command Output ===")
    if result.stdout:
        print("   STDOUT:")
        for line in result.stdout.splitlines()[:preview_lines]:
            print(f"     {line}")
    if result.stderr:
        print("   STDERR:")
        for line in result.stderr.splitlines()[:preview_lines]:
            print(f"     {line}")


def list_test_samples(samples_data: list, test_type: str = "test") -> None:
    """List all available test samples with codec statistics

    Args:
        samples_data: List of sample dictionaries
        test_type: Type of test (e.g., "decoder", "encoder")
    """
    print("=" * 70)
    print(f"AVAILABLE {test_type.upper()} TEST SAMPLES")
    print("=" * 70)

    if samples_data:
        print(f"\n{'Name':<40} {'Codec':<8} {'Enabled':<8} Description")
        print("-" * 70)
        for sample in samples_data:
            if test_type == "decoder":
                prefix = "decode_"
            elif test_type == "encoder":
                prefix = "encode_"
            else:
                prefix = ""
            name = f"{prefix}{sample['name']}" if prefix else sample['name']
            codec = sample.get('codec', 'unknown')
            enabled = "✓" if sample.get('enabled', True) else "✗"
            description = sample.get('description', '')
            print(f"{name:<40} {codec:<8} {enabled:<8} {description}")

        # Count by codec
        codec_counts = {}
        for sample in samples_data:
            if sample.get('enabled', True):
                codec = sample.get('codec', 'unknown')
                codec_counts[codec] = codec_counts.get(codec, 0) + 1

        print("-" * 70)
        print(f"\nTotal: {len(samples_data)} samples")
        if codec_counts:
            codec_summary = ", ".join(
                f"{codec}: {count}"
                for codec, count in sorted(codec_counts.items())
            )
            print(f"Enabled by codec: {codec_summary}")
    else:
        print(f"No {test_type} samples found")

    prefix = (
        "decode_" if test_type == "decoder" else
        "encode_" if test_type == "encoder" else ""
    )
    print(
        "\nUse --test '<pattern>' to filter samples (e.g., --test '"
        f"{prefix}*')"
    )
    print("Use --codec <codec> to run only specific codec tests")
