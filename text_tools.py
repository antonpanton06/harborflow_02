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
    best_start = 0

    for end, event in enumerate(event_code):
        if event in last_seen and last_seen[event] >= start: 			# If event has been seen before and is inside the window, start again from after repeat event. ( window: [GATE_IN,<SCAN,SCAN>,LOAD,LOAD], first SCAN is "start")
            start = last_seen[event] + 1
        last_seen[event] = end                                          # Adds "event" as a key with "end" as data i.e index
        length = end - start + 1
        if length > best_length:          								# strictly greater, so ties keep the first
            best_length = length
            best_start = start

    return best_length, event_code[best_start:best_start + best_length]

def normalize_words(text):
    """Turn text into a list of lowercase words."""
    text = text.lower() # Changes uppercase letters to lowercase letters
    text = re.sub(r"[^\w\s]|_", " ", text) # The pattern that finds punctuation and underscores. " ": replace each match with a space.
    return text.split()

def build_incident_index(incidents):
    """Connect each report word to incident IDs and each ID to its title."""
    # The index answers "Which incidents contain this word?"
    index = {}

    # The title lookup lets search display titles without reopening reports.
    titles = {}

    # Work through the incidents one at a time.
    for incident in incidents:
        incident_id = incident["incident_id"] # Read this incident's ID from its dictionary.

        titles[incident_id] = incident["title"] # Connect this incident's ID to its title.

        words = normalize_words(incident["report"])

        unique_words = set(words)  # Remove repeated words so an incident is counted once per word.

        # Work through each distinct word in this report.
        for word in unique_words:
            # If this word is new, create an empty list for its incident IDs.
            if word not in index:
                index[word] = []

            # Do not duplicate an ID, even if it occurs in more than one file.
            if incident_id not in index[word]:
                index[word].append(incident_id)

    sorted_index = {}

    for word in sorted(index): # sorted(index) gives us the dictionary's word keys alphabetically.
        sorted_index[word] = sorted(index[word]) # Sort this word's incident IDs and store them in the new dictionary.

    sorted_titles = {}

    # Go through the incident IDs alphabetically.
    for incident_id in sorted(titles):
        # Copy each ID and its title into the new dictionary.
        sorted_titles[incident_id] = titles[incident_id]

    # Return the two sorted dictionaries.
    return sorted_index, sorted_titles

def search_incident_index(index, query):
    """Return positive (incident_id, score) matches in the required order."""
    # Apply exactly the same normalization used when indexing report text.
    words = normalize_words(query)

    unique_words = set(words) # Remove repeated words so repetitions counts only once.

    scores = {}

    # Search for each distinct query word.
    for word in unique_words:
        # Only process words that exist in our index.
        if word in index:
            # Visit every incident containing this word.
            for incident_id in index[word]:
                # Give a newly found incident a starting score of zero.
                if incident_id not in scores:
                    scores[incident_id] = 0

                # Add one point because this incident contains the word.
                scores[incident_id] += 1

    # items() gives (ID, score) pairs. A negative score sorts larger scores first.
    # The ID is the second sorting rule, used when two scores are equal.
    matches = sorted(scores.items(), key=lambda match: (-match[1], match[0]))

    return matches