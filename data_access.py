"""File loading and path-handling functions for HarborFlow.

Create reusable JSON and CSV loaders here. Do not hard-code sample records.
"""

from json import load, JSONDecodeError
from pathlib import Path

def load_json(path):
    """Load a JSON file from the given path."""
    with open(path, "r") as file:
        data = load(file)
    return data

def load_vessels(directory):
    """Load vessel data from the given directory."""
    directory = Path(__file__).parent

    vessels = []
    skipped_files = 0

    for path in directory.glob("*.json"):
        if not path.name.startswith("dataset\\vessels\\"):
            continue
        try:
            vessel = load_json(path)
        except JSONDecodeError:
            skipped_files += 1
            continue

        vessels.append(vessel)
    return vessels, skipped_files