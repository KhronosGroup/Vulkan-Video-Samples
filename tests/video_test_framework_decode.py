#!/usr/bin/env python3
"""
Vulkan Video Decoder Test Framework
Tests decoder applications for all supported codecs (H.264, H.265, AV1, VP9).

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

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

# Allow running both as package and as script (exception for this file only)
# pylint: disable=wrong-import-position
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from tests.libs.video_test_fetch_sample import FetchableResource  # noqa: E402
from tests.libs.video_test_config_base import (  # noqa: E402
    BaseTestConfig,
    CodecType,
    TestResult,
    TestStatus,
    check_sample_resources,
    create_error_result,
    load_samples_from_json,
)
from tests.libs.video_test_framework_base import (  # noqa: E402
    VulkanVideoTestFrameworkBase,
    run_complete_framework_main,
)
from tests.libs.video_test_platform_utils import (  # noqa: E402
    PlatformUtils,
)
from tests.libs.video_test_utils import (
    add_common_arguments,
    calculate_file_hash,
    safe_main_wrapper,
)
from tests.libs.video_test_result_reporter import (
    list_test_samples,
)


@dataclass
class DecodeSample(BaseTestConfig):
    """Configuration for decoder test cases with download capability"""
    expected_output_md5: str = ""  # Expected MD5 of decoded YUV output

    @property
    def display_name(self) -> str:
        """Get display name with decode_ prefix"""
        return f"decode_{self.name}"

    @property
    def full_path(self) -> Path:
        """Get the full path to the sample file"""
        resources_dir = Path(__file__).parent / "resources"
        return resources_dir / self.source_filepath

    def exists(self) -> bool:
        """Check if the sample file exists"""
        return self.full_path.exists()

    def to_fetchable_resource(self) -> 'FetchableResource':
        """Convert to FetchableResource for downloading"""
        path_obj = Path(self.source_filepath)
        base_dir = str(path_obj.parent)
        filename = path_obj.name

        # Check if checksum has algorithm prefix (e.g., "md5:checksum")
        if self.source_checksum.startswith('md5:'):
            checksum = self.source_checksum[4:]  # Remove "md5:" prefix
            algorithm = 'md5'
        else:
            checksum = self.source_checksum
            algorithm = 'sha256'

        return FetchableResource(
            self.source_url, filename, checksum, base_dir, algorithm
        )


class VulkanVideoDecodeTestFramework(VulkanVideoTestFrameworkBase):
    """Test framework for Vulkan Video decoders"""

    def _load_decode_samples(
            self, json_file: str = "decode_samples.json"
    ) -> List[DecodeSample]:
        """Load decode samples from JSON configuration"""
        samples_data = load_samples_from_json(json_file, test_type="decode")
        samples = []

        for sample_data in samples_data:
            try:
                sample = DecodeSample(
                    name=sample_data["name"],
                    codec=CodecType(sample_data["codec"]),
                    expect_success=True,
                    extra_args=None,
                    description=sample_data["description"],
                    source_url=sample_data["source_url"],
                    source_checksum=sample_data["source_checksum"],
                    source_filepath=sample_data["source_filepath"],
                    enabled=sample_data["enabled"],
                    expected_output_md5=sample_data.get(
                        "expected_output_md5",
                    ),
                )
                samples.append(sample)
            except (KeyError, ValueError, TypeError) as e:
                msg = (
                    f"⚠️  Failed to load sample "
                    f"{sample_data.get('name', 'unknown')}: {e}"
                )
                print(msg)

        return samples

    def __init__(self, decoder_path: str = None, **options):
        # Call base class constructor
        super().__init__(decoder_path, **options)

        # Decoder-specific attributes
        self.decoder_path = (Path(self.executable_path)
                             if self.executable_path else None)
        self.display = options.get('display', False)
        self.verify_md5 = options.get('verify_md5',  True)

        # Load decode samples from JSON file
        test_suite = options.get('test_suite') or 'decode_samples.json'
        self.decode_samples = self._load_decode_samples(test_suite)

        # Validate paths
        if not self._validate_executable():
            raise FileNotFoundError(
                f"Decoder not found: {self.executable_path}")

    def check_resources(self, auto_download: bool = True,
                        test_configs: List[DecodeSample] = None) -> bool:
        """Check if required resource files are available and have correct
        checksums

        Args:
            auto_download: Whether to automatically download missing files
            test_configs: Optional list of test configs to check resources for.
                         If None, checks all loaded samples.
        """
        samples_to_check = (test_configs if test_configs
                            else self.decode_samples)
        return check_sample_resources(samples_to_check,
                                      "decoder resource",
                                      auto_download)

    def _run_decoder_test(self, config: DecodeSample) -> TestResult:
        """Run decoder test for specified codec"""
        if not self.decoder_path:
            return create_error_result(config, "Decoder path not specified")

        # Use the sample file directly from the config
        # (since DecodeSample now contains everything)
        input_file = config.full_path

        if not input_file.exists():
            return create_error_result(
                config,
                f"Input file not found: {input_file}",
            )

        # Determine output file for MD5 verification
        output_file = None
        should_verify_md5 = (
            self.verify_md5
            and config.expected_output_md5
            and config.expected_output_md5.strip()
        )
        if should_verify_md5:
            output_file = self.results_dir / f"decoded_{config.name}.yuv"

        # Build decoder command using shared method
        cmd = self.build_decoder_command(
            decoder_path=self.decoder_path,
            input_file=input_file,
            output_file=output_file,
            extra_decoder_args=config.extra_args,
            no_display=not self.display,
        )

        # Use base class to execute (handles subprocess details)
        run_cwd = self._default_run_cwd()
        result = self.execute_test_command(
            cmd, config, timeout=self.timeout, cwd=run_cwd
        )

        # Verify MD5 if enabled and test succeeded
        if (should_verify_md5 and output_file and output_file.exists() and
                result.status.name == "SUCCESS"):
            actual_md5 = calculate_file_hash(output_file, 'md5')
            if actual_md5:
                if actual_md5.lower() == config.expected_output_md5.lower():
                    print(f"✓ MD5 verification passed: {actual_md5}")
                else:
                    # MD5 mismatch should fail the test
                    result.status = TestStatus.ERROR
                    result.error_message = (
                        "MD5 mismatch: expected "
                        f"{config.expected_output_md5}, got {actual_md5}"
                    )
                    print(f"✗ MD5 verification failed: expected "
                          f"{config.expected_output_md5}, got {actual_md5}")

        # Clean up output file unless keep_files is set
        if (
            output_file
            and output_file.exists()
            and result.status.name == "SUCCESS"
            and not self.keep_files
        ):
            output_file.unlink()

        return result

    def create_test_suite(
        self,
        codec_filter: Optional[str] = None,
        test_pattern: Optional[str] = None,
    ) -> List[DecodeSample]:
        """Create test suite from enabled samples with optional filtering"""
        # Use base class filtering method
        return self.filter_test_suite(
            self.decode_samples, codec_filter, test_pattern,
            self.test_filter
        )

    def run_single_test(self, config: DecodeSample) -> TestResult:
        """Run a single test case - implementation for base class"""
        result = self._run_decoder_test(config)
        self._validate_test_result(result)
        return result

    def run_test_suite(
        self, test_configs: List[DecodeSample] = None
    ) -> List[TestResult]:
        """Run complete test suite using base class implementation"""
        return self.run_test_suite_base(test_configs)

    def print_summary(self, results: List[TestResult] = None,
                      test_type: str = "DECODER",
                      all_samples: list = None) -> bool:
        """Print comprehensive test results summary"""
        if all_samples is None:
            all_samples = self.decode_samples
        return super().print_summary(results, test_type, all_samples)


def list_decoder_samples():
    """List all available decoder test samples"""
    samples_data = load_samples_from_json("decode_samples.json")
    list_test_samples(samples_data, "decoder")


@safe_main_wrapper
def main() -> int:
    """Main entry point for the decode test framework"""
    parser = argparse.ArgumentParser(
        description="Vulkan Video Decoder Test Framework")

    # Add decoder-specific argument
    parser.add_argument("--decoder", "-d",
                        default="vk-video-dec-test",
                        help="Path to vk-video-dec-test executable")

    # Add common arguments with decoder codec choices
    parser = add_common_arguments(
        parser, codec_choices=["h264", "h265", "av1", "vp9"]
    )

    # Add decoder-specific arguments
    parser.add_argument("--display", action="store_true",
                        help="Enable display output "
                             "(removes --noPresent from decoder commands)")
    parser.add_argument(
        "--no-verify-md5",
        action="store_true",
        help=(
            "Disable MD5 verification of decoded output "
            "(enabled by default when expected_output_md5 is present)"
        ),
    )
    parser.add_argument(
        "--decode-test-suite",
        help="Path to custom decode test suite JSON file",
    )

    args = parser.parse_args()

    # Handle --list-samples option
    if args.list_samples:
        list_decoder_samples()
        return 0

    # Find and resolve decoder executable path
    args.decoder = PlatformUtils.resolve_executable_path(
        args.decoder, args.verbose
    )

    # Use shared complete main function
    return run_complete_framework_main(
        VulkanVideoDecodeTestFramework, "decoder", args
    )


if __name__ == "__main__":
    sys.exit(main())
