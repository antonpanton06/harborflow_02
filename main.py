"""HarborFlow Assignment 2 starter entry point."""


from data_access import load_vessels, load_csv, load_shipments, find_manifest, load_vessel_names, write_csv, load_records, load_incident_index
from datetime import datetime
from pathlib import Path
import csv
from operations import (find_upcoming_call, classify_manifest, CATEGORY_ORDER,
                        build_customer_profile, upsert_profile, PROFILE_HEADER,
                        find_calls_by_month, build_weather_lookup, Get_reference_date,
                        find_upcoming_calls, parse_forecast, recommend)
from text_tools import sanitize_report, longest_stable_sequence, search_incident_index

CUSTOMER_PROFILES_PATH = "exports/customer-profiles.csv"

def main():
    """Run the HarborFlow Port Intelligence Console."""
    run = True
    # TODO: implement the persistent menu and orchestrate the services.
    while run:
        print("HARBORFLOW PORT INTELLIGENCE")
        print("1. List registered vessels")
        print("2. Inspect a vessel manifest")
        print("3. Identify priority cargo")
        print("4. Export a customer operations profile")
        print("5. Find port calls by month")
        print("6. Sanitize an incident report")
        print("7. Analyze the longest stable event sequence")
        print("8. Assess weather risk for upcoming calls")
        print("9. Search incident reports")
        print("10. Close console")

        try:
            option = int(input("Select service: "))
        except ValueError:
            print("Error - Select a service from 1 to 10.") # So program doesn't crash when input ≠ an integer
            continue 

        # Menu selection each option calls the apropriate function:
        if option == 1:
            list_registered_vessels()

        elif option == 2:
            inspect_vessel_manifest()

        elif option == 3:
            identify_priority_cargo()

        elif option == 4:
            export_customer_profile()

        elif option == 5:
            find_port_calls_by_month()

        elif option == 6:
            Sanitize_an_incident_report()

        elif option == 7:
            Analyze_the_longest_stable_event_sequence()

        elif option == 8:
            Assess_weather_risk_for_upcoming_calls()

        elif option == 9:
            search_incident_reports()

        elif option == 10:
            print("Console closed. HarborFlow operational data remains safe.") 
            run =False # Makes while loop = False and stops loop.

        else:
            print("Error - Select a service from 1 to 10.") # If input = an integer which is not 1-10.


#Option 1:
def list_registered_vessels():
    """List all registered vessels."""
    try:
        vessels, skipped_files = load_vessels("dataset/vessels") # Fetches the data
        
        print("\nRegistered HarborFlow vessels:")
        for vessel in vessels:
            print(f"- {vessel['name']} | IMO {vessel['imo']} | {vessel['capacity_teu']:,} TEU") # For each vessel found whitin the data
        print(f"Skipped vessel files: {skipped_files}\n") # Any malformed files gets recognised here

    except FileNotFoundError as error:      # If a malformed file is found then the program will list that specific file
        print(error)
        return

