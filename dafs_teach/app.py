from pathlib import Path

import streamlit as st

from dafs_teach.core.lesson_loader import load_lessons, Lesson, Exercise
from dafs_teach.core.executor import run_code
from dafs_teach.core.progress import ProgressTracker

# ── Configuration ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="DAFS Teaching App",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
DATA_DIR = Path.home() / ".dafs_teach"
DATA_DIR.mkdir(exist_ok=True)

# ── Load content & tracker (cached across reruns) ─────────────────────────────

@st.cache_resource
def get_lessons():
    return load_lessons(BASE_DIR / "content")

@st.cache_resource
def get_tracker():
    return ProgressTracker(DATA_DIR / "progress.db")

lessons = get_lessons()
lessons_by_id = {l.id: l for l in lessons}
tracker = get_tracker()

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Monospace code editor */
textarea[data-testid="stTextArea"] textarea {
    font-family: 'Courier New', Courier, monospace;
    font-size: 14px;
}
/* Tight sidebar nav items */
.sidebar-exercise-item { padding: 2px 0; }
</style>
""", unsafe_allow_html=True)

# ── Session state helpers ─────────────────────────────────────────────────────

def init_state():
    defaults = {
        "student_name": None,
        "current_lesson_id": None,
        "current_exercise_idx": 0,
        "last_result": None,
        "hints_shown": 0,
        "show_solution": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


def go_to_lesson(lesson_id: str, exercise_idx: int = 0):
    st.session_state.current_lesson_id = lesson_id
    st.session_state.current_exercise_idx = exercise_idx
    st.session_state.last_result = None
    st.session_state.hints_shown = 0
    st.session_state.show_solution = False


def go_to_exercise(idx: int):
    st.session_state.current_exercise_idx = idx
    st.session_state.last_result = None
    st.session_state.hints_shown = 0
    st.session_state.show_solution = False


def go_home():
    st.session_state.current_lesson_id = None
    st.session_state.last_result = None


def code_key(lesson_id: str, exercise_id: str) -> str:
    return f"code__{lesson_id}__{exercise_id}"


def get_code(lesson_id: str, exercise: Exercise) -> str:
    """Return saved code for this exercise, falling back to DB then starter code."""
    key = code_key(lesson_id, exercise.id)
    if key in st.session_state:
        return st.session_state[key]
    saved = tracker.get_last_code(st.session_state.student_name, lesson_id, exercise.id)
    return saved if saved else exercise.starter_code


# ── Name entry screen ────────────────────────────────────────────────────────

def render_name_entry():
    st.title("Welcome to DAFS Teaching App 🐍")
    st.markdown("Learn Python for data analysis — one exercise at a time.")
    st.divider()

    col, _ = st.columns([1, 2])
    with col:
        name = st.text_input("Enter your name to get started:", placeholder="e.g. Alice")
        if st.button("Start learning", type="primary", disabled=not name.strip()):
            st.session_state.student_name = name.strip()
            st.rerun()


# ── Lesson browser ────────────────────────────────────────────────────────────

def render_lesson_browser():
    st.title("Choose a Lesson")

    all_progress = tracker.get_all_progress(st.session_state.student_name)

    for lesson in lessons:
        completed = all_progress.get(lesson.id, {})
        n_done = sum(1 for ex in lesson.exercises if completed.get(ex.id, {}).get("completed"))
        n_total = len(lesson.exercises)
        pct = n_done / n_total if n_total else 0

        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(lesson.title)
                st.caption(lesson.description)
                st.progress(pct, text=f"{n_done}/{n_total} exercises completed")
            with c2:
                st.write("")
                st.write("")
                if st.button("Open", key=f"open_{lesson.id}", type="primary"):
                    # Jump to first incomplete exercise
                    first_incomplete = next(
                        (i for i, ex in enumerate(lesson.exercises)
                         if not completed.get(ex.id, {}).get("completed")),
                        0,
                    )
                    go_to_lesson(lesson.id, first_incomplete)
                    st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown(f"**Student:** {st.session_state.student_name}")
        if st.button("← Home", use_container_width=True):
            go_home()
            st.rerun()

        st.divider()

        if st.session_state.current_lesson_id:
            lesson = lessons_by_id[st.session_state.current_lesson_id]
            st.markdown(f"**{lesson.title}**")

            completed = tracker.get_completed(
                st.session_state.student_name, lesson.id
            )
            for i, ex in enumerate(lesson.exercises):
                icon = "✅" if ex.id in completed else ("▶️" if i == st.session_state.current_exercise_idx else "⭕")
                label = f"{icon} {ex.title}"
                if st.button(label, key=f"nav_{i}", use_container_width=True):
                    go_to_exercise(i)
                    st.rerun()
        else:
            st.markdown("**Lessons**")
            all_progress = tracker.get_all_progress(st.session_state.student_name)
            for lesson in lessons:
                completed = all_progress.get(lesson.id, {})
                n_done = sum(1 for ex in lesson.exercises if completed.get(ex.id, {}).get("completed"))
                n_total = len(lesson.exercises)
                icon = "✅" if n_done == n_total else "⭕"
                st.markdown(f"{icon} {lesson.title} ({n_done}/{n_total})")


# ── Exercise view ─────────────────────────────────────────────────────────────

def render_exercise():
    lesson = lessons_by_id[st.session_state.current_lesson_id]
    idx = st.session_state.current_exercise_idx
    exercise = lesson.exercises[idx]
    completed_ids = tracker.get_completed(st.session_state.student_name, lesson.id)
    already_passed = exercise.id in completed_ids

    # ── Header
    st.markdown(f"#### {lesson.title}  ›  Exercise {idx + 1}/{len(lesson.exercises)}")
    st.subheader(exercise.title)
    st.divider()

    # ── Two-column layout: instructions | code editor
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("**Instructions**")
        st.markdown(exercise.instructions)

        # Hints
        if exercise.hints:
            n_hints = st.session_state.hints_shown
            if n_hints < len(exercise.hints):
                if st.button("💡 Show hint"):
                    st.session_state.hints_shown += 1
                    st.rerun()
            for i in range(n_hints):
                st.info(f"**Hint {i + 1}:** {exercise.hints[i]}")

    with right:
        st.markdown("**Your code**")
        default_code = get_code(lesson.id, exercise)
        code = st.text_area(
            label="code editor",
            value=default_code,
            height=320,
            key=code_key(lesson.id, exercise.id),
            label_visibility="collapsed",
        )

        run_col, sol_col = st.columns([1, 1])
        with run_col:
            run_clicked = st.button("▶ Run", type="primary", use_container_width=True)
        with sol_col:
            if st.button("👁 Solution", use_container_width=True):
                st.session_state.show_solution = not st.session_state.show_solution
                st.rerun()

        if st.session_state.show_solution and exercise.solution:
            st.code(exercise.solution, language="python")

    # ── Run code
    if run_clicked:
        with st.spinner("Running your code…"):
            result = run_code(code, exercise.tests)
        st.session_state.last_result = result
        tracker.record_attempt(
            st.session_state.student_name, lesson.id, exercise.id, code, result.passed
        )
        if result.passed:
            already_passed = True
        st.rerun()

    # ── Output & feedback
    result = st.session_state.last_result
    if result is not None:
        st.divider()
        out_col, fb_col = st.columns([1, 1], gap="large")

        with out_col:
            st.markdown("**Output**")
            if result.stdout:
                st.code(result.stdout, language="text")
            elif not result.stderr:
                st.caption("_(no output)_")
            if result.stderr:
                st.code(result.stderr, language="text")

        with fb_col:
            st.markdown("**Feedback**")
            if result.timed_out:
                st.error("⏱ Time limit exceeded")
            elif result.passed:
                st.success("✅ " + result.feedback)
            else:
                st.error("❌ " + result.feedback)

    # ── Navigation
    st.divider()
    prev_col, _, next_col = st.columns([1, 2, 1])
    with prev_col:
        if idx > 0:
            if st.button("← Previous", use_container_width=True):
                go_to_exercise(idx - 1)
                st.rerun()
    with next_col:
        if idx < len(lesson.exercises) - 1:
            disabled = not already_passed
            if st.button("Next →", use_container_width=True, disabled=disabled,
                         help="Complete this exercise to continue"):
                go_to_exercise(idx + 1)
                st.rerun()
        else:
            if st.button("🏠 Back to lessons", use_container_width=True):
                go_home()
                st.rerun()


# ── Router ────────────────────────────────────────────────────────────────────

if st.session_state.student_name is None:
    render_name_entry()
else:
    render_sidebar()
    if st.session_state.current_lesson_id is None:
        render_lesson_browser()
    else:
        render_exercise()
