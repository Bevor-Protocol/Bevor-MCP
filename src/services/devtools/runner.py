import os
import subprocess
from typing import Sequence, Mapping, Optional, Tuple


def run_command(
    command: Sequence[str],
    cwd: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout: Optional[int] = 900,
) -> Tuple[int, str, str]:
    """Run a command and return (code, stdout, stderr).

    Timeout defaults to 15 minutes to accommodate compilation and tests.
    """
    proc = subprocess.Popen(
        command,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return 124, out, f"Timeout after {timeout}s\n{err}"
    return proc.returncode, out, err


