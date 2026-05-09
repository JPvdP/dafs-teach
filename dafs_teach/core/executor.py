import os
import sys
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List


@dataclass
class RunResult:
    stdout: str
    stderr: str
    timed_out: bool
    passed: bool
    feedback: str
    failed_test_idx: int = -1  # index of the first failing test, -1 if all pass


def _run_file(path: str, timeout: int = 10) -> tuple[str, str, bool]:
    """Run a Python file, return (stdout, stderr, timed_out)."""
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout, result.stderr, False
    except subprocess.TimeoutExpired:
        return "", "", True


def run_code(student_code: str, tests: List) -> RunResult:
    # Write student code to a temp file to avoid shell argument length limits
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(student_code)
        student_path = f.name

    try:
        stdout, stderr, timed_out = _run_file(student_path)
    finally:
        os.unlink(student_path)

    if timed_out:
        return RunResult("", "", True, False, "Your code timed out after 10 seconds. Check for infinite loops.")

    if stderr and not stdout:
        # Pure error — no output at all
        return RunResult(stdout, stderr, False, False, f"Your code raised an error:\n\n```\n{stderr.strip()}\n```")

    # Run tests
    for idx, test in enumerate(tests):
        t_type = test.type
        if t_type == "output_contains":
            if test.value not in stdout:
                return RunResult(
                    stdout, stderr, False, False,
                    f"Expected the output to contain **`{test.value}`**, but it didn't.\n\nYour output:\n```\n{stdout.strip() or '(empty)'}\n```",
                    failed_test_idx=idx,
                )
        elif t_type == "output_equals":
            if stdout.strip() != test.value.strip():
                return RunResult(
                    stdout, stderr, False, False,
                    f"Expected output:\n```\n{test.value.strip()}\n```\nYour output:\n```\n{stdout.strip() or '(empty)'}\n```",
                    failed_test_idx=idx,
                )
        elif t_type == "assert":
            combined = student_code + "\n" + test.code
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(combined)
                assert_path = f.name
            try:
                a_out, a_err, a_timeout = _run_file(assert_path)
            finally:
                os.unlink(assert_path)

            if a_timeout:
                return RunResult(stdout, stderr, True, False, "Timed out while running checks.", failed_test_idx=idx)
            if a_err:
                desc = test.description or test.code
                return RunResult(
                    stdout, stderr, False, False,
                    f"Check failed: **{desc}**\n\n```\n{a_err.strip()}\n```",
                    failed_test_idx=idx,
                )

    return RunResult(stdout, stderr, False, True, "All checks passed!")
