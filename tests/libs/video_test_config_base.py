"""
Base classes for Vulkan Video Test Framework
Provides common data structures and enums shared between encoder and
decoder frameworks.

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

import json
import sys
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from tests.libs.video_test_fetch_sample import FetchableResource, SampleFetcher
from tests.libs.video_test_utils import verify_file_checksum


class CodecType(Enum):
    """Enumeration of supported video codecs"""
    H264 = "h264"
    H265 = "h265"
    AV1 = "av1"
    VP9 = "vp9"


class TestFilter(Enum):
    """Enumeration for filtering enabled/disabled tests"""
    ENABLED = "enabled"      # Only enabled tests
    DISABLED = "disabled"    # Only disabled tests
    ALL = "all"              # Both enabled and disabled tests

class TestStatus(Enum):
    """Enumeration of test execution statuses"""
    SUCCESS = "success"
    NOT_SUPPORTED = "not_supported"
    ERROR = "error"
    CRASH = "crash"

@dataclass
class BaseTestConfig:  # pylint: disable=too-many-instance-attributes
    """Base configuration for a test case"""
    name: str
    codec: CodecType
    expect_success: bool = True
    extra_args: Optional[List[str]] = None
    description: str = ""
    timeout: Optional[int] = None
    source_url: str = ""
    source_checksum: str = ""
    source_filepath: str = ""
    enabled: bool = True


@dataclass(init=False)
class TestResult:
    """Result of a single test execution with compact attribute set.

    Maintains backward-compatible properties (stdout, stderr, etc.) while
    storing ancillary data in a single 'meta' mapping to keep attribute count
    modest.
    """
    config: BaseTestConfig
    returncode: int
    execution_time: float
    status: TestStatus
    meta: Dict[str, Any]

    def __init__(
        self,
        config: BaseTestConfig,
        returncode: int,
        execution_time: float,
        status: TestStatus,
        **kwargs: Any,
    ) -> None:
        self.config = config
        self.returncode = returncode
        self.execution_time = execution_time
        self.status = status
        self.meta = {
            "stdout": kwargs.get("stdout", ""),
            "stderr": kwargs.get("stderr", ""),
            "warning_found": bool(kwargs.get("warning_found", False)),
            "error_message": kwargs.get("error_message", ""),
            "command_line": kwargs.get("command_line", ""),
        }

    @property
    def success(self) -> bool:
        """Backward compatibility property"""
        return self.status == TestStatus.SUCCESS

    # Backward-compatible attributes via properties
    @property
    def stdout(self) -> str:
        """Captured standard output from the test run."""
        return self.meta.get("stdout", "")

    @stdout.setter
    def stdout(self, value: str) -> None:
        """Set captured standard output for this result."""
        self.meta["stdout"] = value

    @property
    def stderr(self) -> str:
        """Captured standard error from the test run."""
        return self.meta.get("stderr", "")

    @stderr.setter
    def stderr(self, value: str) -> None:
        """Set captured standard error for this result."""
        self.meta["stderr"] = value

    @property
    def warning_found(self) -> bool:
        """Whether any warning was detected in the output."""
        return bool(self.meta.get("warning_found", False))

    @warning_found.setter
    def warning_found(self, value: bool) -> None:
        """Set the warning flag for this result."""
        self.meta["warning_found"] = bool(value)

    @property
    def error_message(self) -> str:
        """Optional error message describing a failure."""
        return self.meta.get("error_message", "")

    @error_message.setter
    def error_message(self, value: str) -> None:
        """Set the error message for this result."""
        self.meta["error_message"] = value

    @property
    def command_line(self) -> str:
        """The command line used to invoke the test binary."""
        return self.meta.get("command_line", "")

    @command_line.setter
    def command_line(self, value: str) -> None:
        """Set the command line recorded for this result."""
        self.meta["command_line"] = value


def create_error_result(config: BaseTestConfig, error_message: str,
                        command_line: str = "") -> TestResult:
    """Create a TestResult for an error condition

    Args:
        config: Test configuration
        error_message: Error message to include
        command_line: Optional command line that failed

    Returns:
        TestResult with ERROR status
    """
    return TestResult(
        config=config,
        returncode=-1,
        stdout="",
        stderr="",
        execution_time=0,
        status=TestStatus.ERROR,
        error_message=error_message,
        command_line=command_line
    )


def check_sample_resources(samples, sample_type: str = "resource",
                           auto_download: bool = True) -> bool:
    """
    Check if required sample files are available and have correct checksums

    Args:
        samples: List of samples with exists(), full_path, checksum,
                 and to_fetchable_resource() methods
        sample_type: Type description for error messages
        auto_download: Whether to automatically download missing/corrupt files

    Returns:
        True if all samples are valid, False otherwise
    """
    missing_files = set()
    corrupt_files = set()

    for sample in samples:
        if not sample.exists():
            missing_files.add(str(sample.full_path))
        elif hasattr(sample, 'checksum') and sample.checksum:
            # Verify checksum if available
            if not verify_file_checksum(sample.full_path, sample.checksum):
                corrupt_files.add(str(sample.full_path))

    if missing_files or corrupt_files:
        if missing_files:
            print(f"⚠️  Missing {sample_type} files:")
            for file in missing_files:
                print(f"    {file}")

        if corrupt_files:
            print(f"⚠️  Corrupt {sample_type} files (checksum mismatch):")
            for file in corrupt_files:
                print(f"    {file}")

        if auto_download:
            print(f"📥 Attempting to download {sample_type} files...")
            return download_sample_assets(samples, sample_type)

        print("Missing test resources - automatic download is disabled")
        return False

    print(f"✓ All {sample_type} files found and verified")
    return True


def download_sample_assets(samples, asset_type: str = "test") -> bool:
    """
    Download sample assets using integrated fetch system

    Args:
        samples: List of samples with to_fetchable_resource() method
        asset_type: Type description for messages

    Returns:
        True if download successful, False otherwise
    """
    print(f"📥 Downloading {asset_type} assets...")

    # Convert samples to fetchable resources (skip samples with no URL)
    fetchable_resources = []
    for sample in samples:
        # Check if sample has URL directly or via to_fetchable_resource()
        has_url = False
        if hasattr(sample, 'url') and sample.url:
            has_url = True
        elif hasattr(sample, 'download_url') and sample.download_url:
            has_url = True
        elif hasattr(sample, 'to_fetchable_resource'):
            # For adapter classes, check the fetchable resource
            try:
                resource = sample.to_fetchable_resource()
                if hasattr(resource, 'url') and resource.url:
                    has_url = True
            except (AttributeError, TypeError):
                pass

        if has_url:
            fetchable_resources.append(sample.to_fetchable_resource())

    if not fetchable_resources:
        print(f"✓ No {asset_type} assets to download")
        return True

    fetcher = SampleFetcher(fetchable_resources)

    try:
        success = fetcher.fetch_all()
        if success:
            print(f"✓ Downloaded {asset_type} samples")
            return True

        print(f"✗ Failed to download some {asset_type} samples")
        return False
    except (OSError, ValueError, RuntimeError) as e:
        print(f"✗ Error downloading {asset_type} samples: {e}")
        return False


def extract_and_verify_zip(zip_url: str, zip_md5: str,
                           extract_dir: Path) -> bool:
    """
    Download, verify, and extract a zip file from Fluster test suite

    Args:
        zip_url: URL of the zip file to download
        zip_md5: Expected MD5 checksum of the zip file
        extract_dir: Directory to extract files into

    Returns:
        True if successful, False otherwise
    """
    # Create extract directory
    extract_dir.mkdir(parents=True, exist_ok=True)

    # Determine zip filename from URL
    zip_filename = zip_url.split('/')[-1]
    zip_path = extract_dir / zip_filename

    # Check if already extracted (per-zip marker)
    zip_basename = zip_filename.rsplit('.', 1)[0]  # Remove .zip extension
    extracted_marker = extract_dir / f".extracted_{zip_basename}"
    if extracted_marker.exists():
        return True

    # Download zip file if not present
    if not zip_path.exists():
        print(f"  Downloading {zip_filename}...")
        # Use FetchableResource to download with MD5 verification
        resource = FetchableResource(
            url=zip_url,
            filename=zip_filename,
            checksum=zip_md5,
            base_dir=str(extract_dir),
            checksum_algorithm='md5'
        )
        if not resource.update(insecure=False):
            return False

    # Extract zip
    print(f"  Extracting {zip_filename}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Create marker file to avoid re-extraction
        extracted_marker.touch()

        # Remove zip file after successful extraction
        zip_path.unlink()

        return True
    except (zipfile.BadZipFile, OSError) as e:
        print(f"  ✗ Failed to extract {zip_filename}: {e}")
        return False


def _extract_fluster_zips(test_vectors: List[Dict],
                          extract_base: Path) -> None:
    """Extract zip files for Fluster test vectors"""
    # Group test vectors by source URL (many tests share the same zip file)
    sources = {}
    for test_vector in test_vectors:
        source_url = test_vector.get('source')
        if source_url and source_url not in sources:
            sources[source_url] = test_vector.get('source_checksum')

    # Extract zip files (only files with .zip extension)
    for source_url, checksum in sources.items():
        if source_url.lower().endswith('.zip'):
            if not extract_and_verify_zip(source_url, checksum, extract_base):
                print(f"⚠️  Skipping tests from {source_url}")
        else:
            # Non-zip files should be downloaded directly
            # They will be handled by the normal resource download system
            pass


def _create_fluster_sample(test_vector: Dict, suite_name: str,
                           internal_codec: str) -> Optional[Dict[str, Any]]:
    """Create a sample dictionary from a Fluster test vector"""
    name = test_vector.get('name')
    source_url = test_vector.get('source')
    source_checksum = test_vector.get('source_checksum', '')
    input_file = test_vector.get('input_file')
    result_md5 = test_vector.get('result', '')

    if not all([name, source_url, input_file]):
        return None

    relative_path = f"fluster/{internal_codec}/{suite_name}/{input_file}"

    # For zip files: files are extracted during load, no URL/checksum needed
    # For non-zip files: URL points directly, use MD5 checksum with md5: prefix
    if source_url.lower().endswith('.zip'):
        url = ''  # No URL - file was extracted from zip
        checksum = ''  # No checksum needed
    else:
        url = source_url  # Direct download URL
        # Prefix with md5: to indicate MD5 algorithm
        checksum = f"md5:{source_checksum}" if source_checksum else ''

    return {
        'name': f"{suite_name.lower()}_{name.lower()}",
        'codec': internal_codec,
        'source_filepath': relative_path,
        'source_checksum': checksum,
        'source_url': url,
        'description': f"Fluster {suite_name} test: {name}",
        'enabled': True,
        'expected_output_md5': result_md5,
    }


def convert_fluster_to_internal_format(
        fluster_data: Dict[str, Any],
        auto_extract: bool = True
) -> List[Dict[str, Any]]:
    """
    Convert Fluster test suite format to internal format

    Args:
        fluster_data: Parsed Fluster JSON data
        auto_extract: Whether to automatically extract zip files

    Returns:
        List of samples in internal format
    """
    suite_name = fluster_data.get('name', 'unknown')
    codec_name = fluster_data.get('codec', 'unknown')

    # Map Fluster codec names to internal codec names
    codec_map = {'H.264': 'h264', 'H.265': 'h265', 'AV1': 'av1', 'VP9': 'vp9'}
    internal_codec = codec_map.get(codec_name, codec_name.lower())

    # Determine extraction directory
    resources_dir = Path(__file__).parent.parent / "resources"
    extract_base = resources_dir / "fluster" / internal_codec / suite_name

    # Extract zip files if auto_extract is enabled
    test_vectors = fluster_data.get('test_vectors', [])
    if auto_extract:
        _extract_fluster_zips(test_vectors, extract_base)

    # Create sample entries
    samples = []
    for test_vector in test_vectors:
        sample = _create_fluster_sample(test_vector, suite_name,
                                        internal_codec)
        if sample:
            samples.append(sample)

    return samples


def convert_soothe_to_internal_format(
        soothe_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Convert Soothe asset catalog format to internal encoder test format

    Args:
        soothe_data: Parsed Soothe JSON data

    Returns:
        List of encoder test samples in internal format
    """
    catalog_name = soothe_data.get('name', 'unknown')
    # Sanitize catalog name for use as directory name
    catalog_name = catalog_name.replace('.', '_').replace(' ', '_').lower()

    assets = soothe_data.get('assets', [])

    samples = []
    for asset in assets:
        asset_name = asset.get('name')
        source_url = asset.get('source')
        checksum = asset.get('checksum')  # MD5
        filename = asset.get('filename')

        if not all([asset_name, source_url, filename]):
            continue

        # Relative path within resources directory
        relative_path = f"soothe/{catalog_name}/{filename}"

        # Generate tests for each codec with default settings
        for codec in ['h264', 'h265', 'av1']:
            samples.append({
                'name': f"{asset_name}_{codec}",
                'codec': codec,
                'profile': None,
                'extra_args': None,
                'description': (
                    f"Encode {asset_name} using {codec.upper()} "
                    f"(Soothe: {soothe_data.get('name', 'unknown')})"
                ),
                'enabled': True,
                'source_url': source_url,
                'source_filepath': relative_path,
                'source_checksum': f"md5:{checksum}" if checksum else '',
                'source_format': 'y4m',
                'width': 0,  # Not needed for Y4M - read from header
                'height': 0,
            })

    return samples


