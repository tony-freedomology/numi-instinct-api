import os
from pathlib import Path

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent

# Data path: defaults to /app/data/ within the project, can be overridden by NUMI_DATA_PATH
# As per spec, csv/tsv files will be in /app/data, so if BASE_DIR is /app, then data is BASE_DIR / "data"
# If running locally and BASE_DIR is different, NUMI_DATA_PATH should be set.
DEFAULT_DATA_PATH = BASE_DIR / "data"
DATA_PATH = Path(os.getenv("NUMI_DATA_PATH", DEFAULT_DATA_PATH))

ASSESSMENT_QUESTIONS_FILE = DATA_PATH / "assessment_questions.csv"
SCENARIO_MAPPING_FILE = DATA_PATH / "scenario_mapping.json"
FLOWPRINT_LABELS_FILE = DATA_PATH / "Flowprint_Labels.tsv"
SUBTYPE_GLOSSARY_FILE = DATA_PATH / "Subtype_Glossary.csv"

# Profile Store TTL (in seconds)
# Defaults to 24 hours (24 * 60 * 60 = 86400 seconds)
DEFAULT_PROFILE_TTL_SECONDS = 24 * 60 * 60
PROFILE_TTL_SECONDS = int(os.getenv("NUMI_PROFILE_TTL_SECONDS", DEFAULT_PROFILE_TTL_SECONDS))

# Likert score mapping
LIKERT_SCORE_MAP = {
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