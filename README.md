# DAFS Teaching App

An interactive Python learning app for the **Data Analysis for Social Scientists** course. Students work through lessons, write real Python code, and get instant feedback — all from their browser.

## For students

### Installation

You need Python 3.10 or higher. Install the app with:

```bash
pip install git+https://github.com/your-username/dafs-teach.git
```

### Running the app

```bash
dafs-teach
```

This opens the app in your browser automatically. Your progress is saved on your own machine and will be there next time you open it.

### Updating

When new lessons are released, update with:

```bash
pip install --upgrade git+https://github.com/your-username/dafs-teach.git
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

### Local development

Clone the repo and install in editable mode so your changes take effect immediately:

```bash
git clone https://github.com/your-username/dafs-teach.git
cd dafs-teach
pip install -e .
dafs-teach
```
