# DAFS Teaching App

An interactive Python learning app for the **Data Analysis for Sustainability** course. Students work through lessons, write real Python code, and get instant feedback — all from their browser.

## For students

### Installation

You need Python 3.10 or higher. Install the app with:

```bash
pip install git+https://github.com/JPvdP/dafs-teach.git
```

### Running the app

```bash
dafs-teach
```

This opens the app in your browser automatically. Your progress is saved on your own machine and will be there next time you open it.

### Updating

When new lessons are released, update with:

```bash
pip install --upgrade git+https://github.com/JPvdP/dafs-teach.git
```

---

## For instructors

### Adding a new lesson

1. Create a new `.yaml` file in `dafs_teach/content/lessons/`
2. The filename controls the order — use a numeric prefix (e.g. `03_matplotlib.yaml`)
3. Commit and push — students get the new lesson after running `pip install --upgrade`

### Lesson file format

```yaml
title: My New Lesson
description: A short description shown on the lesson card.

exercises:

  - id: unique_exercise_id        # used for progress tracking, never change it
    title: Exercise Title
    instructions: |
      Write your instructions here using **markdown**.
      This supports code blocks, tables, bold, etc.
    starter_code: |
      # Pre-filled code shown in the editor
      x = 
    tests:
      - type: output_contains     # stdout must contain this string
        value: "expected text"
      - type: output_equals       # stdout must exactly match (stripped)
        value: "42"
      - type: assert              # this code is appended to student code and must not raise
        code: "assert result == 42, 'result should be 42'"
        description: "result should equal 42"   # shown to student on failure
    hints:
      - "First hint — revealed one at a time"
      - "Second hint"
    solution: |
      # Reference solution — shown only if the student clicks 'Solution'
      x = 42
      print(x)
```

### Test types

| Type | Behaviour |
|------|-----------|
| `output_contains` | The student's printed output must contain `value` |
| `output_equals` | The student's printed output must exactly equal `value` (whitespace stripped) |
| `assert` | `code` is appended to the student's code and run — any exception counts as failure |

### "Explain the script" exercises

Instead of writing code, students can be asked to explain a script in their own
words. Set `type: explain` and give the script to read; it is shown with line
numbers. There are no tests: the exercise is completed once the explanation is
at least `min_words` long (not counting the template), after which the model
answer in `solution` is shown so students can compare.

```yaml
  - id: explain_something
    type: explain
    title: Exercise Title
    min_words: 40                 # optional, default 30
    script: |
      # The code students have to read
    instructions: |
      Explain any functions students haven't seen before, then the task.
    starter_code: |
      Template shown in the explanation box (optional)
    hints:
      - "Hints work as usual"
    solution: |
      **Model explanation** in markdown, shown after submitting.
```

### Checking module completions

When a student finishes every exercise in a lesson, the app shows them a short
completion code (under "🎓 Get completion code") to send you. Verify one with:

```bash
dafs-teach verify "Alice Example" 01_python_basics ABCDE-12345
```

This prints `VALID` or `INVALID` — no shared database needed, the code is
derived from the student's name and the lesson id.

By default the app uses a built-in secret to derive codes. **Since this repo
is public, that default gives no real protection** — anyone can read the
source and generate their own valid-looking codes. Before relying on this for
grading, set your own private secret (e.g. in your shell profile, and tell
students to set the same value before running the app):

```bash
export DAFS_TEACH_SECRET="something-only-you-and-your-students-know"
```

Both you (when running `dafs-teach verify`) and your students (when running
`dafs-teach`) need the same `DAFS_TEACH_SECRET` value for codes to check out.

### Monitoring student progress (anonymous, deadline-based)

Each student's progress is saved locally on their own machine. Rather than
tracking individual students remotely — that's what your weekly lecture +
lab time is for — the app can send you an **anonymous, aggregate-only**
summary of how a set of lessons went, once their deadline has passed. No
student name or identifier is ever included, only per-exercise
completed/attempts/solution-view counts. The goal is spotting cohort-wide
patterns (which exercises caused the most trouble) between sessions, not
identifying who's struggling.

**How it's triggered:** the app has no background process, so "after the
deadline" means *the next time a student opens the app once the deadline has
passed*. It checks silently but visibly (a small on-screen notice, never
hidden) and sends at most once per deadline — already-sent deadlines are
remembered locally and skipped. Given your weekly lab rhythm, students will
almost always reopen the app within a day or two of a deadline anyway.

**One-time setup:**

1. Create a new Google Sheet (e.g. "DAFS Progress").
2. Go to **Extensions → Apps Script**, delete the placeholder code, and paste
   in the contents of [`instructor_tools/progress_sync_apps_script.gs`](instructor_tools/progress_sync_apps_script.gs).
3. Click **Deploy → New deployment**, type **Web app**, set "Execute as" to
   **Me** and "Who has access" to **Anyone**, then click **Deploy**.
4. Copy the Web app URL it gives you.
5. Set it as an environment variable, and tell students to set the same
   value before running the app (alongside `DAFS_TEACH_SECRET` if you use
   that too):

   ```bash
   export DAFS_TEACH_SYNC_URL="https://script.google.com/macros/s/XXXXX/exec"
   ```

6. Edit [`dafs_teach/content/deadlines.yaml`](dafs_teach/content/deadlines.yaml)
   to match your actual course schedule — it groups lesson ids under a
   deadline id and date. Commit and push; students get the updated schedule
   via `pip install --upgrade`, same as new lessons.

**Useful views once data is coming in:** add a second sheet tab and use
`QUERY` to summarise the raw `Progress` tab, e.g. exercises with the most
students stuck on them, for a given deadline:

```
=QUERY(Progress!A:H, "select C, D, count(D), sum(F) where E = 0 and A = 'week1' group by C, D order by count(D) desc label count(D) 'students not done', sum(F) 'total attempts'", 1)
```

Or a quick per-deadline completion overview:

```
=QUERY(Progress!A:H, "select A, sum(E), count(D) group by A label sum(E) 'completed', count(D) 'exercise records'", 1)
```

Since reports are anonymous, there's no per-student breakdown to query —
that's by design, not a missing feature.

### Local development

Clone the repo and install in editable mode so your changes take effect immediately:

```bash
git clone https://github.com/JPvdP/dafs-teach.git
cd dafs-teach
pip install -e .
dafs-teach
```
