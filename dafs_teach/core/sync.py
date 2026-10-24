import json
import os
import urllib.request
from datetime import datetime
from urllib.error import HTTPError, URLError


def _get_sync_url() -> str | None:
    return os.environ.get("DAFS_TEACH_SYNC_URL") or None


def sync_enabled() -> bool:
    return _get_sync_url() is not None


def send_anonymous_report(deadline_id: str, rows: list[dict], lesson_titles: dict[str, str], timeout: int = 8) -> tuple[bool, str]:
    """POST an anonymous progress summary for one deadline's lessons.

    No student name or other identifier is included — only per-exercise
    completed/attempts/solution_views counts, tagged with which deadline
    and lesson they belong to.
    """
    url = _get_sync_url()
    if url is None:
        return False, "No sync URL configured (DAFS_TEACH_SYNC_URL not set)."

    payload = {
        "deadline_id": deadline_id,
        "rows": [
            {**row, "lesson_title": lesson_titles.get(row["lesson_id"], row["lesson_id"])}
            for row in rows
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read()
        return True, f"Sent an anonymous progress summary for '{deadline_id}' to your instructor ({len(rows)} exercise records, no names included)."
    except HTTPError as e:
        return False, f"Instructor endpoint rejected the report (HTTP {e.code})."
    except URLError as e:
        return False, f"Could not reach the instructor endpoint: {e.reason}"
    except Exception as e:
        return False, f"Report failed: {e}"


def check_and_send_due_deadlines(tracker, deadlines: list, lesson_titles: dict[str, str]) -> list[tuple[str, str]]:
    """Check every configured deadline; send + mark any that are past due and not yet sent.

    Returns a list of (level, message) notices — level is "success" or
    "error" — for the caller to display. Safe to call on every app launch:
    already-sent deadlines are skipped, and a failed send is left unmarked
    so it's retried on the next launch.
    """
    if not sync_enabled() or not deadlines:
        return []

    notices: list[tuple[str, str]] = []
    now = datetime.now()
    for dl in deadlines:
        if now < dl.deadline:
            continue
        if tracker.has_sent_deadline(dl.id):
            continue

        all_rows = tracker.get_all_rows_any_student()
        rows = [r for r in all_rows if r["lesson_id"] in dl.lessons]

        if not rows:
            # Nothing done for this deadline's lessons — nothing meaningful to
            # report, and no point retrying forever once it's passed.
            tracker.mark_deadline_sent(dl.id)
            continue

        ok, message = send_anonymous_report(dl.id, rows, lesson_titles)
        if ok:
            tracker.mark_deadline_sent(dl.id)
            notices.append(("success", message))
        else:
            notices.append(("error", f"Deadline '{dl.id}' passed but the report couldn't be sent yet: {message}"))
    return notices
