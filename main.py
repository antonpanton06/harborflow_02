"""HarborFlow Assignment 2 starter entry point."""


from data_access import load_vessels, load_json


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
        elif option == 10:
            print("Console closed. HarborFlow operational data remains safe.")
            run =False

        else:
            print("Error - Select a service from 1 to 10.")


#Option 1:
def list_registered_vessels():
    """List all registered vessels."""
     
    vessels, skipped_files = load_vessels("dataset/vessels")
    
    print("Registered HarborFlow vessels:")
    for vessel in vessels:
        print(f"- {vessel['name'].upper()} | IMO {vessel['imo']} | {vessel['capacity_teu']} TEU")
    print(f"Skipped vessel files: {skipped_files}")


if __name__ == "__main__":
    main()
