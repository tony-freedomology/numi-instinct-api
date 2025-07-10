import csv
import json
from typing import List, Dict, Any, Set
from functools import lru_cache

from models import ItemMeta
from config import (
    ASSESSMENT_QUESTIONS_FILE,
    SCENARIO_MAPPING_FILE,
    FLOWPRINT_LABELS_FILE,
    SUBTYPE_GLOSSARY_FILE,
    ALL_INSTINCTS,
    FLOWPRINT_DRIVER_NAME_SHORTHAND_TO_FULL
)

@lru_cache(maxsize=None) # Cache results so files are read once
def load_scenario_mapping() -> Dict[str, Dict[str, str]]:
    """Loads the scenario question to subtype mapping."""
    with open(SCENARIO_MAPPING_FILE, 'r') as f:
        return json.load(f)

@lru_cache(maxsize=None)
def load_assessment_questions() -> List[ItemMeta]:
    """Loads assessment questions and maps them to ItemMeta objects."""
    questions: List[ItemMeta] = []
    scenario_mappings = load_scenario_mapping()

    with open(ASSESSMENT_QUESTIONS_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            slot = row["Slot"]
            subtype = row["Subtype"]
            is_reverse = subtype == "Reverse"
            
            # If subtype is "Reverse", the actual subtype is in "Item Text" or needs to be inferred.
            # For now, the CSV has "Reverse" in Subtype column directly. If it meant the item text
            # contains the true subtype, this logic needs adjustment.
            # Based on current CSV, if Subtype is "Reverse", we use it as is.
            # The scoring logic will handle reverse scoring based on this boolean flag.

            item_scenario_map: Dict[str, str] | None = None
            if row["Answer Type"] == "Scenario":
                if slot in scenario_mappings:
                    item_scenario_map = scenario_mappings[slot].copy() # Use .copy() if modifications are expected
                    # Remove prompt_key as it's not part of the A/B/C/D answer mapping
                    if 'prompt_key' in item_scenario_map:
                        del item_scenario_map['prompt_key']
                else:
                    # This case should ideally not happen if data is consistent
                    print(f"Warning: Scenario question {slot} not found in scenario_mapping.json")
            
            questions.append(
                ItemMeta(
                    slot=slot,
                    instinct=row["Instinct"],
                    subtype=subtype, # This will be "Reverse" for reverse-scored items
                    reverse=is_reverse,
                    answer_type=row["Answer Type"],
                    scenario_map=item_scenario_map
                )
            )
    return questions

@lru_cache(maxsize=None)
def load_flowprint_labels() -> Dict[str, Dict[str, str]]:
    """Loads Flowprint labels: (Creation Instinct, Driver Instinct) -> {label, signature}.
       Converts shorthand driver names from TSV to full canonical names for consistency.
    """
    labels: Dict[str, Dict[str, str]] = {}
    with open(FLOWPRINT_LABELS_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            creation_instinct = row["Creation Instinct"]
            driver_instinct_shorthand = row["Driver Instinct"] # This is the shorthand from TSV

            # Convert shorthand to full name.
            # If a shorthand is not in the map, it might be an error in the TSV or an incomplete map.
            # For robustness, we'll use the original value from TSV if not found in map, but log a warning.
            driver_instinct_full = FLOWPRINT_DRIVER_NAME_SHORTHAND_TO_FULL.get(driver_instinct_shorthand)
            
            if driver_instinct_full is None:
                # This case means the shorthand from TSV was not in our mapping.
                # It could be that the TSV already contains a full name, or it's an unexpected value.
                # We'll use the value from the TSV as is, but issue a warning.
                print(f"Warning: Driver Instinct shorthand '{driver_instinct_shorthand}' from row (Creation: {creation_instinct}) in Flowprint_Labels.tsv was not found in the shorthand mapping (FLOWPRINT_DRIVER_NAME_SHORTHAND_TO_FULL in config.py). Using value '{driver_instinct_shorthand}' directly. Please verify if this is intended or if the mapping needs an update.")
                driver_instinct_full = driver_instinct_shorthand # Use the original value

            if creation_instinct not in labels:
                labels[creation_instinct] = {}
            
            # Use the (potentially converted) full driver instinct name as the key
            labels[creation_instinct][driver_instinct_full] = {
                "headline": row["Flowprint Label"],
                "signature": row["Signature Sentence"],
            }
    return labels

@lru_cache(maxsize=None)
def load_subtype_glossary() -> Dict[str, Dict[str, str]]:
    """Loads subtype definitions: Instinct -> Subtype -> Definition."""
    glossary: Dict[str, Dict[str, str]] = {}
    with open(SUBTYPE_GLOSSARY_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            instinct = row["Instinct"]
            subtype = row["Subtype"]
            if instinct not in glossary:
                glossary[instinct] = {}
            glossary[instinct][subtype] = row["Definition"]
    return glossary

@lru_cache(maxsize=None)
def get_instinct_to_subtypes_map() -> Dict[str, List[str]]:
    """Creates a map of instinct to its list of subtypes (excluding "Reverse" as a subtype itself)."""
    questions = load_assessment_questions()
    instinct_subtypes_map: Dict[str, Set[str]] = {instinct: set() for instinct in ALL_INSTINCTS}
    for q_meta in questions:
        # We don't add "Reverse" as a subtype, it's a scoring modification.
        # The actual subtype for a reverse question is the one it modifies.
        # This requires that assessment_questions.csv has the *actual* subtype listed,
        # and "Reverse" is just a flag or a special value in a different column.
        # Based on current CSV structure, the subtype IS "Reverse" for some items.
        # The user clarification stated: "Store any "ignored" options as "Neutral" so they award no points."
        # This refers to scenario options, not the primary subtype of a question.
        # For dominant subtype calculation, we need the defined subtypes.
        # The glossary is a good source for defined subtypes per instinct.
        
        # Let's use the glossary to define the canonical list of subtypes per instinct.
        # This avoids issues if a subtype is only mentioned in a reverse question.
        pass # Will be populated using glossary

    glossary_definitions = load_subtype_glossary()
    final_map: Dict[str, List[str]] = {instinct: [] for instinct in ALL_INSTINCTS}
    for instinct_name, subtypes_dict in glossary_definitions.items():
        if instinct_name in final_map:
            final_map[instinct_name] = sorted(list(subtypes_dict.keys()))
    
    # Ensure all instincts from ALL_INSTINCTS are present, even if not in glossary (should not happen)
    for instinct in ALL_INSTINCTS:
        if instinct not in final_map or not final_map[instinct]:
            # Fallback: try to get from questions if glossary is incomplete for an instinct
            temp_subtypes = set()
            for q_meta in questions:
                if q_meta.instinct == instinct and not q_meta.reverse:
                    temp_subtypes.add(q_meta.subtype)
            if temp_subtypes:
                 final_map[instinct] = sorted(list(temp_subtypes))
            # print(f"Warning: Instinct {instinct} not found in glossary or has no subtypes defined there. Inferred: {final_map[instinct]}")

    # Add subtypes for 'Creation Instinct' if they were missed (they have more items)
    # This map is critical for dominant subtype tie-breaking.
    # The Subtype_Glossary.csv defines the subtypes for each instinct.
    return final_map


# Pre-load all data on startup by calling the functions
ALL_ITEM_METADATA: List[ItemMeta] = load_assessment_questions()
FLOWPRINT_LABEL_DATA: Dict[str, Dict[str, str]] = load_flowprint_labels()
SUBTYPE_GLOSSARY_DATA: Dict[str, Dict[str, str]] = load_subtype_glossary()
INSTINCT_TO_SUBTYPES_MAP: Dict[str, List[str]] = get_instinct_to_subtypes_map()

# For quick lookup
ITEM_META_DICT: Dict[str, ItemMeta] = {item.slot: item for item in ALL_ITEM_METADATA} 