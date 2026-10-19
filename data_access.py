"""File loading and path-handling functions for HarborFlow.

Create reusable JSON and CSV loaders here. Do not hard-code sample records.
"""

from json import load, dump, JSONDecodeError
from pathlib import Path
import csv
from text_tools import build_incident_index

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
    """Load every valid JSON record in a directory without printing anything.

    Shared loader used by Tasks 3, 4, 5 and 9 (written by Vlad).

    Arguments:
        directory       - folder to scan, e.g. "dataset/shipments"
        required_fields - tuple of keys every record must contain

    Returns a tuple (records, skipped_files):
        records       - list of dictionaries that passed validation
        skipped_files - how many files were rejected

    A malformed file or a record missing a required field is skipped,
    so one bad file never stops the other files from loading.
    """
    records = []        # valid records are collected here
    skipped_files = 0   # counter for rejected files

    # Path(directory).glob("*.json") finds every .json file in the folder.
    # sorted() makes the order the same on every computer.
    for path in sorted(Path(directory).glob("*.json")):
        try:
            record = load_json(path)    # JSON text -> Python dict/list
        except JSONDecodeError:
            # The file is not valid JSON (e.g. a missing closing brace).
            skipped_files += 1
            continue                    # skip this file, go to the next one

        # The record must be a dictionary AND contain every required key.
        # all(...) is True only if the check is True for every field.
        if isinstance(record, dict) and all(field in record for field in required_fields):
            records.append(record)
        else:
            skipped_files += 1          # wrong structure or missing field

    return records, skipped_files


def load_shipments(directory):
    """Load valid shipments as a dictionary keyed by shipment_id.

    Example result: {"SHP-1042": {...shipment...}, "SHP-1043": {...}}

    A dictionary lets other functions find a shipment directly by its ID
    (shipments.get("SHP-1042")) instead of searching through a list.
    Returns (shipments, skipped_files).
    """
    # Required fields come from dataset/DATA-DICTIONARY.md.
    required_fields = ("shipment_id", "customer", "destination", "weight_kg", "priority")
    records, skipped_files = load_records(directory, required_fields)

    shipments = {}
    for shipment in records:
        # weight_kg must be a JSON number; a string or null would break
        # the weight sums and the >= 5000 comparison later.
        if isinstance(shipment["weight_kg"], (int, float)):
            shipments[shipment["shipment_id"]] = shipment   # key = ID, value = whole record
        else:
            skipped_files += 1

    return shipments, skipped_files


def find_manifest(directory, call_id):
    """Return the manifest whose call_id field matches (case-insensitive), or None.

    Filenames are not trusted as identifiers: we compare the call_id field
    stored inside each JSON file, so a renamed file still works.
    """
    required_fields = ("call_id", "vessel_id", "shipment_ids", "event_codes")
    manifests, _ = load_records(directory, required_fields)   # _ = skipped count not needed

    for manifest in manifests:
        # casefold() makes "hfl-aar-2071" equal to "HFL-AAR-2071".
        # shipment_ids must be a list, otherwise looping over it would fail.
        if str(manifest["call_id"]).casefold() == call_id.casefold() and isinstance(manifest["shipment_ids"], list):
            return manifest     # first match found: stop searching
    return None                 # loop finished without a match


def load_vessel_names(directory):
    """Return a lookup {vessel_id: name} built from valid vessel files.

    Example: {"VSL-001": "Baltic Pioneer", "VSL-002": "Nordic Relay"}
    Used by Task 5 to turn the vessel_id in port_calls.csv into a name.
    The malformed vessel file is skipped by load_records.
    """
    vessels, _ = load_records(directory, ("vessel_id", "name", "imo", "capacity_teu"))
    # Dictionary comprehension: one key/value pair per vessel.
    return {vessel["vessel_id"]: vessel["name"] for vessel in vessels}


def write_csv(path, header, rows):
    """Rewrite a whole CSV file from an in-memory list of dictionaries.

    Used by Task 4. The header is written exactly once, also when the file
    is created for the first time.

    Arguments:
        path   - output file, e.g. "exports/customer-profiles.csv"
        header - list of column names in output order
        rows   - list of dictionaries, one per CSV row
    """
    path = Path(path)
    # Create the exports/ folder if it does not exist yet.
    # exist_ok=True: no error if the folder is already there.
    path.parent.mkdir(parents=True, exist_ok=True)
    # "w" overwrites the file from scratch. newline="" is required by the
    # csv module to avoid empty lines between rows on Windows.
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=header)   # writes dicts as CSV rows
        writer.writeheader()       # column names, once
        writer.writerows(rows)     # every row in the list

def rebuild_incident_index():
   
    required_fields = ("incident_id", "call_id", "title", "report") # Define the fields every incident must contain.

    incidents, skipped_files = load_records("dataset/incidents", required_fields) # Reuse loader to read the valid incident records.

    index, titles = build_incident_index(incidents)

    cache = {"index": index, "titles": titles} # Put both dictionaries inside one dictionary for the JSON file.

    # Open the cache file for writing, creating it if it does not exist.
    with open("dataset/incident-index.json", "w", encoding="utf-8") as file:
        # Save readable JSON and keep dictionary keys sorted.
        dump(cache, file, indent=4, sort_keys=True)

    return cache

def load_incident_index():

    # Store the locations of the saved index and the source reports.
    cache_path = Path("dataset/incident-index.json") 
    incident_directory = Path("dataset/incidents")

    # Check that the source folder exists.
    if not incident_directory.is_dir():
        raise FileNotFoundError("Incident directory not found.")

    try:
        cache = load_json(cache_path) # Reuse existing function to read the saved JSON.

    except (FileNotFoundError, JSONDecodeError):
        # Rebuild if the cache is missing or contains broken JSON.
        return rebuild_incident_index()

    # Check that the cache contains the expected dictionaries.
    if not isinstance(cache, dict):
        return rebuild_incident_index()

    if not isinstance(cache.get("index"), dict):
        return rebuild_incident_index()

    if not isinstance(cache.get("titles"), dict):
        return rebuild_incident_index()

    cache_time = cache_path.stat().st_mtime # Read the time when the cache file was last modified.

    # Check each incident file's modification time.
    for incident_path in incident_directory.glob("*.json"):
        # A newer incident means the saved index may be outdated.
        if incident_path.stat().st_mtime > cache_time:
            return rebuild_incident_index()

    # The cache passed our checks, so reuse it.
    return cache

