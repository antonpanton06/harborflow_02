"""HarborFlow Assignment 2 starter entry point."""


def main():
    """Run the HarborFlow Port Intelligence Console."""
    # TODO: implement the persistent menu and orchestrate the services.
    while True:
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
            print("Error - Please select a service from 1 to 10.")
            continue

        if option == 10:
            print("Console closed. HarborFlow operational data remains safe.")
            return False


if __name__ == "__main__":
    main()
