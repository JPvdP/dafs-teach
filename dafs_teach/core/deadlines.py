from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml


@dataclass
class Deadline:
    id: str
    deadline: datetime
    lessons: list[str]


def load_deadlines(path: Path) -> list[Deadline]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return [
        Deadline(
            id=item["id"],
            deadline=datetime.fromisoformat(item["deadline"]),
            lessons=item.get("lessons", []),
        )
        for item in data
    ]
