"""File loading and path-handling functions for HarborFlow.

Create reusable JSON and CSV loaders here. Do not hard-code sample records.
"""

from json import load, JSONDecodeError
from pathlib import Path
import csv

def load_json(path):
    """Load a JSON file from the given path."""
    with open(path, "r", encoding="utf-8") as file:
        data = load(file)
    return data

def load_csv(path):
    """Load CSV rows as a list of dictionaries."""
    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
    return rows

def load_vessels(directory):
    """Load vessel data from the given directory."""
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Vessel directory not found: {directory}") # If the file isn't found then raise an error. And then print what file is missing.

    vessels = []
    skipped_files = 0

    for path in directory.glob("*.json"):
        try:
            required_fields = ("vessel_id", "name", "imo", "capacity_teu")
            vessel = load_json(path)

            if not all(field in vessel for field in required_fields): # Returns True only if all keys exists within the dictionary
                skipped_files += 1
                print((f"Skipped {path.name}: missing required field.")) # Print what file has the missing or false value
                continue
        except JSONDecodeError: # If a JSON-file is malformed, makes so the program doesn't crash + counts a skipped file.
            skipped_files += 1
            print(f"Skipped {path.name}: malformed JSON.")
            continue

        vessels.append(vessel) # Fills an empty list with the vessel values

    vessels.sort(key=lambda vessel: vessel["name"].casefold()) # Sort by vessels by alphabet.
    return vessels, skipped_files