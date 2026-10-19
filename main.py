"""HarborFlow Assignment 2 starter entry point."""


from data_access import load_vessels, load_csv, load_shipments, find_manifest, load_vessel_names, write_csv, load_records
from datetime import datetime
from pathlib import Path
import csv
from operations import (find_upcoming_call, classify_manifest, CATEGORY_ORDER,
                        build_customer_profile, upsert_profile, PROFILE_HEADER,
                        find_calls_by_month, build_weather_lookup)
from text_tools import sanitize_report, longest_stable_sequence

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
            print("Error - Select a service from 1 to 10.")
            continue

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

        elif option == 10:
            print("Console closed. HarborFlow operational data remains safe.")
            run =False

        else:
            print("Error - Select a service from 1 to 10.")


#Option 1:
def list_registered_vessels():
    """List all registered vessels."""
    try:
        vessels, skipped_files = load_vessels("dataset/vessels")
        
        print("\nRegistered HarborFlow vessels:")
        for vessel in vessels:
            print(f"- {vessel['name']} | IMO {vessel['imo']} | {vessel['capacity_teu']:,} TEU")
        print(f"Skipped vessel files: {skipped_files}\n")

    except FileNotFoundError as error:
        print(error)
        return

#Option 2:
def inspect_vessel_manifest():
    print()
    """Let the user inspect a vessel's manifest."""

    vessels, skipped_files = load_vessels("dataset/vessels")

    for number, vessel in enumerate(vessels, start=1): # List of vessels for selection
        print(f"{number}. {vessel['name']}")
    print()

    vessel_name = input("Vessel name: ").strip().casefold()
    
    selected_vessel = None
    for vessel in vessels:
        if vessel["name"].casefold() == vessel_name:
            selected_vessel = vessel

    if selected_vessel == None:
        print(f"Vessel not found.") # If there is no vessel that match to be found.
        return

    reference_date = None
    while reference_date is None:
        date_text = input(("Reference date (YYYY-MM-DD): "))

        try:
            parsed_date = datetime.strptime(date_text, "%Y-%m-%d").date()

            if parsed_date.isoformat() != date_text:
                raise ValueError

            reference_date = parsed_date
        except ValueError:
            print("Error - Date must use YYYY-MM-DD.") # Prints if a ValueError uccurs.

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


#Option 3:
def identify_priority_cargo():
    """Classify every resolved shipment of one port call."""
    call_id = input("Call ID: ").strip()

    try:
        port_calls = load_csv("dataset/port_calls.csv")
    except FileNotFoundError:
        print("Port calls file can't be found.")
        return
    except csv.Error:
        print("Port calls file could not be read.")
        return

    known_call_ids = [call["call_id"].casefold() for call in port_calls]
    if call_id.casefold() not in known_call_ids:
        print("Port call not found.")
        return

    manifest = find_manifest("dataset/manifests", call_id)
    if manifest is None:
        print("Manifest unavailable.")
        return

    shipments, _ = load_shipments("dataset/shipments")
    lines, totals = classify_manifest(manifest, shipments)

    for shipment_id, category, reason in lines:
        print(f"{shipment_id} | {category} | {reason}")
    summary = ", ".join(f"{category}={totals[category]}" for category in CATEGORY_ORDER)
    print(f"Category totals: {summary}")


#Option 4:
def export_customer_profile():
    """Create or update one customer's row in exports/customer-profiles.csv."""
    customer_name = input("Customer name: ").strip()

    shipments, _ = load_shipments("dataset/shipments")
    profile = build_customer_profile(customer_name, shipments)
    if profile is None:
        print("Customer not found.") # The export file is not created or modified
        return

    try:
        rows = load_csv(CUSTOMER_PROFILES_PATH) # Existing rows kept in memory
    except FileNotFoundError:
        rows = [] # First run: the file is created below
    except csv.Error:
        print("Customer profile export could not be read.")
        return

    rows = upsert_profile(rows, profile)
    write_csv(CUSTOMER_PROFILES_PATH, PROFILE_HEADER, rows)
    print(f"Customer profile updated: {CUSTOMER_PROFILES_PATH}")


#Option 5:
def find_port_calls_by_month():
    """List all port calls in one month, sorted by date and vessel name."""
    month = None
    while month is None: # Repeat only the month prompt
        try:
            value = int(input("Month (1-12): "))
            if not 1 <= value <= 12:
                raise ValueError
            month = value
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

    vessel_names = load_vessel_names("dataset/vessels")
    calls, problems = find_calls_by_month(port_calls, vessel_names, month)

    for problem in problems:
        print(problem)

    if not calls:
        print("No port calls found.")
        return

    month_name = datetime(2000, month, 1).strftime("%B")
    print(f"Port calls in {month_name}:")
    for arrival_date, vessel_name, port_code, call_id in calls:
        print(f"- {arrival_date.strftime('%d %B %Y')} | {vessel_name} | {port_code} | {call_id}")

#Option 6:
def Sanitize_an_incident_report():
    directory = "dataset/incidents"
    required_fields = ("incident_id", "call_id", "title", "report")
    incidents,_ = load_records(directory, required_fields)
    incidents.sort(key=lambda incident: incident["title"].casefold())

    for count, incident in enumerate(incidents,start=1):                # List all possible incident reports
            print(f"{count}. {incident["title"]}")
    
    incident_choice = None
    while incident_choice is None:
        try:
            choice = int(input(f"Incident number(1-{count}):"))
            if choice < 0 or choice > count:
                raise ValueError
            incident_choice = incidents[choice - 1]
        except ValueError:
            print(f"Error - Select a listed incident")
    
    sanitized_text = sanitize_report(incident_choice["report"])
    if sanitized_text == incident_choice["report"]:
        print("Incident contains no share-sensitive identifiers.")
        return
    
    output_path = Path("exports/sanitized") / f"{incident_choice["incident_id"]}-sanitized.txt"  # Create the file path for the incident report
    output_path.parent.mkdir(parents=True, exist_ok=True)                                       # Makes the parent folders if they do not exist
    with open(output_path, "w", encoding="utf-8", newline="") as file:                          # writes to the file
        file.write(sanitized_text)

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

def Assess_weather_risk_for_upcoming_calls():
    port_calls = load_csv("dataset/port_calls.csv")
    weather_rows = load_csv("dataset/weather.csv")
    vessels,_ = load_vessels("dataset/vessels")

    vessel_name = input("Vessel name: ").strip().casefold()    
    selected_vessel = None
    for vessel in vessels:
        if vessel["name"].casefold() == vessel_name:
            selected_vessel = vessel

    if selected_vessel == None:
        print(f"Vessel not found.") # If there is no vessel that match to be found.
        return
    
    reference_date = None
    while reference_date is None:
        date_text = input(("Reference date (YYYY-MM-DD): "))
        try:
            parsed_date = datetime.strptime(date_text, "%Y-%m-%d").date()

            if parsed_date.isoformat() != date_text:
                raise ValueError

            reference_date = parsed_date
        except ValueError:
            print("Error - Date must use YYYY-MM-DD.") # Prints if a ValueError uccurs.
    
    print(vessel)

    for count, vessel in enumerate(vessels, start=1):
        pass
    print(build_weather_lookup(weather_rows))
    # print(find_upcoming_call(port_calls))
if __name__ == "__main__":
    main()
