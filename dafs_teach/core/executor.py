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


# Generous, because the first import of pandas/matplotlib on a fresh (Windows)
# laptop can take well over 10 seconds while caches are built.
TIMEOUT_SECONDS = 30

# UTF-8 mode: on Windows, piped output otherwise uses the locale encoding
# (e.g. cp1252), and printing a character like "₂" crashes the student's code.
_CHILD_ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def _run_file(path: str, timeout: int = TIMEOUT_SECONDS) -> tuple[str, str, bool, bool]:
    """Run a Python file, return (stdout, stderr, crashed, timed_out).

    `crashed` is based on the exit code, not on stderr, so warnings (which also
    go to stderr) don't count as errors.
    """
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_CHILD_ENV,
            timeout=timeout,
        )
        return result.stdout, result.stderr, result.returncode != 0, False
    except subprocess.TimeoutExpired:
        return "", "", False, True


def run_code(student_code: str, tests: List) -> RunResult:
    # Write student code to a temp file to avoid shell argument length limits
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(student_code)
        student_path = f.name

    try:
        stdout, stderr, crashed, timed_out = _run_file(student_path)
    finally:
        os.unlink(student_path)

    if timed_out:
        return RunResult("", "", True, False, f"Your code timed out after {TIMEOUT_SECONDS} seconds. Check for infinite loops.")

    if crashed and not stdout:
        # Pure error — no output at all
        return RunResult(stdout, stderr, False, False, f"Your code raised an error:\n\n```\n{stderr.strip()}\n```")

    # Run tests
    for idx, test in enumerate(tests):
        t_type = test.type
        if t_type in ("output_contains", "output_equals") and not stdout.strip():
            # Common beginner mistake (especially coming from Jupyter, which shows
            # the last line automatically): computing a value without printing it.
            return RunResult(
                stdout, stderr, False, False,
                "Your code ran, but didn't print anything. Did you forget to put "
                "`print( )` around the value you want to show?",
                failed_test_idx=idx,
            )
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
                a_out, a_err, a_crashed, a_timeout = _run_file(assert_path)
            finally:
                os.unlink(assert_path)

            if a_timeout:
                return RunResult(stdout, stderr, True, False, "Timed out while running checks.", failed_test_idx=idx)
            if a_crashed:
                desc = test.description or test.code
                # Only show the last line (e.g. "AssertionError: <message>"): the
                # full traceback quotes the check's source, which can leak the answer.
                last_line = a_err.strip().splitlines()[-1]
                return RunResult(
                    stdout, stderr, False, False,
                    f"Check failed: **{desc}**\n\n```\n{last_line}\n```",
                    failed_test_idx=idx,
                )

    return RunResult(stdout, stderr, False, True, "All checks passed!")
