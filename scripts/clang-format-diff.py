#!/usr/bin/env python3
#===- clang-format-diff.py - ClangFormat Diff Utility -------*- python -*--===#
#
# Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#
#===------------------------------------------------------------------------===#

"""
ClangFormat Diff Utility
v1.0

This script reads a unified diff from stdin and reformats all the changed
lines. This is useful to reformat all the lines touched by a specific patch.
Example usage for git users:

  git diff -U0 --no-color HEAD^ | clang-format-diff.py -p1 -i
  git diff -U0 --no-color -r HEAD~1 HEAD | clang-format-diff.py -p1 -i

It should be noted that the filename contained in the diff is used unmodified
to determine the source file to update. Users calling this script directly
should be careful to ensure that the path in the diff is correct relative to the
current working directory.
"""

import argparse
import difflib
import re
import subprocess
import sys
from io import StringIO


def main():
    parser = argparse.ArgumentParser(description=
                                     'Reformat changed lines in diff. Without -i '
                                     'option just output the diff that would be '
                                     'introduced.')
    parser.add_argument('-i', action='store_true', default=False,
                        help='apply edits to files instead of displaying a diff')
    parser.add_argument('-p', metavar='NUM', default=0,
                        help='strip the smallest prefix containing P slashes')
    parser.add_argument('-regex', metavar='PATTERN', default=None,
                        help='custom pattern selecting file paths to reformat '
                        '(case sensitive, overrides -iregex)')
    parser.add_argument('-iregex', metavar='PATTERN', default=
                        r'.*\.(cpp|cc|c\+\+|cxx|c|h|hpp|m|mm|js|ts)$',
                        help='custom pattern selecting file paths to reformat '
                        '(case insensitive, overridden by -regex)')
    parser.add_argument('-sort-includes', action='store_true', default=False,
                        help='let clang-format sort include statements')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='be more verbose, ineffective without -i')
    parser.add_argument('-style',
                        help='formatting style to apply (LLVM, Google, Chromium, '
                        'Mozilla, WebKit, file or JSON config)')
    parser.add_argument('-binary', default='clang-format',
                        help='location of binary to use for clang-format')
    args = parser.parse_args()

    try:
        p = int(args.p)
    except ValueError:
        print('error: invalid -p value')
        return 1

    if args.regex is not None:
        file_re = re.compile(args.regex)
    else:
        file_re = re.compile(args.iregex, re.IGNORECASE)

    changed_files = []
    lines_by_file = {}
    for line in sys.stdin:
        match = re.search(r'^\+\+\+\ (.*?/){%s}(\S*)' % p, line)
        if match:
            filename = match.group(2)
            if file_re.search(filename):
                changed_files.append(filename)

        match = re.search(r'^@@.*\+(\d+)(,(\d+))?', line)
        if match:
            start_line = int(match.group(1))
            line_count = 1
            if match.group(3):
                line_count = int(match.group(3))
            if line_count == 0:
                continue
            end_line = start_line + line_count - 1
            lines_by_file.setdefault(filename, []).extend(
                ['-lines', str(start_line) + ':' + str(end_line)])

    if not changed_files:
        return 0

    # Reformat files containing changes in place.
    for filename in changed_files:
        if args.i and args.verbose:
            print('Formatting', filename)
        command = [args.binary, filename]
        if args.i:
            command.append('-i')
        if args.style:
            command.extend(['-style', args.style])
        if args.sort_includes:
            command.append('-sort-includes')
        if filename in lines_by_file:
            command.extend(lines_by_file[filename])
        if not args.i:
            command.append('--output-replacements-xml')

        try:
            p = subprocess.Popen(command, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print("clang-format failed with return code", p.returncode)
                print(stderr.decode())
                return p.returncode

            if not args.i:
                print(stdout.decode('utf-8'), end='')

        except KeyboardInterrupt:
            # Ctrl-C, print a newline so the next shell prompt is on a new line.
            print('')
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())