import hashlib
import hmac
import os

# Instructors should override this via the DAFS_TEACH_SECRET environment
# variable. The fallback below is only a convenience default — since this
# repo is public, anyone can read it, so it gives no real protection against
# a student fabricating a code without completing the lesson.
_DEFAULT_SECRET = "dafs-teach-default-secret-change-me"


def _get_secret() -> str:
    return os.environ.get("DAFS_TEACH_SECRET", _DEFAULT_SECRET)


def using_default_secret() -> bool:
    return "DAFS_TEACH_SECRET" not in os.environ


def _normalize(student_name: str) -> str:
    return " ".join(student_name.strip().lower().split())


def generate_code(student_name: str, lesson_id: str, secret: str | None = None) -> str:
    """Deterministic completion code for a (student, lesson) pair.

    Same student name + lesson always yields the same code, so it can be
    shown to the student at any point after completion without needing to
    be stored anywhere.
    """
    secret = secret if secret is not None else _get_secret()
    message = f"{_normalize(student_name)}|{lesson_id}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest().upper()
    raw = digest[:10]
    return f"{raw[:5]}-{raw[5:]}"


def verify_code(student_name: str, lesson_id: str, code: str, secret: str | None = None) -> bool:
    expected = generate_code(student_name, lesson_id, secret=secret)
    submitted = code.strip().upper()
    return hmac.compare_digest(expected, submitted)
