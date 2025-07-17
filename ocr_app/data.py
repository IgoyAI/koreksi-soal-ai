import json
import os
from typing import Any, Dict

def get_data_file() -> str:
    """Return the path to the JSON data file."""
    base = os.path.dirname(__file__)
    return os.path.join(base, "data.json")


def load_data() -> Dict[str, Any]:
    """Load project data from the JSON file."""
    path = get_data_file()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {"projects": []}


def save_data(data: Dict[str, Any]) -> None:
    """Save project data to the JSON file."""
    path = get_data_file()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

