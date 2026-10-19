"""HarborFlow operational business rules.

Keep calculations and record-processing logic separate from user interaction
where practical.
"""
from datetime import datetime

def find_upcoming_call(port_calls, vessel_id, reference_date):
    """Find the earliest qualifying call for a vessel."""
    upcoming_calls = []

    for call in port_calls:
        if call["vessel_id"] != vessel_id:
            continue

        try:
            arrival_date = datetime.strptime(call["arrival_date"], "%Y-%m-%d").date()
        except ValueError:
            print(f"Skipped {call['call_id']}: invalid arrival date.")
            continue

        if arrival_date >= reference_date:
            upcoming_calls.append(call)

    if not upcoming_calls:
        return None

    upcoming_calls.sort(key=lambda call: (call["arrival_date"], call["call_id"]))
    return upcoming_calls [0]

# ---------- Task 3: priority cargo (written by Vlad) ----------

# Fixed order used when printing the category totals.
CATEGORY_ORDER = ("CONTROLLED", "COLD CHAIN", "EXPEDITE", "STANDARD")


def classify_shipment(shipment):
    """Pure function: return (category, reason) for one shipment.

    "Pure" = no input() or print(); it only takes data and returns a result,
    which makes it easy to test.

    Rule order is business policy - the first matching rule wins:
      1. hazardous is true                    -> CONTROLLED
      2. temperature_controlled is true       -> COLD CHAIN
      3. priority EXPRESS or weight >= 5000   -> EXPEDITE
      4. otherwise                            -> STANDARD
    Each rule ends with return, so later rules are never checked once one
    has matched. Example: a hazardous EXPRESS shipment is CONTROLLED.
    """
    # .get(key, False): the boolean flags are optional in the dataset and a
    # missing flag must count as False (DATA-DICTIONARY.md).
    if shipment.get("hazardous", False) is True:
        return "CONTROLLED", "hazardous cargo"
    if shipment.get("temperature_controlled", False) is True:
        return "COLD CHAIN", "temperature controlled"
    # priority is a required field, so [] is safe here. upper() accepts "express".
    if shipment["priority"].upper() == "EXPRESS":
        return "EXPEDITE", "express service"
    # >= means exactly 5000 kg also counts as heavy.
    if shipment["weight_kg"] >= 5000:
        return "EXPEDITE", "heavy cargo"
    return "STANDARD", "standard handling"


def classify_manifest(manifest, shipments):
    """Classify every resolved shipment of a manifest, in manifest order.

    Arguments:
        manifest  - one manifest dictionary (has "shipment_ids")
        shipments - dictionary {shipment_id: shipment} from load_shipments

    Returns (lines, totals):
        lines  - list of tuples (shipment_id, category, reason)
        totals - dictionary {category: count} with every category present
    Missing shipment records (e.g. SHP-1051) are skipped, not classified.
    """
    lines = []
    # Start every category at 0 so the summary also prints e.g. "COLD CHAIN=0".
    totals = {category: 0 for category in CATEGORY_ORDER}

    for shipment_id in manifest["shipment_ids"]:
        shipment = shipments.get(shipment_id)   # None if the ID has no record
        if shipment is None:
            continue                            # missing link: skip, do not crash
        category, reason = classify_shipment(shipment)
        lines.append((shipment_id, category, reason))
        totals[category] += 1                   # count this category

    return lines, totals


# ---------- Task 4: customer profile (written by Vlad) ----------

# Column order of exports/customer-profiles.csv, as defined in the brief.
PROFILE_HEADER = ["customer", "shipment_count", "total_weight_kg", "express_count", "destinations"]


def build_customer_profile(customer_name, shipments):
    """Summarise all shipments of one customer.

    Returns one CSV row as a dictionary, or None if the customer has no
    shipments. Matching ignores upper/lower case.
    """
    # Keep only this customer's shipments (list comprehension with a filter).
    matches = [shipment for shipment in shipments.values()
               if shipment["customer"].casefold() == customer_name.casefold()]
    if not matches:          # empty list -> customer not found
        return None

    # {...} builds a set, which removes duplicate destinations;
    # sorted() turns it into an alphabetical list, e.g. ["CPH", "GOT", "OSL"].
    destinations = sorted({shipment["destination"] for shipment in matches})
    # Add 1 for every EXPRESS shipment.
    express_count = sum(1 for shipment in matches if shipment["priority"].upper() == "EXPRESS")
    total_weight = sum(shipment["weight_kg"] for shipment in matches)

    return {
        "customer": matches[0]["customer"],         # name as written in the dataset, not as typed
        "shipment_count": len(matches),
        "total_weight_kg": f"{total_weight:.2f}",   # always two decimals, e.g. "6420.50"
        "express_count": express_count,
        "destinations": "|".join(destinations),     # ["CPH","GOT"] -> "CPH|GOT"
    }


def upsert_profile(rows, profile):
    """Return a new row list where the customer's row is replaced, or appended if new.

    "Upsert" = update if it exists, insert if it does not.
    Replacing in place keeps the row position and guarantees one row per
    customer, so exporting the same customer twice never creates a duplicate.
    """
    updated_rows = []
    replaced = False        # flag: has this customer's row already been replaced?

    for row in rows:
        # row.get("customer", "") avoids a crash if a row lacks the column.
        if row.get("customer", "").casefold() == profile["customer"].casefold():
            if not replaced:                     # first time we meet this customer
                updated_rows.append(profile)     # put the new data in the old position
                replaced = True
            # an old duplicate row (if any) is simply not copied
        else:
            updated_rows.append(row)             # other customers are kept unchanged

    if not replaced:                             # customer was not in the file
        updated_rows.append(profile)             # add as a new row at the end
    return updated_rows


