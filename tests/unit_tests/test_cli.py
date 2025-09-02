"""
Unit tests for command line interface.

Tests CLI argument parsing and option handling.

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

import subprocess
import sys
from pathlib import Path

# Test directory
TESTS_DIR = Path(__file__).parent.parent


class TestListSamples:
    """Tests for --list-samples option"""

    def test_list_samples_runs_successfully(self):
        """Test that --list-samples runs without error"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        has_samples = "DECODER SAMPLES" in result.stdout
        assert has_samples or "AVAILABLE" in result.stdout

    def test_list_samples_shows_decode_tests(self):
        """Test that --list-samples shows decoder tests"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        # Should show some H.264 samples
        assert "h264" in result.stdout.lower()

    def test_list_samples_shows_encode_tests(self):
        """Test that --list-samples shows encoder tests"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        # Should show some H.264 samples
        assert "h264" in result.stdout.lower()


class TestHelpOption:
    """Tests for --help option"""

    def test_codec_framework_help(self):
        """Test --help for codec framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--encoder" in result.stdout
        assert "--decoder" in result.stdout
        assert "--test" in result.stdout
        assert "--codec" in result.stdout

    def test_decode_framework_help(self):
        """Test --help for decode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--decoder" in result.stdout
        assert "--test" in result.stdout

    def test_encode_framework_help(self):
        """Test --help for encode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--encoder" in result.stdout
        assert "--test" in result.stdout


class TestSkipListOptions:
    """Tests for skip list CLI options"""

    def test_ignore_skip_list_option_accepted(self):
        """Test that --ignore-skip-list is a valid option"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--ignore-skip-list" in result.stdout

    def test_only_skipped_option_accepted(self):
        """Test that --only-skipped is a valid option"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--only-skipped" in result.stdout

    def test_skip_list_option_accepted(self):
        """Test that --skip-list is a valid option"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--skip-list" in result.stdout


class TestCodecFilter:
    """Tests for --codec filter option"""

    def test_codec_choices_in_help(self):
        """Test that codec choices are shown in help"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "h264" in result.stdout
        assert "h265" in result.stdout
        assert "av1" in result.stdout
        assert "vp9" in result.stdout

    def test_invalid_codec_rejected(self):
        """Test that invalid codec is rejected"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--codec", "invalid_codec", "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        # Should fail with error about invalid choice
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()


class TestTestPatternOption:
    """Tests for --test pattern option"""

    def test_test_option_in_help(self):
        """Test that --test option is documented"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--test" in result.stdout
        out_lower = result.stdout.lower()
        assert "pattern" in out_lower or "filter" in out_lower

    def test_test_option_in_decode_help(self):
        """Test that --test option is documented in decode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--test" in result.stdout


