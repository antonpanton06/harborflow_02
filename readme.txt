HARBORFLOW PORT INTELLIGENCE CONSOLE - TEAM README

Run instructions
----------------
Command:
Python version tested:

Team members and concrete contributions
---------------------------------------
Name: Vladyslav Pryshchep
Contribution: - Implementation: Task 3 (priority cargo), Task 4 (customer profile CSV
  export), Task 5 (port calls by month). Menu options 3-5 in main.py; related
  functions in operations.py and data_access.py.
- Testing: 12 test-ledger rows for Tasks 3-5.
- Integration: added Tasks 3-5 to the shared main.py menu.

Name: Anton Johansson
Contribution: Task 0 – Product Shell: Developed the main menu, program flow, input validation, and error handling.
Task 1 – List Registered Vessels: Implemented JSON data loading, vessel validation, alphabetical sorting, and handling of invalid records.
Task 2 – Inspect Vessel Manifest: Implemented vessel searches, upcoming port call identification, and retrieval of manifests and shipment data.
Task 9 - Incident search: Added keyword search, ranked results, cache handling, and menu integration.
Additional Contributions: Contributed to the overall program structure and integration of the assigned tasks into the main console.
Testing - 2 rows in test-ledger for Tasks 1-2.

Name: Nils-Oskar Arnell
Contribution: 
  Task 6 (Sanitize incident report), regex patterns, function: sanitize_report 
  Task 7 (Analyze longest stable event sequence), function: longest_stable_sequence
  Task 8 (Asses weather risk), functions: find_upcoming_calls, parse_forecast, build_weather_lookup
  Testing: 4 rows in test-ledger for tasks 6-8

Name (if applicable):
Contribution:

Architecture
------------
main.py responsibilities: Runs the menu, collects input, calls the other modules, displays results, and saves sanitized reports.
data_access.py responsibilities: Loads and validates JSON/CSV data, finds records, writes CSV exports, and manages the incident-index cache.
operations.py responsibilities: Handles cargo classification, customer profiles, port-call filtering, date input and validation, and weather recommendations.
text_tools.py responsibilities: Sanitizes reports, finds the longest stable event sequence, normalizes words, and builds and searches the incident index.

File and error-handling design
------------------------------
How paths are resolved: Every path is given as a relative path, so the console must be run from the project root. Folders are scanned with pathlib.Path(...).glob("*.json")
rather than hard-coded filenames, and sorted() is applied in load_records so the file order is the same on every computer. Filenames are not trusted as identifiers: 
find_manifest matches the call_id field stored inside each JSON file, so a renamed manifest still works. Output folders (exports/, exports/sanitized/) are created on demand with mkdir

How malformed or missing input is handled: 
  Bad menu input, months, dates and incident numbers are caught with try/except, and only that prompt repeats.
  Missing files, unreadable CSVs and invalid text print a clear message and return to the menu.
  Bad JSON files or records with missing or wrong-typed fields are skipped and counted, so one bad file never blocks the rest.
  Bad CSV rows (invalid date, unknown vessel) are reported and skipped.
  Broken links (missing shipment, manifest or forecast) show a message such as MISSING RECORD or Manifest unavailable. instead of crashing.
  Optional boolean flags default to False.

How generated files are updated safely:
  Customer profiles: The customer is looked up first. The existing rows are read into memory and the customer’s row is replaced or appended, so there are no duplicates. 
  The file is rewritten with one header. The export aborts if the existing file is unreadable.
  Sanitized reports: These go to separate files, so the source reports are never changed. Nothing is written when there is nothing to sanitize.
  Incident index: The cache is reused only if it is valid and newer than all incident files. Otherwise it is rebuilt, saved and reloaded. A missing incident folder raises 
  an error instead of saving an empty index.

Known limitations
-----------------
Write "None known" or describe each known limitation.
