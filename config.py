import os
from pathlib import Path

# Get the absolute path of the directory where this config.py file is located.
# This makes the path independent of where the script is run from.
_current_dir = Path(__file__).resolve().parent

# Define the data path relative to this file's location.
# This assumes the 'data' directory is at the same level as config.py.
DATA_PATH = _current_dir / 'data'

# TTL for cached profiles in seconds (default: 24 hours)
PROFILE_TTL_SECONDS = int(os.environ.get("NUMI_PROFILE_TTL_SECONDS", 86400))


# --- Data File Paths ---
# Use the / operator from pathlib to join the base data path with filenames
ASSESSMENT_QUESTIONS_FILE = DATA_PATH / "assessment_questions.csv"
SCENARIO_MAPPING_FILE = DATA_PATH / "scenario_mapping.json"
FLOWPRINT_LABELS_FILE = DATA_PATH / "Flowprint_Labels.tsv"
SUBTYPE_GLOSSARY_FILE = DATA_PATH / "Subtype_Glossary.csv"

# --- Likert Scale Mapping ---
# Maps user-facing answers to internal numeric scores for Likert-scale questions
LIKERT_MAPPING = {
    "Strongly Disagree": 1,
    "Disagree": 2,
    "Neutral": 3,
    "Agree": 4,
    "Strongly Agree": 5
}

# Order for Creation Instinct tie-breaking (if raw scores and endorsed items are tied)
CREATION_SUBTYPE_TIEBREAK_ORDER = [
    "Architect", "Storyteller", "Visionary", "Artist", "Activator", "Connector"
]

# Instincts list (excluding Creation for Driver calculation, including all for general processing)
ALL_INSTINCTS = [
    "Energy Rhythm", "Input Style", "Emotional Processing", "Decision Style",
    "Pattern Instinct", "Stress Response", "Environment Response", "Time Orientation",
    "Social Instinct", "Creation Instinct"
]

DRIVER_INSTINCTS_CANDIDATES = [
    instinct for instinct in ALL_INSTINCTS if instinct != "Creation Instinct"
]

CREATION_INSTINCT_NAME = "Creation Instinct"

# Mapping for reverse-coded Likert items: Slot -> Target Subtype to reward
REVERSE_ITEM_MAPPING = {
    "ER-5": "Steady",
    "IS-5": "Analyzer",
    "EP-5": "Externalizer",
    "DS-5": "Analytical",
    "PI-5": "System-Builder",
    "SR-5": "Freeze",    # As per user: "calmness here indicates opposite of Freeze; disagree = feels frozen"
    "EN-5": "Adapter",
    "TO-5": "Past",
}

# Mapping for number of items per instinct (for raw score validation/ranges)
# From instinct_map_scoring.md Section 4
# Energy Rhythm, ... Pattern Instinct (8 of them) have 10 items.
# Social Instinct has 8 items.
# Creation Instinct has 12 items.
ITEMS_PER_INSTINCT = {
    "Energy Rhythm": 10,
    "Input Style": 10,
    "Emotional Processing": 10,
    "Decision Style": 10,
    "Pattern Instinct": 10,
    "Stress Response": 10,
    "Environment Response": 10,
    "Time Orientation": 10,
    "Social Instinct": 8,
    "Creation Instinct": 12
}

# Mapping from shorthand Driver Instinct names in Flowprint_Labels.tsv to full canonical names
FLOWPRINT_DRIVER_NAME_SHORTHAND_TO_FULL = {
    "Energy": "Energy Rhythm",
    "Input": "Input Style",
    "Emotional": "Emotional Processing", # Assuming 'Emotional' is shorthand for 'Emotional Processing'
    "Decision": "Decision Style",
    "Pattern": "Pattern Instinct",
    "Stress": "Stress Response",
    "Environment": "Environment Response",
    "Time": "Time Orientation",
    "Social": "Social Instinct"
    # Add any other shorthands if they exist in the TSV
} 