# ---------- Task 5: port calls by month (written by Vlad) ----------

def parse_iso_date(text):
    """Parse a strict YYYY-MM-DD date. Raises ValueError otherwise.

    strptime raises ValueError for impossible dates such as 2026-02-30.
    The isoformat() check also rejects non-padded input such as 2026-2-5,
    which strptime would otherwise accept.
    """
    parsed_date = datetime.strptime(text, "%Y-%m-%d").date()   # string -> date
    if parsed_date.isoformat() != text:                        # date -> string, compare
        raise ValueError(f"Not ISO format: {text}")
    return parsed_date


def find_calls_by_month(port_calls, vessel_names, month):
    """Return (calls, problems) for one month.

    Arguments:
        port_calls   - rows from port_calls.csv (list of dictionaries)
        vessel_names - lookup {vessel_id: name} from load_vessel_names
        month        - integer 1-12 chosen by the user

    calls    - tuples (arrival_date, vessel_name, port_code, call_id),
               sorted by date and then vessel name
    problems - messages for rows that were reported and skipped
    """
    calls = []
    problems = []

    for call in port_calls:
        # 1. The date must be valid; a bad row is reported and skipped.
        try:
            arrival_date = parse_iso_date(call["arrival_date"])
        except ValueError:
            problems.append(f"Skipped {call['call_id']}: invalid arrival date.")
            continue

        # 2. The vessel_id must link to a known vessel (relationship check).
        vessel_name = vessel_names.get(call["vessel_id"])
        if vessel_name is None:
            problems.append(f"Skipped {call['call_id']}: unknown vessel {call['vessel_id']}.")
            continue

        # 3. Keep only calls in the requested month.
        if arrival_date.month == month:
            calls.append((arrival_date, vessel_name, call["port_code"], call["call_id"]))

    # Sort key is a tuple: first by date (call[0]); when dates are equal,
    # by vessel name (call[1]) ignoring case.
    calls.sort(key=lambda call: (call[0], call[1].casefold()))
    return calls, problems


def find_upcoming_calls(port_calls, vessel_id, reference_date):
    """Return (calls, problems): all upcoming calls of a vessel, sorted.

    calls are (arrival_date, call) tuples sorted by date, then call_id.
    """
    calls = []          # Qalifying calls of the vessel
    problems = []       # Problems encountered while processing the calls. to be printed.

    for call in port_calls:
        if call["vessel_id"] != vessel_id: # ignore calls of other vessels
            continue
        try: # Check if the arrival date is valid and parse it to a date object. If not valid, add to problems list and continue to next call.
            arrival_date = parse_iso_date(call["arrival_date"]) 
        except ValueError:
            problems.append(f"Skipped {call['call_id']}: invalid arrival date.")
            continue
        if arrival_date >= reference_date: # If the arrival date is greater than or equal to the reference date, add the call to the calls list.
            calls.append((arrival_date, call))

    calls.sort(key=lambda item: (item[0], item[1]["call_id"])) # Sort the calls list by arrival date and then by call_id.
    return calls, problems

def parse_forecast(row):
    """Return (wind, rain, waves) as floats. Raises ValueError if malformed."""
    try:
        return (float(row["wind_kmh"]),
                float(row["precipitation_mm"]),
                float(row["wave_height_m"]))
    except (ValueError, TypeError, KeyError):
        raise ValueError("malformed forecast row")

def build_weather_lookup(weather_rows):
    """Return {(port_code, date_text): row}. The first row wins on duplicates."""
    lookup = {}
    for row in weather_rows: # Iterate through the weather rows and build a lookup dictionary with the port code and date as the key. If there are duplicate keys, the first row wins.
        key = (row["port_code"].strip(), row["date"].strip())
        lookup.setdefault(key, row) # Add the row to the lookup dictionary if the key does not already exist. If the key already exists, do nothing (the first row wins).
    return lookup

def recommend(wind, rain, waves):
    """Return every recommendation whose condition is true, in table order."""
    recommendations = []
    if wind >= 45:
        recommendations.append("Suspend crane operations.")
    if waves >= 2.5:
        recommendations.append("Arrange tug assistance.")
    if rain >= 8 and wind < 45:
        recommendations.append("Prepare covered handling.")
    if not recommendations:
        recommendations.append("Normal operating plan.")
    return recommendations

def Get_reference_date():
    """Input reference date"""
    reference_date = None
    while reference_date is None:
        date_text = input(("Reference date (YYYY-MM-DD): "))
        try:
            parsed_date = datetime.strptime(date_text, "%Y-%m-%d").date()

            if parsed_date.isoformat() != date_text: # strptime accepts yyyy-m-d which we do not want so if input is not in the format yyyy-mm-dd reject reference date
                raise ValueError
            reference_date = parsed_date
        except ValueError:
            print("Error - Date must use YYYY-MM-DD.") # Prints if a ValueError uccurs.
    return reference_date