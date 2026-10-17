"""HarborFlow Assignment 2 starter entry point."""


from data_access import load_vessels
from datetime import datetime

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
        print(f"Vessel: {vessel} not found.") # If there is no vessels to be found or wrong input
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
            print("Error - Date must use YYYY-MM-DD.")


    print(f"\nVessel name: {selected_vessel["name"]}")
    print(f"Manifest for {selected_vessel["name"]} | Call {selected_vessel["call_id"]} | {reference_date}")
    print()


if __name__ == "__main__":
    main()