def load_samples_from_json(json_file: str,
                           test_type: str = "decode") -> List[Dict[str, Any]]:
    """
    Load sample definitions from JSON file.
    Supports internal format, Fluster test suite format, and Soothe asset
    catalog format.

    Args:
        json_file: Path to JSON file containing sample definitions
        test_type: Type of test ("decode" or "encode")

    Returns:
        List of sample dictionaries
    """
    try:
        # Handle absolute paths and paths relative to cwd
        json_path = Path(json_file)
        if not json_path.is_absolute():
            # If it's not absolute, first check if it exists relative to cwd
            if not json_path.exists():
                # If not, try relative to tests directory (parent of libs/)
                json_path = Path(__file__).parent.parent / json_file

        if not json_path.exists():
            raise FileNotFoundError(
                f"Test suite file not found: {json_path}"
            )

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Detect format and convert if necessary
        if 'test_vectors' in data:
            # Fluster format - only supported for decode tests
            if test_type == "encode":
                print("✗ Error: Fluster test suite format is only supported "
                      "for decode tests, not encode tests")
                sys.exit(1)
            print(f"📦 Detected Fluster test suite format: {data.get('name')}")
            return convert_fluster_to_internal_format(data)

        if 'assets' in data:
            # Soothe format - only supported for encode tests
            if test_type == "decode":
                print("✗ Error: Soothe asset catalog format is only supported "
                      "for encode tests, not decode tests")
                sys.exit(1)
            print(f"📦 Detected Soothe asset catalog: {data.get('name')}")
            return convert_soothe_to_internal_format(data)

        # Internal format
        if 'samples' in data:
            return data['samples']

        # Unrecognized format
        print(f"✗ Error: Unrecognized test suite format in {json_file}")
        print("   Expected 'samples' (internal format), 'test_vectors' "
              "(Fluster), or 'assets' (Soothe)")
        sys.exit(1)
    except (OSError, IOError, json.JSONDecodeError) as e:
        print(f"✗ Failed to load samples from {json_file}: {e}")
        raise
