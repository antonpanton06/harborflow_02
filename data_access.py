"""File loading and path-handling functions for HarborFlow.

Create reusable JSON and CSV loaders here. Do not hard-code sample records.
"""

from json import load, dump, JSONDecodeError
from pathlib import Path
import csv
from text_tools import build_incident_index, normalize_words

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

# ---------- Task 9: save, validate and reuse the incident index ----------

def rebuild_incident_index():
    """Read valid reports, save a fresh index, and load the saved result."""
    # A missing folder is different from a folder with no incident files.
    if not Path("dataset/incidents").is_dir():
        raise FileNotFoundError("Incident directory not found.")

    # Reuse the shared loader; _ means we do not need its skipped-file count.
    required_fields = ("incident_id", "call_id", "title", "report")
    incidents, _ = load_records("dataset/incidents", required_fields)

    # Required fields must contain text before we can normalize or index them.
    valid_incidents = []
    for incident in incidents:
        if all(isinstance(incident[field], str) for field in required_fields):
            valid_incidents.append(incident)

    # Our text function returns two dictionaries; store both in one JSON object.
    index, titles = build_incident_index(valid_incidents)
    cache = {"index": index, "titles": titles}

    # This is the only dataset file Task 9 writes. Source reports stay unchanged.
    with open("dataset/incident-index.json", "w", encoding="utf-8") as file:
        # indent makes the JSON readable; sort_keys orders dictionary keys.
        dump(cache, file, indent=4, sort_keys=True, ensure_ascii=False)
        file.write("\n")

    # Search uses data loaded from the saved JSON, including on the first run.
    return load_json("dataset/incident-index.json")


def valid_incident_cache(cache):
    """Return True only when the saved data has the structure search needs."""
    # Valid JSON can still contain the wrong data, such as a list or a number.
    if not isinstance(cache, dict):
        return False
    if set(cache) != {"index", "titles"}:
        return False
    if not isinstance(cache["index"], dict):
        return False
    if not isinstance(cache["titles"], dict):
        return False

    # Shorter names make the following checks easier to read.
    index = cache["index"]
    titles = cache["titles"]

    # Dictionaries loaded from JSON preserve the key order in the saved file.
    if list(index) != sorted(index) or list(titles) != sorted(titles):
        return False

    # Every displayed title must be text.
    for title in titles.values():
        if not isinstance(title, str):
            return False

    # Each normalized word must point to a sorted list of distinct incident IDs.
    for word, incident_ids in index.items():
        if normalize_words(word) != [word]:
            return False
        if not isinstance(incident_ids, list):
            return False

        # Check types before using IDs as dictionary keys or sorting them.
        for incident_id in incident_ids:
            if not isinstance(incident_id, str):
                return False
            if incident_id not in titles:
                return False

        # set removes duplicates; sorted returns the required alphabetical order.
        if incident_ids != sorted(set(incident_ids)):
            return False

    # All checks passed. The caller can safely use this cache.
    return True


def load_incident_index():
    """Reuse a valid fresh cache, or rebuild a missing, malformed or old one."""
    # Relative paths work when the console is run from the project root.
    cache_path = Path("dataset/incident-index.json")
    incident_directory = Path("dataset/incidents")

    # Tell the menu about missing source data instead of saving an empty index.
    if not incident_directory.is_dir():
        raise FileNotFoundError("Incident directory not found.")

    try:
        # Reuse the JSON loader rather than opening files in the menu.
        cache = load_json(cache_path)
    except (FileNotFoundError, JSONDecodeError, UnicodeDecodeError):
        # Missing files, broken JSON and invalid text encoding are recoverable.
        return rebuild_incident_index()

    # A file can be readable JSON but still have an unusable structure.
    if not valid_incident_cache(cache):
        return rebuild_incident_index()

    # Nanoseconds retain enough precision to notice quick successive edits.
    cache_time = cache_path.stat().st_mtime_ns
    for incident_path in incident_directory.glob("*.json"):
        # Only inspect file times here; fresh caches do not reread report text.
        if incident_path.stat().st_mtime_ns > cache_time:
            return rebuild_incident_index()

    return cache
