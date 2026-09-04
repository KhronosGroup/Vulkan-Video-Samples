"""
Video Test Dry Run Probe
Hardware capability probing via the applications' --dryRun mode.

Copyright 2026 Igalia S.L.

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
from pathlib import Path
from typing import Optional, Tuple

from tests.libs.video_test_platform_utils import PlatformUtils

# A dry run only initializes the device; it must never take as long as a test.
DRY_RUN_TIMEOUT = 60


def run_dry_run(cmd: Optional[list], *, unsupported_exit_code: int,
                cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
    """Run a dry-run command; report support plus the output it produced.

    The support verdict is True whenever it cannot be determined, so that a
    test is never skipped on the strength of a probe that failed to run.
    """
    if not cmd:
        return True, "", ""

    try:
        subprocess_kwargs = PlatformUtils.get_subprocess_kwargs()
        subprocess_kwargs['timeout'] = DRY_RUN_TIMEOUT
        if cwd is not None:
            subprocess_kwargs['cwd'] = str(cwd)
        result = subprocess.run(cmd, check=False, **subprocess_kwargs)
    except (OSError, subprocess.SubprocessError):
        return True, "", ""

    # A negative returncode means the probe died on a signal (SIGSEGV etc.),
    # so it determined nothing.
    supported = (result.returncode < 0
                 or result.returncode != unsupported_exit_code)
    return supported, result.stdout, result.stderr
