"""
Video Test Framework Main Entry Points
Contains standalone main execution functions for test frameworks.

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
            skip_list=args.skip_list,
            ignore_skip_list=args.ignore_skip_list,
            only_skipped=args.only_skipped,
            show_skipped=args.show_skipped,
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
            skip_list=args.skip_list,
            ignore_skip_list=args.ignore_skip_list,
            only_skipped=args.only_skipped,
            show_skipped=args.show_skipped,
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
