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
main.py responsibilities:
data_access.py responsibilities:
operations.py responsibilities:
text_tools.py responsibilities:

File and error-handling design
------------------------------
How paths are resolved:
How malformed or missing input is handled:
How generated files are updated safely:

Known limitations
-----------------
Write "None known" or describe each known limitation.