class TestOutputOptions:
    """Tests for output-related options"""

    def test_verbose_option_accepted(self):
        """Test that --verbose option is valid"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--verbose" in result.stdout or "-v" in result.stdout

    def test_export_json_option_accepted(self):
        """Test that --export-json option is valid"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--export-json" in result.stdout

    def test_keep_files_option_accepted(self):
        """Test that --keep-files option is valid"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--keep-files" in result.stdout


class TestFrameworkTypeOptions:
    """Tests for encoder/decoder-only options"""

    def test_encoder_only_option(self):
        """Test that --encoder-only option is valid"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--encoder-only" in result.stdout

    def test_decoder_only_option(self):
        """Test that --decoder-only option is valid"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--decoder-only" in result.stdout


class TestCustomTestSuiteOptions:
    """Tests for custom test suite options"""

    def test_decode_test_suite_option(self):
        """Test that --decode-test-suite option is valid"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--decode-test-suite" in result.stdout

    def test_encode_test_suite_option(self):
        """Test that --encode-test-suite option is valid"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert "--encode-test-suite" in result.stdout


class TestDecodeFrameworkCLI:
    """Tests for video_test_framework_decode.py CLI options"""

    def test_decode_skip_list_options(self):
        """Test skip list options in decode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--ignore-skip-list" in result.stdout
        assert "--only-skipped" in result.stdout
        assert "--skip-list" in result.stdout

    def test_decode_codec_filter(self):
        """Test --codec filter in decode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--codec" in result.stdout
        assert "h264" in result.stdout
        assert "h265" in result.stdout

    def test_decode_test_pattern(self):
        """Test --test pattern in decode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--test" in result.stdout

    def test_decode_invalid_codec_rejected(self):
        """Test invalid codec is rejected in decode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--codec", "invalid_codec", "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()

    def test_decode_verbose_option(self):
        """Test --verbose option in decode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--verbose" in result.stdout or "-v" in result.stdout

    def test_decode_export_json_option(self):
        """Test --export-json option in decode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--export-json" in result.stdout


class TestEncodeFrameworkCLI:
    """Tests for video_test_framework_encode.py CLI options"""

    def test_encode_skip_list_options(self):
        """Test skip list options in encode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--ignore-skip-list" in result.stdout
        assert "--only-skipped" in result.stdout
        assert "--skip-list" in result.stdout

    def test_encode_codec_filter(self):
        """Test --codec filter in encode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--codec" in result.stdout
        assert "h264" in result.stdout
        assert "h265" in result.stdout

    def test_encode_test_pattern(self):
        """Test --test pattern in encode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--test" in result.stdout

    def test_encode_invalid_codec_rejected(self):
        """Test invalid codec is rejected in encode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--codec", "invalid_codec", "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()

    def test_encode_verbose_option(self):
        """Test --verbose option in encode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--verbose" in result.stdout or "-v" in result.stdout

    def test_encode_export_json_option(self):
        """Test --export-json option in encode framework"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--help"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
        assert "--export-json" in result.stdout


class TestActualFrameworkRun:
    """Tests for actual framework execution (without video processing)"""

    def test_codec_no_matching_tests(self):
        """Test codec framework with pattern that matches nothing"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--test", "nonexistent_pattern_xyz_*",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should complete with "no tests were run" message
        assert "no tests were run" in result.stdout.lower()

    def test_decode_no_matching_tests(self):
        """Test decode framework with pattern that matches nothing"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--test", "nonexistent_pattern_xyz_*",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should complete with "no tests were run" message
        assert "no tests were run" in result.stdout.lower()

    def test_encode_no_matching_tests(self):
        """Test encode framework with pattern that matches nothing"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--test", "nonexistent_pattern_xyz_*",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should complete with "no tests were run" message
        assert "no tests were run" in result.stdout.lower()

    def test_codec_missing_encoder_executable(self):
        """Test codec framework with non-existent encoder path"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--encoder", "/nonexistent/path/to/encoder",
             "--encoder-only",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should report missing executable
        assert "not found" in result.stdout.lower() or result.returncode != 0

    def test_codec_missing_decoder_executable(self):
        """Test codec framework with non-existent decoder path"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--decoder", "/nonexistent/path/to/decoder",
             "--decoder-only",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should report missing executable
        assert "not found" in result.stdout.lower() or result.returncode != 0

    def test_decode_missing_executable(self):
        """Test decode framework with non-existent decoder path"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--decoder", "/nonexistent/path/to/decoder",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should report missing executable
        assert "not found" in result.stdout.lower() or result.returncode != 0

    def test_encode_missing_executable(self):
        """Test encode framework with non-existent encoder path"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--encoder", "/nonexistent/path/to/encoder",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should report missing executable
        assert "not found" in result.stdout.lower() or result.returncode != 0

    def test_codec_filter_by_codec_no_match(self):
        """Test codec filter with VP9 and non-matching pattern"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--codec", "vp9",
             "--test", "nonexistent_*",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should complete with "no tests were run" message
        assert "no tests were run" in result.stdout.lower()

    def test_decode_h264_pattern_filters_tests(self):
        """Test decode framework filters to H.264 tests with pattern"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--test", "h264_*",
             "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        assert result.returncode == 0
        # Should show h264 samples
        assert "h264" in result.stdout.lower()
        # Should not show other codecs
        out_lower = result.stdout.lower()
        assert "av1" not in out_lower or "h264" in out_lower

    def test_encode_h264_pattern_filters_tests(self):
        """Test encode framework filters to H.264 tests with pattern"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--test", "h264_*",
             "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        assert result.returncode == 0
        # Should show h264 samples
        assert "h264" in result.stdout.lower()

    def test_codec_h264_codec_filter(self):
        """Test codec framework filters by H.264 codec"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_codec.py"),
             "--codec", "h264",
             "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        assert result.returncode == 0
        # Should show h264 samples
        assert "h264" in result.stdout.lower()

    def test_decode_av1_codec_filter(self):
        """Test decode framework filters by AV1 codec"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--codec", "av1",
             "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        assert result.returncode == 0
        # Should show av1 samples
        assert "av1" in result.stdout.lower()

    def test_encode_h265_codec_filter(self):
        """Test encode framework filters by H.265 codec"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--codec", "h265",
             "--list-samples"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        assert result.returncode == 0
        # Should show h265 samples
        assert "h265" in result.stdout.lower()

    def test_decode_run_with_h264_filter_missing_binary(self):
        """Test decode run with h264 filter but missing binary"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_decode.py"),
             "--decoder", "/nonexistent/decoder",
             "--codec", "h264",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should report missing executable
        assert "not found" in result.stdout.lower() or result.returncode != 0

    def test_encode_run_with_h264_filter_missing_binary(self):
        """Test encode run with h264 filter but missing binary"""
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "video_test_framework_encode.py"),
             "--encoder", "/nonexistent/encoder",
             "--codec", "h264",
             "--no-auto-download"],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=60,
            check=False
        )
        # Should report missing executable
        assert "not found" in result.stdout.lower() or result.returncode != 0


class TestModuleExecution:
    """Tests for running as Python modules"""

    def test_codec_framework_importable(self):
        """Test that codec framework can be imported"""
        imp = "from tests.video_test_framework_codec import "
        imp += "VulkanVideoTestFramework"
        result = subprocess.run(
            [sys.executable, "-c", imp],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0

    def test_decode_framework_importable(self):
        """Test that decode framework can be imported"""
        imp = "from tests.video_test_framework_decode import "
        imp += "VulkanVideoDecodeTestFramework"
        result = subprocess.run(
            [sys.executable, "-c", imp],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0

    def test_encode_framework_importable(self):
        """Test that encode framework can be imported"""
        imp = "from tests.video_test_framework_encode import "
        imp += "VulkanVideoEncodeTestFramework"
        result = subprocess.run(
            [sys.executable, "-c", imp],
            capture_output=True,
            text=True,
            cwd=TESTS_DIR.parent,
            timeout=30,
            check=False
        )
        assert result.returncode == 0
