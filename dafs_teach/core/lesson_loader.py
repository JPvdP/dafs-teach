import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List


@dataclass
class Test:
    type: str        # 'output_contains' | 'output_equals' | 'assert'
    value: str = ""  # used by output_* types
    code: str = ""   # used by assert type (appended to student code)
    description: str = ""


@dataclass
class Exercise:
    id: str
    title: str
    instructions: str
    starter_code: str = ""
    tests: List[Test] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    solution: str = ""


@dataclass
class Lesson:
    id: str
    title: str
    description: str
    exercises: List[Exercise]


def load_lessons(content_dir: Path) -> List[Lesson]:
    lessons_dir = content_dir / "lessons"
    lessons = []
    for path in sorted(lessons_dir.glob("*.yaml")):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        exercises = [
            Exercise(
                id=ex["id"],
                title=ex["title"],
                instructions=ex["instructions"],
                starter_code=ex.get("starter_code", ""),
                tests=[Test(**t) for t in ex.get("tests", [])],
                hints=ex.get("hints", []),
                solution=ex.get("solution", ""),
            )
            for ex in data.get("exercises", [])
        ]
        lessons.append(
            Lesson(
                id=path.stem,
                title=data["title"],
                description=data["description"],
                exercises=exercises,
            )
        )
    return lessons
