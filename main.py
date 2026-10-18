"""HarborFlow Assignment 2 starter entry point."""


from data_access import load_vessels, load_csv
from datetime import datetime
import csv
from operations import find_upcoming_call

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



    print(f"\nVessel name: {selected_vessel["name"]}")
    print(f"Manifest for {selected_vessel["name"]} | Call {selected_call["call_id"]} | {formated_date}")

    
    print()


if __name__ == "__main__":
    main()
