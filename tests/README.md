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
- `--include-disabled` - Include disabled tests in test suite
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
- **NOT_SUPPORTED** - Feature not supported by hardware/driver (exit code 77)
- **CRASH** - Application crashed (exit code ±6, SIGABRT)
- **ERROR** - Other failure conditions

### Test Naming Convention

Tests are automatically prefixed with their type:
- **Decoder tests** - Prefixed with `decode_` (e.g., `decode_h264_baseline_480p`)
- **Encoder tests** - Prefixed with `encode_` (e.g., `encode_h264_main_720p`)

This makes it easy to filter tests by type:
```bash
# Run only decoder tests
python3 video_test_framework_codec.py --test "decode_*"

# Run only H.264 encoder tests
python3 video_test_framework_codec.py --test "encode_h264_*"
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