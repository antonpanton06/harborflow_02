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

# ---------- Task 3: priority cargo ----------

CATEGORY_ORDER = ("CONTROLLED", "COLD CHAIN", "EXPEDITE", "STANDARD")


def classify_shipment(shipment):
    """Pure function: return (category, reason) for one shipment.

    Rule order is business policy - the first matching rule wins:
      1. hazardous is true                    -> CONTROLLED
      2. temperature_controlled is true       -> COLD CHAIN
      3. priority EXPRESS or weight >= 5000   -> EXPEDITE
      4. otherwise                            -> STANDARD
    Missing boolean flags count as false.
    """
    if shipment.get("hazardous", False) is True:
        return "CONTROLLED", "hazardous cargo"
    if shipment.get("temperature_controlled", False) is True:
        return "COLD CHAIN", "temperature controlled"
    if shipment["priority"].upper() == "EXPRESS":
        return "EXPEDITE", "express service"
    if shipment["weight_kg"] >= 5000:
        return "EXPEDITE", "heavy cargo"
    return "STANDARD", "standard handling"


def classify_manifest(manifest, shipments):
    """Classify every resolved shipment of a manifest in manifest order.

    Returns (lines, totals). Missing shipment records are not classified.
    """
    lines = []
    totals = {category: 0 for category in CATEGORY_ORDER}

    for shipment_id in manifest["shipment_ids"]:
        shipment = shipments.get(shipment_id)
        if shipment is None:
            continue
        category, reason = classify_shipment(shipment)
        lines.append((shipment_id, category, reason))
        totals[category] += 1

    return lines, totals


# ---------- Task 4: customer profile ----------

PROFILE_HEADER = ["customer", "shipment_count", "total_weight_kg", "express_count", "destinations"]


def build_customer_profile(customer_name, shipments):
    """Summarise all shipments of one customer. Returns None if no shipment matches."""
    matches = [shipment for shipment in shipments.values()
               if shipment["customer"].casefold() == customer_name.casefold()]
    if not matches:
        return None

    destinations = sorted({shipment["destination"] for shipment in matches})
    express_count = sum(1 for shipment in matches if shipment["priority"].upper() == "EXPRESS")
    total_weight = sum(shipment["weight_kg"] for shipment in matches)

    return {
        "customer": matches[0]["customer"], # Name as written in the dataset
        "shipment_count": len(matches),
        "total_weight_kg": f"{total_weight:.2f}",
        "express_count": express_count,
        "destinations": "|".join(destinations),
    }


def upsert_profile(rows, profile):
    """Return a new list where the customer's row is replaced, or appended if new."""
    updated_rows = []
    replaced = False

    for row in rows:
        if row.get("customer", "").casefold() == profile["customer"].casefold():
            if not replaced: # Replace in place, never keep a duplicate
                updated_rows.append(profile)
                replaced = True
        else:
            updated_rows.append(row)

    if not replaced:
        updated_rows.append(profile)
    return updated_rows


# ---------- Task 5: port calls by month ----------

def parse_iso_date(text):
    """Parse a strict YYYY-MM-DD date. Raises ValueError otherwise."""
    parsed_date = datetime.strptime(text, "%Y-%m-%d").date()
    if parsed_date.isoformat() != text:
        raise ValueError(f"Not ISO format: {text}")
    return parsed_date


def find_calls_by_month(port_calls, vessel_names, month):
    """Return (calls, problems) for one month.

    calls are (arrival_date, vessel_name, port_code, call_id) sorted by date
    and then vessel name. problems describe rows that were reported and skipped.
    """
    calls = []
    problems = []

    for call in port_calls:
        try:
            arrival_date = parse_iso_date(call["arrival_date"])
        except ValueError:
            problems.append(f"Skipped {call['call_id']}: invalid arrival date.")
            continue

        vessel_name = vessel_names.get(call["vessel_id"])
        if vessel_name is None:
            problems.append(f"Skipped {call['call_id']}: unknown vessel {call['vessel_id']}.")
            continue

        if arrival_date.month == month:
            calls.append((arrival_date, vessel_name, call["port_code"], call["call_id"]))

    calls.sort(key=lambda call: (call[0], call[1].casefold()))
    return calls, problems

def build_weather_lookup(weather_rows):
    """Return {(port_code, date_text): row}. The first row wins on duplicates."""
    lookup = {}
    for row in weather_rows:
        key = (row["port_code"].strip(), row["date"].strip())
        lookup.setdefault(key, row)
    return lookup