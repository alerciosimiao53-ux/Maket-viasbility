from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_dir(path: str | Path) -> Path:
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))
