"""
Video Test Framework Base
Contains the base class for Vulkan Video test frameworks.

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

import fnmatch
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from tests.libs.video_test_config_base import (
    BaseTestConfig,
    TestFilter,
    TestResult,
    TestStatus,
    create_error_result,
)

from tests.libs.video_test_platform_utils import (
    PlatformUtils,
)

from tests.libs.video_test_result_reporter import (
    get_status_display,
    print_codec_breakdown,
    print_detailed_results,
    print_final_summary,
    print_command_output,
)
from tests.libs.video_test_utils import (
    DEFAULT_TEST_TIMEOUT,
)


# pylint: disable=too-many-public-methods
class VulkanVideoTestFrameworkBase:
    """Base class for Vulkan Video test frameworks providing common
    functionality"""

    def __init__(self, executable_path: str = None, **options):
        self.executable_path = executable_path
        self.work_dir = options.get('work_dir')
        self.device_id = options.get('device_id')
        self.verbose = options.get('verbose', False)

        # Convert legacy boolean flags to TestFilter enum
        include_disabled = options.get('include_disabled', False)
        only_disabled = options.get('only_disabled', False)
        if only_disabled:
            test_filter = TestFilter.DISABLED
        elif include_disabled:
            test_filter = TestFilter.ALL
        else:
            test_filter = TestFilter.ENABLED

        self._options = {
            'keep_files': options.get('keep_files', False),
            'no_auto_download': options.get('no_auto_download', False),
            'timeout': int(options.get('timeout', DEFAULT_TEST_TIMEOUT)),
            'test_filter': test_filter,
        }

        # Ensure directories exist via properties
        self.resources_dir.mkdir(exist_ok=True)
        self.work_dir_path.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

        # Results tracking
        self.results: List[TestResult] = []

    @property
    def keep_files(self) -> bool:
        """Whether to keep output artifacts after the run."""
        return bool(self._options['keep_files'])

    @property
    def no_auto_download(self) -> bool:
        """If true, do not auto-download missing/corrupt samples."""
        return bool(self._options['no_auto_download'])

    @property
    def timeout(self) -> int:
        """Per-test timeout in seconds."""
        return int(self._options['timeout'])

    @property
    def test_filter(self) -> TestFilter:
        """Test filter mode (ENABLED, DISABLED, or ALL)."""
        return self._options['test_filter']

    @property
    def include_disabled(self) -> bool:
        """Whether to include disabled tests (legacy compatibility)."""
        return self.test_filter == TestFilter.ALL

    @property
    def only_disabled(self) -> bool:
        """Whether to run only disabled tests (legacy compatibility)."""
        return self.test_filter == TestFilter.DISABLED

    def _validate_executable(self) -> bool:
        """Validate that the test executable exists, checking both filesystem
        and PATH"""
        if not self.executable_path:
            print("✗ Executable path not specified")
            return False

        # Use PlatformUtils to find the executable (it has all search
        # paths built-in now)
        found_exe = PlatformUtils.find_executable(self.executable_path)

        if found_exe:
            self.executable_path = str(found_exe)
            if self.verbose:
                print(f"✓ Found executable: {self.executable_path}")
            return True

        print(f"✗ Executable not found: {self.executable_path}")
        print("Please ensure the executable is built and available in PATH "
              "or provide full path.")
        print("  Searched in: build directories, install/*/bin, PATH, "
              "and common output directories")
        return False

    def check_resources(self, auto_download: bool = True,
                        test_configs: list = None) -> bool:
        """Check if required resource files are available - to be implemented
        by subclasses

        Args:
            auto_download: Whether to automatically download missing files
            test_configs: Optional list of test configs to check resources for
        """
        raise NotImplementedError(
            "Subclasses must implement check_resources method"
        )

    def cleanup_results(self, test_type: str = "test") -> None:
        """Clean up output artifacts (decoded/encoded files) if keep_files
        is False and there are no test failures"""
        has_failures = any(
            r.status in [TestStatus.ERROR, TestStatus.CRASH]
            for r in self.results
        )

        # Always export JSON results if we have any results
        if self.results:
            json_filename = f"{test_type}_results.json"
            json_file = self.results_dir / json_filename
            try:
                self.export_results_json(str(json_file), test_type)
                if has_failures:
                    print(f"🔍 Test failures detected - results saved to: "
                          f"{json_file}")
                else:
                    print(f"📊 Results exported to: {json_file}")
            except (OSError, IOError, ValueError, TypeError) as e:
                print(f"⚠️  Could not save JSON results file: {e}")

        if self.keep_files:
            print(f"📁 Results kept in: {self.results_dir}")
            return

        if has_failures:
            print(f"🔍 Test failures detected - results kept for debugging "
                  f"in: {self.results_dir}")
            return

        try:
            # Remove all files in results directory except JSON results
            for item in self.results_dir.iterdir():
                if item.is_file() and not item.name.endswith('_results.json'):
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print("🧹 Cleaned up output artifacts")
        except (OSError, PermissionError) as e:
            print(f"⚠️  Failed to clean up results: {e}")

    def create_test_suite(self, codec_filter: str = None,
                          test_pattern: str = None):
        """Create test suite - to be implemented by subclasses"""
        raise NotImplementedError(
            "Subclasses must implement create_test_suite method"
        )

    def run_test_suite(self, test_configs) -> List[TestResult]:
        """Run test suite using base implementation"""
        return self.run_test_suite_base(test_configs)

    def determine_test_status(self, returncode: int,
                              _stderr: str = "") -> TestStatus:
        """
        Determine test status based on return code and stderr output.

        Args:
            returncode: Process return code
            stderr: Standard error output (optional, for better status
                detection)

        Returns:
            TestStatus enum value
        """
        # Normalize logic to a single return for readability/linting
        status = TestStatus.ERROR
        if returncode == 0:
            status = TestStatus.SUCCESS
        elif returncode == 77:
            status = TestStatus.NOT_SUPPORTED
        else:
            abs_code = abs(returncode)
            if abs_code in (6, 11):  # SIGABRT, SIGSEGV
                status = TestStatus.CRASH
            elif PlatformUtils.is_windows():
                if abs_code in (0xC0000005, 3221225477):  # access violation
                    status = TestStatus.CRASH
                elif returncode == -1073741819:  # assert/abort (signed)
                    status = TestStatus.CRASH
                elif returncode in (-1, 1, 3, 22):  # common codes
                    status = TestStatus.CRASH

        return status

    def _count_results_by_status(self, results: List[TestResult]) -> tuple:
        """Count results by status type"""
        passed = sum(1 for r in results if r.status == TestStatus.SUCCESS)
        not_supported = sum(
            1 for r in results if r.status == TestStatus.NOT_SUPPORTED
        )
        crashed = sum(1 for r in results if r.status == TestStatus.CRASH)
        failed = sum(1 for r in results if r.status == TestStatus.ERROR)
        return passed, not_supported, crashed, failed

    def _count_disabled_tests(self, samples: list) -> int:
        """Count disabled tests from samples list"""
        return sum(1 for s in samples
                   if hasattr(s, 'enabled') and not s.enabled)

    def _count_enabled_tests(self, samples: list) -> int:
        """Count enabled tests from samples list"""
        return sum(1 for s in samples
                   if not hasattr(s, 'enabled') or s.enabled)

    def _group_results_by_codec(self, results: List[TestResult]) -> dict:
        """Group results by codec with counts"""
        codec_results = {}
        for result in results:
            codec = result.config.codec.value
            if codec not in codec_results:
                codec_results[codec] = {
                    "pass": 0, "not_supported": 0, "crash": 0, "fail": 0,
                    "total": 0
                }

            codec_results[codec]["total"] += 1
            if result.status == TestStatus.SUCCESS:
                codec_results[codec]["pass"] += 1
            elif result.status == TestStatus.NOT_SUPPORTED:
                codec_results[codec]["not_supported"] += 1
            elif result.status == TestStatus.CRASH:
                codec_results[codec]["crash"] += 1
            else:
                codec_results[codec]["fail"] += 1
        return codec_results

    def print_summary(self, results: List[TestResult] = None,
                      test_type: str = "TEST",
                      all_samples: list = None) -> bool:
        """Print comprehensive test results summary with codec breakdown"""
        if results is None:
            results = self.results

        test_type_upper = test_type.upper()
        print("=" * 70)
        print(f"VULKAN VIDEO {test_type_upper} TEST RESULTS SUMMARY")
        print("=" * 70)

        passed, not_supported, crashed, failed = self._count_results_by_status(
            results
        )
        codec_results = self._group_results_by_codec(results)

        print_codec_breakdown(codec_results)
        print("-" * 70)

        print_detailed_results(results)

        print("-" * 70)

        # Count disabled/enabled tests based on filter mode
        disabled_count = 0
        enabled_count = 0
        if self.test_filter == TestFilter.DISABLED and all_samples:
            # In DISABLED mode, show how many enabled tests are skipped
            enabled_count = self._count_enabled_tests(all_samples)
        elif self.test_filter == TestFilter.ENABLED and all_samples:
            # In ENABLED mode, show how many disabled tests are skipped
            disabled_count = self._count_disabled_tests(all_samples)
        # When TestFilter.ALL, don't count disabled/enabled separately

        total_including_all = len(results) + disabled_count + enabled_count
        print(f"Total Tests:   {total_including_all:3}")
        if self.test_filter == TestFilter.DISABLED and enabled_count > 0:
            print(f"Enabled (skipped): {enabled_count:3} "
                  "(--only-disabled mode)")
        elif self.test_filter == TestFilter.ENABLED and disabled_count > 0:
            print(f"Disabled:      {disabled_count:3} "
                  "(use --include-disabled to run)")
        # Don't show disabled count when using --include-disabled (ALL mode)

        print(f"Passed:        {passed:3}")
        print(f"Not Supported: {not_supported:3}")
        print(f"Crashed:       {crashed:3}")
        print(f"Failed:        {failed:3}")
        print(f"Success Rate: {passed/len(results)*100:.1f}%")

        return print_final_summary(
            (passed, not_supported, crashed, failed), test_type
        )

    def _default_run_cwd(self) -> Optional[Path]:
        """Return default working directory for subprocess execution."""
        if self.results_dir and self.results_dir.exists():
            return self.results_dir
        return None

    def _result_to_dict(self, result: TestResult, test_type: str) -> dict:
        """Convert a TestResult to a dictionary for JSON export"""
        # Use display_name if available, otherwise use name
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
            "error_message": result.error_message,
            "command_line": result.command_line
        }

        # Add input file path
        if hasattr(result.config, 'full_path'):
            result_dict["input_file"] = str(result.config.full_path)
        elif hasattr(result.config, 'full_yuv_path'):
            result_dict["input_file"] = str(
                result.config.full_yuv_path
            )

        # Add profile if it exists (for encoder tests)
        if hasattr(result.config, 'profile') and result.config.profile:
            result_dict["profile"] = result.config.profile

        return result_dict

    def result_to_dict(self, result: TestResult, test_type: str) -> dict:
        """Public wrapper for converting a TestResult to dictionary form."""
        return self._result_to_dict(result, test_type)

    def export_results_json(self, output_file: str, test_type: str) -> bool:
        """
        Export test results to JSON file.

        Args:
            output_file: Output JSON file path
            test_type: Type of test ("decoder" or "encoder")

        Returns:
            True if export successful, False otherwise
        """
        try:
            results_data = [
                self.result_to_dict(result, test_type)
                for result in self.results
            ]

            # Ensure directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "summary": {
                        "total_tests": len(self.results),
                        "passed": sum(
                            1 for r in self.results
                            if r.status == TestStatus.SUCCESS
                        ),
                        "not_supported": sum(
                            1 for r in self.results
                            if r.status == TestStatus.NOT_SUPPORTED
                        ),
                        "crashed": sum(
                            1 for r in self.results
                            if r.status == TestStatus.CRASH
                        ),
                        "failed": sum(
                            1 for r in self.results
                            if r.status == TestStatus.ERROR
                        )
                    },
                    "results": results_data
                }, f, indent=2)

            return True

        except (OSError, IOError) as e:
            print(f"✗ Failed to export {test_type} results: {e}")
            return False

    # Computed path properties to reduce stored attributes
    @property
    def test_dir(self) -> Path:
        """Directory containing this test module."""
        return Path(__file__).parent.parent

    @property
    def project_root(self) -> Path:
        """Repository root directory (one level above tests)."""
        return self.test_dir.parent

    @property
    def resources_dir(self) -> Path:
        """Folder where test resources are stored."""
        return self.test_dir / "resources"

    @property
    def work_dir_path(self) -> Path:
        """Working directory used to place outputs and results."""
        return Path(self.work_dir) if self.work_dir else self.test_dir

    @property
    def results_dir(self) -> Path:
        """Directory where per-run results are written."""
        return self.work_dir_path / "results"

    def _validate_test_result(self, result: TestResult) -> None:
        """Validate test result against expectations"""
        config = result.config

        # Status is already determined by determine_test_status()
        # Add appropriate error messages for different failure types
        # Only set error message if one doesn't already exist
        # (e.g., from MD5 verification or other checks)
        if config.expect_success and result.status == TestStatus.ERROR:
            if not result.error_message:
                result.error_message = (
                    f"Expected success but got return code {result.returncode}"
                )
        elif config.expect_success and result.status == TestStatus.CRASH:
            if not result.error_message:
                result.error_message = (
                    f"Application crashed with return code {result.returncode}"
                )

        # Check for unexpected failures or concerning warnings
        if result.warning_found:
            # For now, warnings don't fail tests, just log them
            pass

    def execute_test_command(
        self,
        cmd: list,
        config: BaseTestConfig,
        timeout: int = DEFAULT_TEST_TIMEOUT,
        cwd: Optional[Path] = None,
    ) -> TestResult:
        """Execute a test command and return result

        Args:
            cmd: Command and arguments list
            config: The test configuration
            timeout: Default timeout in seconds
                (overridden by framework/config)
            cwd: Optional working directory for the subprocess
        """
        command_line = ' '.join(cmd)

        if self.verbose:
            print(f"    Command: {command_line}")

        try:
            # Get platform-specific subprocess kwargs
            # (includes capture_output and text)
            subprocess_kwargs = (
                PlatformUtils.get_subprocess_kwargs()
            )
            # Prefer per-test timeout if provided in config; handle None safely
            cfg_timeout = getattr(config, 'timeout', None)
            if cfg_timeout is not None:
                try:
                    subprocess_kwargs['timeout'] = int(cfg_timeout)
                except (TypeError, ValueError):
                    # Fall back to framework or default timeout
                    subprocess_kwargs['timeout'] = (
                        int(self.timeout) if self.timeout else int(timeout)
                    )
            else:
                subprocess_kwargs['timeout'] = (
                    int(self.timeout) if self.timeout else int(timeout)
                )
            if cwd is not None:
                subprocess_kwargs['cwd'] = str(cwd)

            result = subprocess.run(cmd, check=False, **subprocess_kwargs)

            return TestResult(
                config=config,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=0,  # Set by caller
                status=self.determine_test_status(
                    result.returncode, result.stderr),
                command_line=command_line
            )

        except subprocess.TimeoutExpired:
            return create_error_result(
                config, "Test timed out", command_line)
        except (OSError, subprocess.SubprocessError) as e:
            return create_error_result(config, str(e), command_line)

    def build_decoder_command(  # pylint: disable=too-many-arguments
        self,
        decoder_path: Path,
        input_file: Path,
        *,
        output_file: Path = None,
        extra_decoder_args: list = None,
        no_display: bool = True,
    ) -> list:
        """Build decoder command with standard options

        Args:
            decoder_path: Path to decoder executable
            input_file: Input video file to decode
            output_file: Optional output YUV file path
            extra_decoder_args: Optional extra decoder arguments
            no_display: If True, add --noPresent flag

        Returns:
            List of command and arguments
        """
        cmd = [
            str(decoder_path),
            "-i", str(input_file),
            "--verbose",
            "--enablePostProcessFilter", "0",
        ]

        # Add output file if specified
        if output_file:
            cmd.extend(["-o", str(output_file)])

        # Add --noPresent by default unless display is requested
        if no_display:
            cmd.append("--noPresent")

        # Add device ID if specified
        if self.device_id is not None:
            cmd.extend(["--deviceID", str(self.device_id)])

        # Add extra decoder arguments
        if extra_decoder_args:
            cmd.extend(extra_decoder_args)

        return cmd

    def run_decoder_validation(
        self,
        decoder_path: Path,
        input_file: Path,
        extra_decoder_args: list = None,
        config: BaseTestConfig = None,
    ) -> bool:
        """Run decoder to validate an encoded file

        Args:
            decoder_path: Path to decoder executable
            input_file: Input video file to decode
            extra_decoder_args: Optional extra decoder arguments
            config: Test configuration (for timeout settings)

        Returns:
            True if decoder successfully decoded the file, False otherwise
        """
        if not decoder_path or not decoder_path.exists():
            print("  ⚠️  Decoder path not valid for validation")
            return False

        print(f"  🔍 Validating with decoder: {input_file.name}")

        # Build decoder command
        cmd = self.build_decoder_command(
            decoder_path=decoder_path,
            input_file=input_file,
            output_file=None,  # No output needed for validation
            extra_decoder_args=extra_decoder_args,
            no_display=True,
        )

        # Print decoder command if verbose
        if self.verbose:
            print(f"    Decoder command: {' '.join(cmd)}")

        # Run decoder using base class method
        run_cwd = self._default_run_cwd()
        result = self.execute_test_command(
            cmd, config, timeout=self.timeout, cwd=run_cwd
        )

        # Show decoder output if verbose
        if self.verbose:
            if result.stdout:
                print("    Decoder stdout:")
                print(result.stdout)
            if result.stderr:
                print("    Decoder stderr:")
                print(result.stderr)

        # Check if decoder succeeded
        if result.status == TestStatus.SUCCESS:
            print("  ✓ Decoder validation passed")
            return True

        # Decoder failed
        print(f"  ✗ Decoder validation failed "
              f"(status: {result.status.name}, "
              f"exit code: {result.returncode})")
        return False

    def filter_test_suite(
        self,
        samples: list,
        codec_filter: Optional[str] = None,
        test_pattern: Optional[str] = None,
        test_filter: TestFilter = TestFilter.ENABLED,
    ) -> list:
        """Filter test samples based on codec and pattern

        Args:
            samples: List of test samples to filter
            codec_filter: Filter by codec type
            test_pattern: Filter by name pattern
            test_filter: Filter mode (ENABLED, DISABLED, or ALL)
        """
        filtered_samples = []
        for sample in samples:
            # Apply codec filter first
            if codec_filter and sample.codec.value != codec_filter:
                continue

            # Apply name pattern filter
            # (match against display_name or name)
            sample_name = getattr(sample, 'display_name', sample.name)
            exact_match = test_pattern and sample_name == test_pattern

            if test_pattern and not exact_match and not fnmatch.fnmatch(sample_name, test_pattern):
                continue

            # Handle enabled/disabled filtering
            # But allow exact matches to override disabled filtering
            if hasattr(sample, 'enabled'):
                if test_filter == TestFilter.DISABLED and sample.enabled and not exact_match:
                    # Skip enabled samples when filter is DISABLED, unless exact match
                    continue
                if test_filter == TestFilter.ENABLED and not sample.enabled and not exact_match:
                    # Skip disabled samples when filter is ENABLED, unless exact match
                    continue
                # TestFilter.ALL includes both enabled and disabled

            filtered_samples.append(sample)

        return filtered_samples

    def run_test_suite_base(self, test_configs: list) -> List[TestResult]:
        """Run complete test suite with common flow"""
        if test_configs is None:
            test_configs = self.create_test_suite()

        self._print_suite_start()

        # Check resource files (auto-download missing/corrupt unless disabled)
        if not self._check_and_prepare_resources(test_configs):
            return []

        print()

        results: List[TestResult] = []
        total = len(test_configs)

        for i, config in enumerate(test_configs, 1):
            # Print test header
            test_name = getattr(config, 'display_name', config.name)
            print(f"[{i}/{total}] Running: {test_name}")

            # Run test and measure time
            try:
                start_time = time.time()
                result = self.run_single_test(config)
                result.execution_time = time.time() - start_time
                results.append(result)
                self.results.append(result)

                # Print result
                self._print_single_result(result)

            except (KeyError, ValueError, AttributeError, TypeError) as err:
                # Handle unexpected errors gracefully
                error_result = TestResult(
                    config=config,
                    returncode=-1,
                    execution_time=0,
                    status=TestStatus.ERROR,
                    stdout="",
                    stderr="",
                    error_message=str(err),
                )
                results.append(error_result)
                self.results.append(error_result)
                print(f"⚠️  ERROR: {err}")

            print()

        return results

    def run_single_test(self, config):
        """Run a single test - to be implemented by subclasses"""
        raise NotImplementedError(
            "Subclasses must implement run_single_test method"
        )

    def _print_suite_start(self) -> None:
        """Print header information for the test run."""
        print("=" * 70)
        print("VULKAN VIDEO TEST SUITE")
        print("=" * 70)
        print(f"Binary: {self.executable_path}")
        if self.work_dir:
            print(f"Work Dir: {self.work_dir}")
        print()

    def _check_and_prepare_resources(self, test_configs: list = None) -> bool:
        """Check and optionally download resources, printing clear errors.

        Args:
            test_configs: Optional list of test configs to check resources for.
                         Passed to check_resources() if supported.
        """
        auto_download = not self.no_auto_download

        # Try to pass test_configs to check_resources if it supports it
        try:
            ok = self.check_resources(auto_download=auto_download,
                                      test_configs=test_configs)
        except TypeError:
            # Fall back to old signature if subclass doesn't support test_configs
            ok = self.check_resources(auto_download=auto_download)

        if ok:
            return True
        if auto_download:
            print(
                "✗ FATAL: Missing or corrupt resource files could not be "
                "downloaded"
            )
        else:
            print(
                "✗ FATAL: Missing or corrupt resource files (auto-download "
                "disabled)"
            )
        return False

    def _print_single_result(self, result: TestResult) -> None:
        """Print a concise line for the result and optional diagnostics."""
        label, symbol = get_status_display(result.status)
        print(f"{symbol} {label} ({result.execution_time:.2f}s)")

        if result.error_message:
            print(f"   Error: {result.error_message}")

        # Always show command and output on crash, or when verbose is enabled
        if result.status == TestStatus.CRASH:
            print(f"   Command: {result.command_line}")
            print_command_output(result)
        elif self.verbose and (result.stdout or result.stderr):
            print_command_output(result)


def run_framework_main(
    framework, test_configs, export_json_path, test_type: str
) -> int:
    """Common main execution logic for test frameworks

    Args:
        framework: Instantiated test framework
        test_configs: Test configurations to run
        export_json_path: Optional path to export JSON results
        test_type: Type of test ("decoder" or "encoder")

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Run tests
        results = framework.run_test_suite(test_configs)

        if not results:
            print("No tests were run!")
            return 1

        # Print summary
        success = framework.print_summary(results)

        # Export results if requested
        if export_json_path:
            framework.export_results_json(export_json_path, test_type)

        # Cleanup
        framework.cleanup_results(test_type)

        return 0 if success else 1

    except (OSError, ValueError, RuntimeError, KeyboardInterrupt) as e:
        print(f"✗ FATAL ERROR: {e}")
        return 1


