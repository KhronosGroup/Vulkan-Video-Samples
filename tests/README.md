# Vulkan Video Test Framework

This directory contains a comprehensive testing framework for Vulkan Video codec implementations, supporting both encoding and decoding operations across H.264, H.265, AV1, and VP9 codecs.

## Framework Components

### Core Scripts

- **`video_test_framework_codec.py`** - Unified test orchestrator that runs both encoder and decoder tests
- **`video_test_framework_encode.py`** - Encoder-specific test runner
- **`video_test_framework_decode.py`** - Decoder-specific test runner


### Configuration Files

- **`encode_samples.json`** - Encoder test definitions with YUV input files
- **`decode_samples.json`** - Decoder test definitions with codec samples
- **`skipped_samples.json`** - Test skip list with conditions for skipping tests

### Decode Samples Format

The `decode_samples.json` file defines decoder test cases:

```json
{
  "samples": [
    {
      "name": "h264_4k_main",
      "codec": "h264",
      "description": "Test H.264 decoding with 4K main profile sample",
      "expected_output_md5": "716a1a1999bd67ed129b07c749351859",
      "source_url": "https://storage.googleapis.com/vulkan-video-samples/avc/4k_26_ibp_main.h264",
      "source_checksum": "1b6c2fa6ea7cb8fac8064036d8729f668e913ea7cf3860009924789b8edf042f",
      "source_filepath": "video/avc/4k_26_ibp_main.h264"
    }
  ]
}
```

#### Decode Sample Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique test identifier (used with `--test` option) |
| `codec` | Yes | Codec type: `h264`, `h265`, `av1`, `vp9` |
| `description` | No | Human-readable test description |
| `expected_output_md5` | No | MD5 hash of expected decoded YUV output for verification |
| `source_url` | Yes | URL to download the test sample |
| `source_checksum` | Yes | SHA256 checksum of the source file |
| `source_filepath` | Yes | Relative path where the file is stored in `resources/` |

### Encode Samples Format

The `encode_samples.json` file defines encoder test cases:

```json
{
  "samples": [
    {
      "name": "h264_main_profile",
      "codec": "h264",
      "profile": "main",
      "extra_args": null,
      "description": "Test H.264 Main profile encoding",
      "width": 352,
      "height": 288,
      "source_url": "https://storage.googleapis.com/vulkan-video-samples/yuv/352x288_15_i420.yuv",
      "source_checksum": "6e0e1a026717237f9546dfbd29d5e2ebbad0a993cdab38921bb43291a464ccd4",
      "source_filepath": "video/yuv/352x288_15_i420.yuv"
    }
  ]
}
```

#### Encode Sample Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique test identifier (used with `--test` option) |
| `codec` | Yes | Codec type: `h264`, `h265`, `av1` |
| `profile` | No | Encoding profile (e.g., `baseline`, `main`, `high`, `high444`, `main10`) |
| `extra_args` | No | Array of extra command-line arguments for the encoder |
| `description` | No | Human-readable test description |
| `width` | Yes | Input video width in pixels |
| `height` | Yes | Input video height in pixels |
| `source_url` | Yes | URL to download the YUV input file |
| `source_checksum` | Yes | SHA256 checksum of the source file |
| `source_filepath` | Yes | Relative path where the file is stored in `resources/` |

#### Extra Arguments Example

```json
{
  "name": "h264_cbr_ratecontrol",
  "codec": "h264",
  "profile": "high",
  "extra_args": [
    "--rateControlMode", "cbr",
    "--averageBitrate", "2000000"
  ],
  "description": "Test H.264 CBR rate control",
  "width": 352,
  "height": 288,
  "source_url": "...",
  "source_checksum": "...",
  "source_filepath": "video/yuv/352x288_15_i420.yuv"
}
```

### Test Skip List

The framework uses a skip list system to skip tests that are known to fail on specific platforms or GPU drivers. By default, tests listed in `skipped_samples.json` are skipped.

#### Skip List Format

```json
{
  "version": "1.0",
  "description": "Test skip list for Vulkan Video Samples test framework",
  "skipped_tests": [
    {
      "name": "av1_basic_10bit",
      "type": "decode",
      "format": "vvs",
      "drivers": ["all"],
      "platforms": ["all"],
      "reproduction": "always",
      "reason": "10-bit AV1 decoding not yet supported",
      "bug_url": "",
      "date_added": "2025-01-27"
    }
  ]
}
```

#### Skip List Fields

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `name` | Yes | test name or pattern | Supports wildcards (e.g., `av1_*_10bit`) |
| `type` | Yes | `decode`, `encode` | Test type (decoder or encoder test) |
| `format` | Yes | `vvs`, `fluster`, `soothe` | Test suite format |
| `drivers` | Yes | array | GPU drivers to skip: `all`, `nvidia`, `nvk`, `intel`, `anv`, `amd`, `radv` |
| `platforms` | Yes | array | OS platforms: `all`, `windows`, `linux` (defined but not enforced) |
| `reproduction` | Yes | `always`, `flaky` | Whether failure is consistent |
| `reason` | No | free text | Human-readable explanation |
| `bug_url` | No | URL | Link to tracking issue |
| `date_added` | No | YYYY-MM-DD | When the skip entry was added |

#### Driver Values

- `nvidia` - NVIDIA proprietary driver
- `nvk` - NVK (open-source NVIDIA via Mesa)
- `intel` - Intel proprietary/legacy driver
- `anv` - ANV (Intel Vulkan via Mesa)
- `amd` - AMD proprietary (AMDGPU-PRO)
- `radv` - RADV (AMD Vulkan via Mesa)
- `all` - Matches any driver

