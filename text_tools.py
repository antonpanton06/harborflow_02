"""Regex sanitization, stable-sequence, and incident-index functions."""
import re

#  i.e template for how email-address, seal, and container looks. for finding in report for clasifying.
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")   # Make a e-mail pattern object. I.e <combination of: digits, letters, and "._%+-">@<letters, digits, dots or hyphens>.<more than 2 letters>
SEAL_PATTERN = re.compile(r"SEAL-\d{6}", re.IGNORECASE)                         # Make a seal pattern object. I.e "SEAL-"<six digits>. case incensitive.
CONTAINER_PATTERN = re.compile(r"[A-Za-z]{4}\d{7}")                             # Make a container pattern object. I.e <4 letters><7 digits>

def sanitize_report(text):
    """Classify sensitive data and return sanitized text."""
    # substitutes the sensitive data int text for [EMAIL], [SEAL], or [CONTAINER]
    text = EMAIL_PATTERN.sub("[EMAIL]", text)
    text= SEAL_PATTERN.sub("[SEAL]", text)
    text = CONTAINER_PATTERN.sub("[CONTAINER]", text)
    return text

def longest_stable_sequence(event_code):
    #start values
    start = 0
    last_seen = {}
    best_length = 0
    print(event_code)
	
    for end, event in enumerate(event_code):
        if event in last_seen and last_seen[event] >= start: 			# If event has been seen before and is inside the window, start again from after repeat event. ( window: [GATE_IN,<SCAN,SCAN>,LOAD,LOAD], first SCAN is "start")
            start = last_seen[event] + 1
        last_seen[event] = end                                          # Adds "event" as a key with "end" as data i.e index
        length = end - start + 1
        if length > best_length:          								# strictly greater, so ties keep the first
            best_length = length
            best_start = start

    return best_length, event_code[best_start:best_start + best_length]