#Option 2:
def inspect_vessel_manifest():
    """Let the user inspect a vessel's manifest."""
    print() # Just for looks...

    vessels, skipped_files = load_vessels("dataset/vessels") # Fetches the data

    for number, vessel in enumerate(vessels, start=1): # List of vessels for selection
        print(f"{number}. {vessel['name']}")
    print()

    vessel_name = input("Vessel name: ").strip().casefold() # You select the name of the vessel listed
    
    selected_vessel = None # Start value
    for vessel in vessels:
        if vessel["name"].casefold() == vessel_name:
            selected_vessel = vessel # A for lopp that looks through the vessels to see if 

    if selected_vessel == None:
        print(f"Vessel not found.") # If there is no vessel that match to be found.
        return

    reference_date = Get_reference_date()

    try:
        port_calls = load_csv("dataset/port_calls.csv") # Calls for the function with "dataset/port_calls.csv" as the path.
    except FileNotFoundError:
        print("Port calls file can't be found.") # Prints if file can't be found
        return # Returns so that user gets sent back to main.
    except csv.Error:
        print("Port calls file could not be read.") # Prints if the file is found but can't be read.
        return # Returns so that user gets sent back to main.

    selected_call = find_upcoming_call(port_calls, selected_vessel["vessel_id"], reference_date)

    if selected_call == None:
        print("No upcoming port calls found.")
        return

    arrival_date = datetime.strptime(selected_call["arrival_date"], "%Y-%m-%d").date()
    formated_date = arrival_date.strftime("%d %B %Y")
    
    print(f"\nManifest for {selected_vessel["name"]} | Call {selected_call["call_id"]} | {formated_date}")

    manifest = find_manifest("dataset/manifests", selected_call["call_id"])

    if manifest is None:
        print("Manifest unavailable.")
        return # If no manifest matches the selected call["call_id"]

    shipments, skipped_files = load_shipments("dataset/shipments") # "dataset/shipments" is the directory we're searching for.

    # Start values that gets updated as the program goes through the manifest
    resolved_weight = 0.0
    missing_records = 0 
    
    for number, shipment_id in enumerate(manifest["shipment_ids"], start=1):
        shipment = shipments.get(shipment_id)

        if shipment == None:
            print(f"{number}. {shipment_id} | MISSING RECORD") # If the shipment and the shipment_id has no match then add a missing record and continue.
            missing_records += 1 
            continue

        cargo_type = shipment.get("cargo_type", "NOT PROVIDED") # Finds the cargo type for the shipment
        resolved_weight += shipment["weight_kg"] # Calculates the resolved weight

        print(f"{number}. {shipment_id} | {shipment['customer']} | "f"{shipment['weight_kg']} kg | {cargo_type}")

    print(f"Declared shipments: {len(manifest['shipment_ids'])}") # len() calculates the no. of matching shipments_ids
    print(f"Resolved weight: {resolved_weight:.2f} kg") # Prints the resolved weight with two decimals
    print(f"Missing shipment records: {missing_records}") # Prints exact amount of missing records the program detects
    print()


#Option 3: (written by Vlad)
def identify_priority_cargo():
    """Task 3 - classify every resolved shipment of one port call.

    Flow: ask call ID -> check it exists in port_calls.csv -> find its
    manifest -> load shipments -> classify (operations.py) -> print.
    Unknown call or missing manifest returns to the menu (appendix rule).
    """
    call_id = input("Call ID: ").strip()     # strip() removes surrounding spaces

    try:
        port_calls = load_csv("dataset/port_calls.csv")
    except FileNotFoundError:
        print("Port calls file can't be found.")
        return                               # return = back to the menu
    except csv.Error:
        print("Port calls file could not be read.")
        return

    # Every known call ID in lowercase, so the user may type any case.
    known_call_ids = [call["call_id"].casefold() for call in port_calls]
    if call_id.casefold() not in known_call_ids:
        print("Port call not found.")
        return

    # The call exists, but its manifest may be missing (e.g. HFL-BAD-9999).
    manifest = find_manifest("dataset/manifests", call_id)
    if manifest is None:
        print("Manifest unavailable.")
        return

    shipments, _ = load_shipments("dataset/shipments")      # {shipment_id: shipment}
    lines, totals = classify_manifest(manifest, shipments)  # business logic lives in operations.py

    # Each line is a tuple, unpacked directly in the for statement.
    for shipment_id, category, reason in lines:
        print(f"{shipment_id} | {category} | {reason}")
    # Build "CONTROLLED=1, COLD CHAIN=0, ..." in the fixed category order.
    summary = ", ".join(f"{category}={totals[category]}" for category in CATEGORY_ORDER)
    print(f"Category totals: {summary}")