def run_complete_framework_main(framework_class, test_type: str, args) -> int:
    """Complete main execution including framework creation

    Args:
        framework_class: The framework class to instantiate
        test_type: Type of test ("decoder" or "encoder")
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Create framework instance with appropriate arguments
    if test_type == "decoder":
        framework = framework_class(
            decoder_path=args.decoder,
            work_dir=args.work_dir,
            device_id=args.device_id,
            verbose=args.verbose,
            keep_files=args.keep_files,
            display=args.display,
            no_auto_download=args.no_auto_download,
            timeout=args.timeout,
            verify_md5=not args.no_verify_md5,
            include_disabled=args.include_disabled,
            only_disabled=args.only_disabled,
            test_suite=args.decode_test_suite,
        )
    else:  # encoder
        validate_with_decoder = getattr(args, 'validate_with_decoder', True)
        decoder_path = (
            getattr(args, 'decoder', None) if validate_with_decoder else None
        )
        decoder_args = (
            getattr(args, 'decoder_args', None)
            if validate_with_decoder else None
        )
        framework = framework_class(
            encoder_path=args.encoder,
            work_dir=args.work_dir,
            device_id=args.device_id,
            verbose=args.verbose,
            keep_files=args.keep_files,
            no_auto_download=args.no_auto_download,
            timeout=args.timeout,
            include_disabled=args.include_disabled,
            only_disabled=args.only_disabled,
            test_suite=args.encode_test_suite,
            validate_with_decoder=validate_with_decoder,
            decoder=decoder_path,
            decoder_args=decoder_args,
        )

    # Create test suite with filters
    test_configs = framework.create_test_suite(
        codec_filter=args.codec,
        test_pattern=args.test
    )

    # Run tests using shared main logic
    return run_framework_main(
        framework, test_configs, args.export_json, test_type
    )
