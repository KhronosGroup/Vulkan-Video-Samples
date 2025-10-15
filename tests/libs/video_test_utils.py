"""
Video Test Utilities
Common utility functions for command-line argument parsing and framework
helpers.

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

import hashlib
from pathlib import Path

# Constants
DEFAULT_TEST_TIMEOUT = 120  # seconds


def calculate_file_hash(file_path: Path, algorithm: str = 'md5') -> str:
    """Calculate file hash

    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5' or 'sha256')

    Returns:
        Hash string (empty on error)
    """
    try:
        hasher = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):  # Read in 64KB chunks
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError) as e:
        print(f"⚠️  Failed to calculate {algorithm.upper()} "
              f"for {file_path}: {e}")
        return ""


def verify_file_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum

    Supports MD5 (with md5: prefix) and SHA256 (default).

    Args:
        file_path: Path to file
        expected_checksum: Expected checksum (use md5: prefix for MD5)

    Returns:
        True if checksum matches, False otherwise
    """
    try:
        # Detect checksum algorithm
        if expected_checksum.startswith('md5:'):
            algorithm = 'md5'
            expected = expected_checksum[4:]  # Strip md5: prefix
        else:
            algorithm = 'sha256'
            expected = expected_checksum

        actual = calculate_file_hash(file_path, algorithm)
        return actual == expected if actual else False
    except (OSError, IOError):
        return False


def add_common_arguments(parser, codec_choices=None):
    """Add common command-line arguments to parser

    Args:
        parser: ArgumentParser instance to add arguments to
        codec_choices: Optional list of valid codec choices

    Returns:
        Modified parser
    """
    parser.add_argument("--work-dir", "-w",
                        help="Working directory for test files")
    parser.add_argument("--export-json", "-j",
                        help="Export results to JSON file")
    parser.add_argument("--codec", "-c",
                        choices=codec_choices,
                        help="Test only specific codec")
    parser.add_argument(
        "--test",
        "-t",
        help="Filter tests by name pattern (supports wildcards)",
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show command lines being executed")
    parser.add_argument("--keep-files", action="store_true",
                        help="Keep output artifacts (decoded/encoded files)")
    parser.add_argument(
        "--no-auto-download",
        action="store_true",
        help="Skip automatic download of missing/corrupt sample files",
    )
    parser.add_argument("--list-samples", action="store_true",
                        help="List all available test samples and exit")
    parser.add_argument(
        "--device-id",
        help="Select device ID to use (platform-specific)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TEST_TIMEOUT,
        help=f"Per-test timeout in seconds (default: {DEFAULT_TEST_TIMEOUT})",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include disabled tests in test suite",
    )
    parser.add_argument(
        "--only-disabled",
        action="store_true",
        help="Run only disabled tests (excludes enabled tests)",
    )
    return parser


def safe_main_wrapper(main_func):
    """Decorator to wrap main function with standard exception handling

    Args:
        main_func: The main function to wrap

    Returns:
        Wrapped function with exception handling
    """
    def wrapper(*args, **kwargs):
        try:
            return main_func(*args, **kwargs)
        except (OSError, ValueError, RuntimeError, KeyboardInterrupt) as e:
            print(f"✗ FATAL ERROR: {e}")
            return 1
    return wrapper
