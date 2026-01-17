#!/usr/bin/env python3

# Copyright (c) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Script to determine if source code in Pull Request is properly formatted.
# Exits with non 0 exit code if formatting is needed.
#
# This script assumes to be invoked at the project root directory.

import subprocess
import sys
import os
import re

# Color codes for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    NC = '\033[0m'  # No Color

def run_command(cmd, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output,
                              text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return 1, "", str(e)

def get_files_to_check():
    """Get list of C/C++ files to check formatting for."""
    # Get files changed compared to master
    returncode, stdout, stderr = run_command("git diff --name-only master")
    if returncode != 0:
        print(f"Error getting git diff: {stderr}")
        return []

    files = stdout.strip().split('\n') if stdout.strip() else []

    # Filter for C/C++ files, excluding vulkan headers
    cpp_extensions = re.compile(r'.*\.(cpp|cc|c\+\+|cxx|c|h|hpp)$')
    vulkan_include = re.compile(r'^include/vulkan')

    filtered_files = []
    for file in files:
        if file and cpp_extensions.match(file) and not vulkan_include.match(file):
            filtered_files.append(file)

    return filtered_files

def check_formatting(files):
    """Check formatting of specified files using clang-format-diff.py."""
    if not files:
        return True, ""

    files_str = ' '.join(files)
    cmd = f"git diff -U0 master -- {files_str} | python ./scripts/clang-format-diff.py -p1 -style=file"

    returncode, stdout, stderr = run_command(cmd)
    if returncode != 0:
        print(f"Error running clang-format-diff: {stderr}")
        return False, stderr

    return stdout.strip() == "", stdout

def main():
    """Main function to check code formatting."""
    # Change to script directory's parent (project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)

    files_to_check = get_files_to_check()

    if not files_to_check:
        print(f"{Colors.GREEN}No source code to check for formatting.{Colors.NC}")
        return 0

    print(f"Checking formatting for files: {', '.join(files_to_check)}")

    is_formatted, format_output = check_formatting(files_to_check)

    if is_formatted:
        print(f"{Colors.GREEN}All source code in PR properly formatted.{Colors.NC}")
        return 0
    else:
        print(f"{Colors.RED}Found formatting errors!{Colors.NC}")
        print(format_output)
        return 1

if __name__ == "__main__":
    sys.exit(main())