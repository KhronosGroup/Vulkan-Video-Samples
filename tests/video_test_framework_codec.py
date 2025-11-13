#!/usr/bin/env python3
"""
Vulkan Video Samples Test Framework
Main orchestrator that invokes separate encoder and decoder test frameworks.

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

# pylint: disable=wrong-import-position, protected-access
import sys

import pathlib
if __package__ is None or __package__ == "":
    # Add repository root so 'tests' becomes importable
    sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

import json
from pathlib import Path
from typing import List, Tuple, Optional
from enum import Enum
import argparse
from dataclasses import dataclass

# Import the specialized test frameworks and base classes
from tests.libs.video_test_config_base import (
    TestResult,
    TestStatus,
    load_samples_from_json,
    download_sample_assets,
)

from tests.libs.video_test_platform_utils import (
    PlatformUtils,
)

from tests.libs.video_test_utils import safe_main_wrapper
from tests.video_test_framework_encode import VulkanVideoEncodeTestFramework
from tests.video_test_framework_decode import VulkanVideoDecodeTestFramework


@dataclass
class FrameworkConfig:
    """Configuration settings for the test framework"""
    encoder_path: Optional[str] = None
    decoder_path: Optional[str] = None
    work_dir: Optional[str] = None
    device_id: Optional[str] = None
    verbose: bool = False
    keep_files: bool = False
    no_auto_download: bool = False


class TestType(Enum):
    """Enumeration of test types for video codec testing"""
    ENCODER = "encoder"
    DECODER = "decoder"


class VulkanVideoTestFramework:  # pylint: disable=too-many-instance-attributes
    """Main test framework orchestrator for Vulkan Video codecs"""

    def __init__(self, encoder_path: Optional[str] = None,
                 decoder_path: Optional[str] = None, **options):
        # Create configuration object
        self.config = FrameworkConfig(
            encoder_path=encoder_path,
            decoder_path=decoder_path,
            work_dir=options.get('work_dir'),
            device_id=options.get('device_id'),
            verbose=options.get('verbose', False),
            keep_files=options.get('keep_files', False),
            no_auto_download=options.get('no_auto_download', False)
        )
        self.include_disabled = options.get('include_disabled', False)
        self.only_disabled = options.get('only_disabled', False)

        # Setup directories
        self.test_dir = Path(__file__).parent
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)

        # Initialize specialized test frameworks
        self.encode_framework = None
        self.decode_framework = None

        if encoder_path and Path(encoder_path).exists():
            # Create options with work_dir and device_id
            encoder_options = options.copy()
            encoder_options['work_dir'] = self.config.work_dir
            encoder_options['device_id'] = self.config.device_id
            if 'encode_test_suite' in options:
                encoder_options['test_suite'] = options['encode_test_suite']
            # Pass decoder path for validation if available
            if decoder_path and Path(decoder_path).exists():
                encoder_options['decoder'] = decoder_path
            else:
                encoder_options['validate_with_decoder'] = False

            self.encode_framework = VulkanVideoEncodeTestFramework(
                encoder_path=encoder_path,
                **encoder_options
            )

        if decoder_path and Path(decoder_path).exists():
            # Create options with work_dir and device_id
            decoder_options = options.copy()
            decoder_options['work_dir'] = self.config.work_dir
            decoder_options['device_id'] = self.config.device_id
            if 'decode_test_suite' in options:
                decoder_options['test_suite'] = options['decode_test_suite']

            self.decode_framework = VulkanVideoDecodeTestFramework(
                decoder_path=decoder_path,
                **decoder_options
            )

        # Combined results tracking
        self.all_results: List[TestResult] = []

    def check_resources(self, auto_download: bool = True) -> bool:
        """Check if required resource files are available and have correct
        checksums"""
        encode_ok = True
        decode_ok = True

        # Override auto_download based on the framework's no_auto_download
        # setting
        effective_auto_download = (
            auto_download and not self.config.no_auto_download
        )

        if self.encode_framework:
            encode_ok = self.encode_framework.check_resources(
                effective_auto_download
            )

        if self.decode_framework:
            decode_ok = self.decode_framework.check_resources(
                effective_auto_download
            )

        return encode_ok and decode_ok

    def cleanup_results(self):
        """Clean up output artifacts if keep_files is False"""
        if self.encode_framework:
            self.encode_framework.cleanup_results("encode")

        if self.decode_framework:
            self.decode_framework.cleanup_results("decode")

    def download_assets(self) -> bool:
        """Download test assets using the fetch scripts"""
        encode_ok = True
        decode_ok = True

        if self.encode_framework:
            encode_ok = download_sample_assets(
                self.encode_framework.encode_samples, "encode test"
            )

        if self.decode_framework:
            decode_ok = download_sample_assets(
                self.decode_framework.decode_samples, "decode test"
            )

        return encode_ok and decode_ok

    def create_test_suite(self,
                          test_type_filter: Optional[TestType] = None
                          ) -> Tuple[List, List]:
        """Create test suites for encoder and decoder"""
        encode_tests = []
        decode_tests = []

        if (self.encode_framework and (test_type_filter is None or
                                       test_type_filter == TestType.ENCODER)):
            encode_tests = self.encode_framework.create_test_suite()

        if (self.decode_framework and (test_type_filter is None or
                                       test_type_filter == TestType.DECODER)):
            decode_tests = self.decode_framework.create_test_suite()

        return encode_tests, decode_tests

    def run_test_suite(self, codec_filter: Optional[str] = None,
                       test_type_filter: Optional[TestType] = None,
                       test_pattern: Optional[str] = None
                       ) -> Tuple[List, List]:
        """Run complete test suite"""
        # Check if at least one framework is available
        if not self.encode_framework and not self.decode_framework:
            print("✗ FATAL: No encoder or decoder executables found!")
            print(f"  Encoder path: {self.config.encoder_path}")
            print(f"  Decoder path: {self.config.decoder_path}")
            print("\nPlease ensure executables are built and accessible.")
            print(
                "You can specify paths with --encoder and --decoder options."
            )
            return [], []

        print("=== Vulkan Video Samples Test Framework ===")
        print(f"Encoder: {self.config.encoder_path}")
        print(f"Decoder: {self.config.decoder_path}")
        if self.config.work_dir:
            print(f"Work Dir: {self.config.work_dir}")
        print()

        # Check resource files (automatically downloads missing/corrupt files)
        if not self.check_resources(auto_download=True):
            print("✗ FATAL: Missing or corrupt resource files could not "
                  "be downloaded")
            return [], []

        encode_results = []
        decode_results = []

        # Run encoder tests
        if (self.encode_framework and
                (test_type_filter is None or
                 test_type_filter == TestType.ENCODER)):
            print("\n" + "=" * 50)
            print("RUNNING ENCODER TESTS")
            print("=" * 50)

            encode_test_configs = self.encode_framework.create_test_suite(
                codec_filter=codec_filter, test_pattern=test_pattern
            )

            encode_results = self.encode_framework.run_test_suite(
                encode_test_configs)
            self.all_results.extend(encode_results)

        # Run decoder tests
        if (self.decode_framework and
                (test_type_filter is None or
                 test_type_filter == TestType.DECODER)):
            print("\n" + "=" * 50)
            print("RUNNING DECODER TESTS")
            print("=" * 50)

            decode_test_configs = self.decode_framework.create_test_suite(
                codec_filter=codec_filter,
                test_pattern=test_pattern
            )

            decode_results = self.decode_framework.run_test_suite(
                decode_test_configs)
            self.all_results.extend(decode_results)

        return encode_results, decode_results

    def _count_disabled_tests(self) -> int:
        """Count disabled tests from both frameworks"""
        # When running with --include-disabled or --only-disabled,
        # we still want to show how many tests are disabled in total
        if self.only_disabled:
            # When showing only disabled, count enabled as "skipped"
            return self._count_enabled_tests()

        # When including both or only enabled, count disabled tests
        total_disabled = 0
        if self.encode_framework and self.encode_framework.encode_samples:
            total_disabled += sum(
                1 for s in self.encode_framework.encode_samples
                if hasattr(s, 'enabled') and not s.enabled
            )
        if self.decode_framework and self.decode_framework.decode_samples:
            total_disabled += sum(
                1 for s in self.decode_framework.decode_samples
                if hasattr(s, 'enabled') and not s.enabled
            )
        return total_disabled

    def _count_enabled_tests(self) -> int:
        """Count enabled tests from both frameworks"""
        total_enabled = 0
        if self.encode_framework and self.encode_framework.encode_samples:
            total_enabled += sum(
                1 for s in self.encode_framework.encode_samples
                if hasattr(s, 'enabled') and s.enabled
            )
        if self.decode_framework and self.decode_framework.decode_samples:
            total_enabled += sum(
                1 for s in self.decode_framework.decode_samples
                if hasattr(s, 'enabled') and s.enabled
            )
        return total_enabled

    def _print_final_status(self, overall_success: bool,
                            test_counts: dict) -> None:
        """Print final status message

        Args:
            overall_success: Whether all tests passed
            test_counts: Dict with keys 'passed', 'not_supported',
                        'crashed', 'failed'
        """
        passed = test_counts['passed']
        not_supported = test_counts['not_supported']
        crashed = test_counts['crashed']
        failed = test_counts['failed']

        if overall_success:
            if not_supported > 0:
                print(f"\n✓ ALL TESTS COMPLETED - {passed} passed, "
                      f"{not_supported} not supported by "
                      f"hardware/driver")
            else:
                print("\n🎉 ALL TESTS PASSED!")
        elif crashed > 0 and failed > 0:
            print(f"\n💥 {crashed} TEST(S) CRASHED, "
                  f"{failed} FAILED!")
        elif crashed > 0:
            print(f"\n💥 {crashed} TEST(S) CRASHED!")
        else:
            print(f"\n✗ {failed} TEST(S) FAILED!")

    def print_summary(self, encode_results: Optional[List] = None,
                      decode_results: Optional[List] = None) -> bool:
        """Print comprehensive test results summary"""
        print("\n" + "=" * 70)
        print("VULKAN VIDEO CODEC TEST RESULTS SUMMARY")
        print("=" * 70)

        encode_success = True
        decode_success = True

        if encode_results and self.encode_framework:
            print("\nENCODER RESULTS:")
            encode_success = self.encode_framework.print_summary(
                encode_results)

        if decode_results and self.decode_framework:
            print("\nDECODER RESULTS:")
            decode_success = self.decode_framework.print_summary(
                decode_results)

        # Combined summary
        total_tests = len(self.all_results)
        total_passed = sum(1 for r in self.all_results
                           if r.status == TestStatus.SUCCESS)
        total_not_supported = sum(
            1 for r in self.all_results
            if r.status == TestStatus.NOT_SUPPORTED
        )
        total_crashed = sum(1 for r in self.all_results
                            if r.status == TestStatus.CRASH)
        total_failed = sum(1 for r in self.all_results
                           if r.status == TestStatus.ERROR)

        # Count disabled tests
        total_disabled = self._count_disabled_tests()
        total_including_disabled = total_tests + total_disabled

        print("\n" + "=" * 70)
        print("OVERALL SUMMARY")
        print("=" * 70)
        print(f"Total Tests:   {total_including_disabled:3}")
        if self.only_disabled:
            # When running only disabled tests, show how many enabled were
            # skipped
            if total_disabled > 0:
                print(f"Skipped (enabled): {total_disabled:3} "
                      "(remove --only-disabled to run)")
        elif not self.include_disabled and total_disabled > 0:
            # Only show disabled count when not using --include-disabled
            print(f"Disabled:      {total_disabled:3} "
                  "(use --include-disabled to run)")
        print(f"Passed:        {total_passed:3}")
        print(f"Not Supported: {total_not_supported:3}")
        print(f"Crashed:       {total_crashed:3}")
        print(f"Failed:        {total_failed:3}")
        if total_tests > 0:
            success_rate = total_passed/total_tests*100
            print(f"Success Rate: {success_rate:.1f}%")

        overall_success = encode_success and decode_success
        self._print_final_status(
            overall_success,
            {
                'passed': total_passed,
                'not_supported': total_not_supported,
                'crashed': total_crashed,
                'failed': total_failed
            }
        )

        return overall_success

    def export_results_json(self, output_file: str) -> bool:
        """Export test results to JSON file"""
        try:
            combined_results = []

            # Combine results from both frameworks using base class helper
            if self.encode_framework:
                for result in self.encode_framework.results:
                    result_dict = self.encode_framework._result_to_dict(
                        result,
                        "encoder",
                    )
                    combined_results.append(result_dict)

            if self.decode_framework:
                for result in self.decode_framework.results:
                    result_dict = self.decode_framework._result_to_dict(
                        result,
                        "decoder",
                    )
                    combined_results.append(result_dict)

            # Ensure directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "summary": {
                        "total_tests": len(combined_results),
                        "passed": sum(1 for r in combined_results
                                      if r["success"]),
                        "not_supported": sum(
                            1 for r in combined_results
                            if r["status"] == "not_supported"
                        ),
                        "crashed": sum(
                            1 for r in combined_results
                            if r["status"] == "crash"
                        ),
                        "failed": sum(
                            1 for r in combined_results
                            if r["status"] == "error"
                        )
                    },
                    "results": combined_results
                }, f, indent=2)

            print(f"✓ Results exported to {output_file}")
            return True

        except (OSError, IOError) as e:
            print(f"✗ Failed to export results: {e}")
            return False


def list_all_samples() -> None:
    """List all available test samples from both encoder and decoder"""
    print("=" * 70)
    print("AVAILABLE TEST SAMPLES")
    print("=" * 70)

    # Load and display decoder samples
    print("\n📹 DECODER SAMPLES:")
    print("-" * 70)
    decoder_samples = load_samples_from_json("decode_samples.json")
    if decoder_samples:
        print(f"{'Name':<40} {'Codec':<8} {'Enabled':<8} Description")
        print("-" * 70)
        for sample in decoder_samples:
            name = f"decode_{sample['name']}"
            codec = sample.get('codec', 'unknown')
            enabled = "✓" if sample.get('enabled', True) else "✗"
            description = sample.get('description', '')
            print(f"{name:<40} {codec:<8} {enabled:<8} {description}")
    else:
        print("No decoder samples found")

    # Load and display encoder samples
    print("\n✏️  ENCODER SAMPLES:")
    print("-" * 70)
    encoder_samples = load_samples_from_json("encode_samples.json")
    if encoder_samples:
        print(f"{'Name':<40} {'Codec':<8} {'Enabled':<8} Description")
        print("-" * 70)
        for sample in encoder_samples:
            name = f"encode_{sample['name']}"
            codec = sample.get('codec', 'unknown')
            enabled = "✓" if sample.get('enabled', True) else "✗"
            description = sample.get('description', '')
            print(f"{name:<40} {codec:<8} {enabled:<8} {description}")
    else:
        print("No encoder samples found")

    print("=" * 70)

    # Print summary
    decoder_count = len(decoder_samples) if decoder_samples else 0
    encoder_count = len(encoder_samples) if encoder_samples else 0
    total_count = decoder_count + encoder_count

    print(f"\nTotal: {total_count} samples "
          f"({decoder_count} decoder, {encoder_count} encoder)")
    print("\nUse --test '<pattern>' to filter samples "
          "(e.g., --test 'decode_h264_*')")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="Vulkan Video Samples Test Framework")

    # Platform-specific default executable names using PlatformUtils
    encoder_default = ("vk-video-enc-test" +
                       PlatformUtils.get_executable_extension())
    decoder_default = ("vk-video-dec-test" +
                       PlatformUtils.get_executable_extension())

    parser.add_argument(
        "--encoder", "-e",
        default=encoder_default,
        help="Path to vk-video-enc-test executable")
    parser.add_argument(
        "--decoder", "-d",
        default=decoder_default,
        help="Path to vk-video-dec-test executable")
    parser.add_argument(
        "--work-dir", "-w",
        help="Working directory for test files")
    parser.add_argument(
        "--export-json", "-j",
        help="Export results to JSON file")
    parser.add_argument(
        "--codec", "-c",
        choices=["h264", "h265", "av1", "vp9"],
        help="Test only specific codec")
    parser.add_argument(
        "--test", "-t",
        help="Filter tests by name pattern (supports wildcards "
             "like 'h264_*' or 'av1_*')")
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show command lines being executed")
    parser.add_argument(
        "--encoder-only", action="store_true",
        help="Run only encoder tests")
    parser.add_argument(
        "--decoder-only", action="store_true",
        help="Run only decoder tests")
    parser.add_argument(
        "--keep-files", action="store_true",
        help="Keep output artifacts after testing")
    parser.add_argument(
        "--no-auto-download", action="store_true",
        help="Skip automatic download of missing/corrupt sample files")
    parser.add_argument(
        "--deviceID",
        help="Vulkan device ID to use for testing "
             "(decimal or hex with 0x prefix)")
    parser.add_argument(
        "--list-samples", action="store_true",
        help="List all available test samples and exit")
    parser.add_argument(
        "--include-disabled", action="store_true",
        help="Include disabled tests in test suite")
    parser.add_argument(
        "--only-disabled", action="store_true",
        help="Run only disabled tests")
    parser.add_argument(
        "--encode-test-suite",
        help="Path to custom encode test suite JSON file")
    parser.add_argument(
        "--decode-test-suite",
        help="Path to custom decode test suite JSON file")
    return parser


def find_executables(args: argparse.Namespace) -> Tuple[str, str]:
    """Find and resolve executable paths"""
    encoder_path = args.encoder
    decoder_path = args.decoder

    # Try to find encoder using centralized search
    if encoder_path and not Path(encoder_path).is_absolute():
        found_encoder = PlatformUtils.find_executable(encoder_path)
        if found_encoder:
            encoder_path = str(found_encoder)
            if args.verbose:
                print(f"✓ Found encoder: {encoder_path}")

    # Try to find decoder using centralized search
    if decoder_path and not Path(decoder_path).is_absolute():
        found_decoder = PlatformUtils.find_executable(decoder_path)
        if found_decoder:
            decoder_path = str(found_decoder)
            if args.verbose:
                print(f"✓ Found decoder: {decoder_path}")

    return encoder_path, decoder_path


def run_framework_tests(args: argparse.Namespace, encoder_path: str,
                        decoder_path: str) -> bool:
    """Run the actual test framework"""
    device_id = args.deviceID if args.deviceID else None

    # Create test framework with resolved paths
    framework = VulkanVideoTestFramework(
        encoder_path=encoder_path,
        decoder_path=decoder_path,
        work_dir=args.work_dir,
        device_id=device_id,
        verbose=args.verbose,
        keep_files=args.keep_files,
        no_auto_download=args.no_auto_download,
        include_disabled=args.include_disabled,
        only_disabled=args.only_disabled,
        encode_test_suite=args.encode_test_suite,
        decode_test_suite=args.decode_test_suite
    )

    # Determine test type filter
    test_type_filter = None
    if args.encoder_only:
        test_type_filter = TestType.ENCODER
    elif args.decoder_only:
        test_type_filter = TestType.DECODER

    # Run tests
    encode_results, decode_results = framework.run_test_suite(
        codec_filter=args.codec,
        test_type_filter=test_type_filter,
        test_pattern=args.test
    )

    if not encode_results and not decode_results:
        print("No tests were run!")
        return False

    # Print summary
    success = framework.print_summary(encode_results, decode_results)

    # Cleanup results if requested
    framework.cleanup_results()

    # Export results if requested (after cleanup to preserve export files)
    if args.export_json:
        json_path = Path(args.export_json)
        if not json_path.is_absolute():
            json_path = Path.cwd() / json_path
        framework.export_results_json(str(json_path))

    return success


@safe_main_wrapper
def main() -> int:
    """Main entry point for the video codec test framework"""
    parser = create_argument_parser()

    args = parser.parse_args()

    # Handle --list-samples option
    if args.list_samples:
        list_all_samples()
        return 0

    # Find executable paths
    encoder_path, decoder_path = find_executables(args)

    # Run the framework tests
    success = run_framework_tests(args, encoder_path, decoder_path)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
