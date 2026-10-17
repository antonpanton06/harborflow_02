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