#### Skip List Examples

```bash
# Run tests ignoring the skip list (run all tests)
python3 video_test_framework_codec.py --ignore-skip-list

# Run only skipped tests (useful for testing fixes)
python3 video_test_framework_codec.py --only-skipped

# Use a custom skip list
python3 video_test_framework_codec.py --skip-list my_skip_list.json
```


### Usage Examples

#### Run All Tests
```bash
python3 video_test_framework_codec.py
```

#### Run Encoder Tests Only
```bash
python3 video_test_framework_codec.py --encoder-only --codec h264
```

#### Run Specific Test Pattern
```bash
python3 video_test_framework_codec.py --test "*baseline*" --verbose
```

#### Export Results to JSON
```bash
python3 video_test_framework_codec.py --export-json results.json
```

### Command Line Options

- `--encoder PATH` - Path to vk-video-enc-test executable
- `--decoder PATH` - Path to vk-video-dec-test executable
- `--codec {h264,h265,av1,vp9}` - Filter by specific codec
- `--test PATTERN` - Filter by test name pattern (supports wildcards)
- `--list-samples` - List all available test samples and exit
- `--encoder-only` - Run only encoder tests
- `--decoder-only` - Run only decoder tests
- `--skip-list FILE` - Path to custom skip list JSON file (default: skipped_samples.json)
- `--ignore-skip-list` - Ignore the skip list and run all tests
- `--only-skipped` - Run only skipped tests
- `--show-skipped` - Show skipped tests in summary output
- `--no-auto-download` - Skip automatic download of missing/corrupt sample files
- `--export-json FILE` - Export results to JSON file
- `--keep-files` - Keep output artifacts (decoded/encoded files) for debugging
- `--verbose` - Show detailed command execution
- `--display` - Enable display output for decoder tests (removes --noPresent flag)
- `--deviceID` - Vulkan device ID to use for testing (decimal or hex with 0x prefix)
- `--no-verify-md5` - Disable MD5 verification of decoded output
- `--decode-test-suite FILE` - Path to custom decode test suite JSON file
- `--encode-test-suite FILE` - Path to custom encode test suite JSON file

### Test Status Types

- **SUCCESS** - Test passed successfully
- **NOT_SUPPORTED** - Feature not supported by hardware/driver (exit code 69, EX_UNAVAILABLE)
- **CRASH** - Application crashed (exit code ±6, SIGABRT)
- **ERROR** - Other failure conditions

### Test Naming Convention

Tests are automatically prefixed with their type for display:
- **Decoder tests** - Prefixed with `decode_` (e.g., `decode_h264_4k_main`)
- **Encoder tests** - Prefixed with `encode_` (e.g., `encode_h264_main_profile`)

When filtering tests with `--test`, you can use either the base name or the prefixed name:
```bash
# These are equivalent - run a specific test by base name or full name
python3 video_test_framework_codec.py --test "h264_4k_main"
python3 video_test_framework_codec.py --test "decode_h264_4k_main"

# Run only decoder tests (using prefix)
python3 video_test_framework_codec.py --test "decode_*"

# Run only H.264 encoder tests
python3 video_test_framework_codec.py --test "encode_h264_*"

# Run all AV1 tests (both encode and decode)
python3 video_test_framework_codec.py --test "av1_*"
```

### Asset Management

The framework automatically downloads required test assets. Assets are cached in the `resources/` directory and verified by SHA256 checksums. Use `--no-auto-download` to disable this behavior.

### Fluster Test Suite Compatibility

The framework supports [Fluster](https://github.com/fluendo/fluster) test suite format for decoder tests. When a Fluster JSON file is provided via `--decode-test-suite`, the framework will:

- Automatically detect the Fluster format (presence of `test_vectors` field)
- Download and extract zip archives containing test vectors
- Convert test vectors to internal format with proper MD5 verification
- Extract files to `resources/fluster/{codec}/{suite_name}/`
- Cache extracted files to avoid re-downloading

Example usage:
```bash
# Use Fluster JVT-AVC_V1 test suite
python3 video_test_framework_decode.py --decode-test-suite path/to/JVT-AVC_V1.json

# Filter specific tests from Fluster suite
python3 video_test_framework_decode.py --decode-test-suite JVT-AVC_V1.json --test "*baseline*"
```

**Note**: Fluster format is only supported for decode tests, not encode tests.

### MD5 Verification

For decoder tests, the framework can verify the correctness of decoded output by comparing MD5 hashes:

- When `expected_output_md5` is specified in `decode_samples.json`, the decoder will validate that output raw YUV data has the md5 value.
- If hashes don't match, the test is marked as **ERROR** (failed)
- Use `--no-verify-md5` to disable MD5 verification
- MD5 values can be generated using: `ffmpeg -i input.h264 -f md5 -`

### Results Format

JSON export includes:
- Test summary with counts by status type
- Individual test results with timing and status information
- Support for both encoder and decoder test results in unified format

### Individual Framework Usage

Each component can be run independently:

```bash
# List available samples
python3 video_test_framework_codec.py --list-samples
python3 video_test_framework_encode.py --list-samples
python3 video_test_framework_decode.py --list-samples

# Encoder tests only
python3 video_test_framework_encode.py

# Decoder tests only
python3 video_test_framework_decode.py --display
```