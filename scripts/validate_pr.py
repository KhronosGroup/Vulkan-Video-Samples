#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate pull request title and body.

Usage:
  python3 validate_pr.py --title "scope: description" --body-file body.md
  python3 validate_pr.py --title "scope: description" --body "## Description ..."

Exits with code 1 and prints a human-readable error summary when
validation fails.
"""

import argparse
import re
import sys

TITLE_PATTERN = re.compile(
    r"^([a-z]+|[A-Z][a-zA-Z0-9]*(\{[^}]+\})?): .+"
)
FORBIDDEN_INDICATORS = re.compile(
    r"\b(wip|fixup|squash|tmp|todo|hack|xxx|do not merge|dnm|draft)\b",
    re.IGNORECASE,
)
HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")
SECTION_RE = re.compile(r"## {}\s*\n([\s\S]*?)(?=\n## |$)")
GPU_HEADER = re.compile(r"###\s+.+/.+/.+")

REQUIRED_TEST_FIELDS = [
    "Total Tests",
    "Passed",
    "Failed",
    "Success Rate",
]


def extract_section(body, name):
    """Return the content of a markdown ## section, stripped of HTML comments."""
    match = re.search(SECTION_RE.pattern.format(re.escape(name)), body)
    if not match:
        return ""
    return HTML_COMMENT.sub("", match.group(1)).strip()


def validate_title(title):
    """Validate the PR title and return a list of error strings."""
    errors = []

    if not TITLE_PATTERN.match(title):
        errors.append(
            "**Title** — must match pattern `scope: description`\n"
            "  - scope: lowercase (cmake, ci, docs) OR "
            "PascalCase (VkVideoDecoder, FindShaderc)\n"
            "  - Example: `cmake: fix build issue` or "
            "`VkVideoDecoder: add H265 support`\n"
            f"  - Got: `{title}`"
        )

    match = FORBIDDEN_INDICATORS.search(title)
    if match:
        errors.append(
            f"**Title** — must not contain draft indicators like `{match.group(0)}`\n"
            "  - Forbidden: WIP, fixup, squash, tmp, todo, hack, "
            "xxx, do not merge, dnm, draft"
        )

    if len(title) > 100:
        errors.append(
            f"**Title** — must not exceed 100 characters (currently {len(title)})."
        )

    if title.endswith("."):
        errors.append("**Title** — must not end with a period.")

    return errors


def validate_body(body):
    """Validate the PR body sections and return a list of error strings."""
    errors = []

    # --- Description (required) ---
    if not extract_section(body, "Description"):
        errors.append("**Description** — please describe your changes.")

    # --- Type of change (required) ---
    if not extract_section(body, "Type of change"):
        errors.append(
            "**Type of change** — please specify: "
            "bug fix / feature / refactor / docs / cleanup."
        )

    # --- Tests (required) ---
    tests_content = extract_section(body, "Tests")
    if not tests_content:
        errors.append("**Tests** — please provide your test results.")
    else:
        missing = [
            field
            for field in REQUIRED_TEST_FIELDS
            if not re.search(rf"{field}\s*:\s*\S+", tests_content, re.IGNORECASE)
        ]
        if missing:
            errors.append(
                f"**Tests** — missing or empty fields: {', '.join(missing)}.\n"
                "  Expected format:\n"
                "  ```\n"
                "  Total Tests: 70\n"
                "  Passed: 48\n"
                "  Failed: 0\n"
                "  Success Rate: 100.0%\n"
                "  ```"
            )

        if not GPU_HEADER.search(tests_content):
            errors.append(
                "**Tests** — please include a header with GPU / Driver / OS.\n"
                "  Example: `### NVIDIA GeForce RTX 3050 Ti Laptop GPU "
                "/ NVIDIA 570.123.19 / Ubuntu 24.04.3 LTS`"
            )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate PR title and body")
    parser.add_argument("--title", required=True, help="Pull request title")
    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="Pull request body as a string")
    body_group.add_argument("--body-file", help="Path to a file containing the PR body")
    args = parser.parse_args()

    title = args.title
    if args.body_file:
        with open(args.body_file, encoding="utf-8") as f:
            body = f.read()
    else:
        body = args.body

    errors = validate_title(title) + validate_body(body)

    if errors:
        print("❌ PR validation failed. Please fix the following:\n")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    print("✅ PR title and body validation passed.")


if __name__ == "__main__":
    main()
