from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_resource_json(relative_path: str) -> dict[str, Any]:
    base_dir = Path(__file__).resolve().parent
    target = base_dir / relative_path
    with target.open("r", encoding="utf-8") as file:
        return json.load(file)