#Option 4: (written by Vlad)
def export_customer_profile():
    """Task 4 - create or update one customer's row in exports/customer-profiles.csv.

    Flow: ask name -> build profile from shipments -> read existing export
    -> replace or append the row -> rewrite the whole file.
    """
    customer_name = input("Customer name: ").strip()

    shipments, _ = load_shipments("dataset/shipments")
    profile = build_customer_profile(customer_name, shipments)
    if profile is None:
        # Return before touching the file: it is not created or modified.
        print("Customer not found.")
        return

    try:
        rows = load_csv(CUSTOMER_PROFILES_PATH)  # existing rows kept in memory
    except FileNotFoundError:
        rows = []       # first run: not an error, the file is created below
    except csv.Error:
        print("Customer profile export could not be read.")
        return          # do not overwrite a file we could not read

    rows = upsert_profile(rows, profile)                     # replace or append
    write_csv(CUSTOMER_PROFILES_PATH, PROFILE_HEADER, rows)  # rewrite with header once
    print(f"Customer profile updated: {CUSTOMER_PROFILES_PATH}")


#Option 5: (written by Vlad)
def find_port_calls_by_month():
    """Task 5 - list all port calls in one month, sorted by date and vessel name.

    Flow: ask month (repeat only this prompt on error) -> load port calls
    and vessel names -> filter and sort (operations.py) -> print.
    """
    month = None                    # loop state: no valid month yet
    while month is None:            # loop variable instead of while True (appendix rule)
        try:
            value = int(input("Month (1-12): "))   # "abc" raises ValueError here
            if not 1 <= value <= 12:
                raise ValueError                   # treat 0 or 13 the same way as "abc"
            month = value                          # valid: the loop condition becomes False
        except ValueError:
            print("Error - Enter a month from 1 to 12.")

    try:
        port_calls = load_csv("dataset/port_calls.csv")
    except FileNotFoundError:
        print("Port calls file can't be found.")
        return
    except csv.Error:
        print("Port calls file could not be read.")
        return

    vessel_names = load_vessel_names("dataset/vessels")     # {vessel_id: name}
    calls, problems = find_calls_by_month(port_calls, vessel_names, month)

    # Report skipped rows first (e.g. the invalid date 2026-02-30).
    for problem in problems:
        print(problem)

    if not calls:
        print("No port calls found.")
        return

    # Any date in that month gives its name: 10 -> "October".
    month_name = datetime(2000, month, 1).strftime("%B")
    print(f"Port calls in {month_name}:")
    for arrival_date, vessel_name, port_code, call_id in calls:
        # %d %B %Y -> "18 October 2026"
        print(f"- {arrival_date.strftime('%d %B %Y')} | {vessel_name} | {port_code} | {call_id}")

#Option 6:
def Sanitize_an_incident_report():
    directory = "dataset/incidents"
    required_fields = ("incident_id", "call_id", "title", "report") # Define the fields every incident must contain.
    incidents,_ = load_records(directory, required_fields) # Reuses the loader to read the valid incident records.
    incidents.sort(key=lambda incident: incident["title"].casefold())
    if not incidents:
        print("No incident reports available.")
        return
    for count, incident in enumerate(incidents,start=1):                # List all possible incident reports
            print(f"{count}. {incident["title"]}")
    
    incident_choice = None
    while incident_choice is None:
        try:
            choice = int(input(f"Incident number(1-{count}):"))
            if choice <= 0 or choice > count:
                raise ValueError
            incident_choice = incidents[choice - 1]
        except ValueError:
            print(f"Error - Select a listed incident.")
    
    sanitized_text = sanitize_report(incident_choice["report"])
    if sanitized_text == incident_choice["report"]:
        print("Incident contains no share-sensitive identifiers.")
        return
    
    output_path = Path("exports/sanitized") / f"{incident_choice["incident_id"]}-sanitized.txt"  # Create the file path for the incident report
    output_path.parent.mkdir(parents=True, exist_ok=True)                                       # Makes the parent folders if they do not exist
    with open(output_path, "w", encoding="utf-8", newline="") as file:                          # writes to the file
        file.write(sanitized_text)
    print("Incident sanitized:", sanitized_text)

