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

def load_records(directory, required_fields):
    """Load every valid JSON record in a directory without printing.

    Returns (records, skipped_files). Malformed files and records missing a
    required field are skipped so one bad file does not stop the others.
    """
    records = []
    skipped_files = 0

    for path in sorted(Path(directory).glob("*.json")):
        try:
            record = load_json(path)
        except JSONDecodeError:
            skipped_files += 1
            continue

        if isinstance(record, dict) and all(field in record for field in required_fields):
            records.append(record)
        else:
            skipped_files += 1

    return records, skipped_files


def load_shipments(directory):
    """Load valid shipments as a dictionary keyed by shipment_id."""
    required_fields = ("shipment_id", "customer", "destination", "weight_kg", "priority")
    records, skipped_files = load_records(directory, required_fields)

    shipments = {}
    for shipment in records:
        if isinstance(shipment["weight_kg"], (int, float)): # weight_kg must be a JSON number
            shipments[shipment["shipment_id"]] = shipment
        else:
            skipped_files += 1

    return shipments, skipped_files


def find_manifest(directory, call_id):
    """Return the manifest whose call_id field matches (case-insensitive), or None.

    Filenames are not trusted as identifiers; the call_id field is compared.
    """
    required_fields = ("call_id", "vessel_id", "shipment_ids", "event_codes")
    manifests, _ = load_records(directory, required_fields)

    for manifest in manifests:
        if str(manifest["call_id"]).casefold() == call_id.casefold() and isinstance(manifest["shipment_ids"], list):
            return manifest
    return None


def load_vessel_names(directory):
    """Return a lookup {vessel_id: name} built from valid vessel files."""
    vessels, _ = load_records(directory, ("vessel_id", "name", "imo", "capacity_teu"))
    return {vessel["vessel_id"]: vessel["name"] for vessel in vessels}


def write_csv(path, header, rows):
    """Rewrite a whole CSV file from an in-memory list of dictionaries.

    The header is written exactly once, also when the file is first created.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