#Option 7:
def Analyze_the_longest_stable_event_sequence():
    call_id = input("Call ID: ").strip()
    manifest = find_manifest("dataset/manifests", call_id)
    if manifest is None:
        print("Manifest unavailable.")
        return

    length, sequence = longest_stable_sequence(manifest["event_codes"])                         # Return length of sequence and the sequence itself
    print(f"Event codes: {','.join(manifest['event_codes'])}")                                  # Print string listing event codes
    print(f"Longest stable sequence length: {length}")                                          # Length of longest sequence
    print(f"Sequence: {' -> '.join(sequence)}")                                                 # Longest sequence 

#Option 8:
def Assess_weather_risk_for_upcoming_calls():
    """Show weather recommendations for a vessel's upcoming port calls."""
    try:
        vessels, _ = load_vessels("dataset/vessels")
    except FileNotFoundError as error:
        print(error)
        return
    # List vessels for selection
    vessel_name = input("Vessel name: ").strip().casefold()
    selected_vessel = None
    for vessel in vessels:
        if vessel["name"].casefold() == vessel_name:
            selected_vessel = vessel
            break
    if selected_vessel is None:
        print("Vessel not found.")
        return
    
    reference_date = None
    while reference_date is None: 
        reference_date = Get_reference_date() # Get the reference date from the user input and validate it.
    try:
        port_calls = load_csv("dataset/port_calls.csv")
        weather_rows = load_csv("dataset/weather.csv")
    except FileNotFoundError:
        print("Port calls or weather file can't be found.")
        return
    except csv.Error:
        print("Port calls or weather file could not be read.")
        return

    calls, problems = find_upcoming_calls(port_calls, selected_vessel["vessel_id"], reference_date) # Find the upcoming calls for the selected vessel and the reference date, returning a list of calls and any problems encountered.
    # Print any problems encountered while processing the calls.
    for problem in problems:
        print(problem)
    if not calls: # If there are no upcoming calls for the selected vessel, print a message and return.
        print("No upcoming port calls found.")
        return

    weather = build_weather_lookup(weather_rows) # Build a lookup dictionary for the weather data, using the port code and date as the key.

    for arrival_date, call in calls: # Iterate through the upcoming calls for the selected vessel, printing the weather recommendations for each call.
        print(f"\n{selected_vessel['name']} | {call['port_code']} | {arrival_date.strftime('%d %B %Y')}")

        row = weather.get((call["port_code"].strip(), arrival_date.isoformat())) # Get the weather data for the port code and arrival date from the weather lookup dictionary. If there is no weather data for the port code and arrival date, print a message and continue to the next call.
        if row is None:
            print("Forecast unavailable")
            continue

        try: # Parse the weather data for wind, rain, and waves from the weather row. If the weather row is malformed, print a message and continue to the next call.
            wind, rain, waves = parse_forecast(row)
        except ValueError:
            print(f"Skipped forecast for {call['call_id']}: malformed forecast row.")
            continue
        # Print the weather data and recommendations for the upcoming call.
        print(f"Wind: {wind:.1f} km/h | Rain: {rain:.1f} mm | Waves: {waves:.1f} m")
        print("Recommendation: " + " ".join(recommend(wind, rain, waves)))

# Option 9:
def search_incident_reports():
    """Ask for keywords and display matches from the saved incident index."""
    
    query = input("Search incident reports: ").strip() # What you want to search for: e.g "reefer delay"

    try:
        cache = load_incident_index() # Fetch data
     # Handle file failures 
    except OSError as error:
        print(f"Incident search unavailable: {error}")
        return
    except UnicodeDecodeError:
        # A source report with unreadable text cannot be indexed safely.
        print("Incident search unavailable: a report is not valid UTF-8 text.")
        return

    # The search function only receives cached data; it never reads reports.
    matches = search_incident_index(cache["index"], query)
    print(f"Matches for '{query}':")

    # Each result is an (ID, score) pair; titles also come from the cache.
    # When there are no matches, the loop prints no result lines.
    for incident_id, score in matches:
        title = cache["titles"][incident_id]
        print(f"- {incident_id} | score {score} | {title}")


if __name__ == "__main__":
    main()
