from collections import defaultdict
import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone

from models import UserAnswer, Profile, ItemMeta, FullScoringResult
from data_loader import (
    ITEM_META_DICT, 
    INSTINCT_TO_SUBTYPES_MAP, 
    FLOWPRINT_LABEL_DATA,
    ALL_ITEM_METADATA # Used for endorsed item count in Creation tie-breaking
)
from config import (
    LIKERT_SCORE_MAP, 
    CREATION_SUBTYPE_TIEBREAK_ORDER, 
    ALL_INSTINCTS,
    DRIVER_INSTINCTS_CANDIDATES,
    CREATION_INSTINCT_NAME,
    REVERSE_ITEM_MAPPING # <-- Import new mapping
)

def calculate_subtype_endorsements(user_answers: List[UserAnswer]) -> Dict[str, int]:
    """Calculates +1 endorsements for each subtype based on user answers."""
    subtype_endorsements: Dict[str, int] = defaultdict(int)
    # subtype_endorsement_counts is not strictly needed anymore by other functions
    # as Creation tie-breaking for endorsed items will re-evaluate answers.

    for answer in user_answers:
        item_meta = ITEM_META_DICT.get(answer.slot)
        if not item_meta:
            # print(f"Warning: Item slot {answer.slot} not found in metadata.")
            continue

        endorsement_value = 0
        target_subtype_for_endorsement: Optional[str] = None

        if item_meta.answer_type == "Likert":
            score = LIKERT_SCORE_MAP.get(answer.answer, 0)
            if item_meta.reverse: # This item is reverse-scored
                if score <= 2 and score != 0: # Endorsed if user disagrees with the reverse statement
                    endorsement_value = 1
                    # Get the *actual* subtype this reverse question rewards
                    target_subtype_for_endorsement = REVERSE_ITEM_MAPPING.get(item_meta.slot)
                    if not target_subtype_for_endorsement:
                        print(f"Warning: Reverse item {item_meta.slot} not found in REVERSE_ITEM_MAPPING.")
                        endorsement_value = 0 # Do not award point if mapping is missing
            else: # Normal Likert item
                if score >= 4:
                    endorsement_value = 1
                target_subtype_for_endorsement = item_meta.subtype
        
        elif item_meta.answer_type == "Scenario":
            # Scenario items are never reverse-coded per user spec.
            if item_meta.scenario_map:
                chosen_subtype = item_meta.scenario_map.get(answer.answer) # answer.answer is 'A', 'B', etc.
                if chosen_subtype and chosen_subtype != "Neutral": # "Neutral" awards no points
                    # User spec for SI-6: "If an option maps to a subtype that isn't one of the four "scored" subtypes (e.g. SI-6 option B), it's fine—award 0 points for that click."
                    # This implies we only score if chosen_subtype is a known, scorable subtype.
                    # INSTINCT_TO_SUBTYPES_MAP contains all scorable subtypes from the glossary.
                    # We need to check if chosen_subtype is a valid one.
                    is_scorable_subtype = False
                    for _, scorable_list in INSTINCT_TO_SUBTYPES_MAP.items():
                        if chosen_subtype in scorable_list:
                            is_scorable_subtype = True
                            break
                    
                    if is_scorable_subtype:
                        endorsement_value = 1
                        target_subtype_for_endorsement = chosen_subtype
                    # else: print(f"Debug: Scenario choice {answer.answer} for slot {item_meta.slot} mapped to {chosen_subtype}, which is not in glossary/scorable. No points.")

        if endorsement_value > 0 and target_subtype_for_endorsement:
            # Ensure target_subtype_for_endorsement is not "Reverse" itself, which it shouldn't be now.
            if target_subtype_for_endorsement != "Reverse":
                 subtype_endorsements[target_subtype_for_endorsement] += endorsement_value
            # else: print(f"Warning: Attempted to endorse 'Reverse' subtype directly for slot {item_meta.slot}")
            
    return dict(subtype_endorsements)


def get_raw_subtype_totals(subtype_endorsements: Dict[str, int]) -> Dict[str, int]:
    """Returns the raw subtype totals. Initializes all known subtypes to 0."""
    all_defined_subtypes: Dict[str, int] = {}
    for instinct_name in INSTINCT_TO_SUBTYPES_MAP:
        for subtype_name in INSTINCT_TO_SUBTYPES_MAP[instinct_name]:
            # "Reverse" is not a subtype in the glossary, so it won't be initialized here.
            all_defined_subtypes[subtype_name] = 0
    
    for subtype, score in subtype_endorsements.items():
        if subtype in all_defined_subtypes: # Only accumulate scores for known, defined subtypes
            all_defined_subtypes[subtype] = score
        # else: print(f"Warning: Endorsed subtype '{subtype}' not found in defined subtypes map. Score ignored for raw totals.")

    return all_defined_subtypes


def calculate_instinct_metrics(raw_subtype_totals: Dict[str, int]) -> Tuple[Dict[str, float], Dict[str, int], Dict[str, float]]:
    """Calculates mean (Strength), range, and standard deviation for each instinct."""
    instinct_strength: Dict[str, float] = {}
    instinct_range: Dict[str, int] = {}
    instinct_std_dev: Dict[str, float] = {}

    for instinct_name, subtype_list in INSTINCT_TO_SUBTYPES_MAP.items():
        if not subtype_list: # Should not happen if INSTINCT_TO_SUBTYPES_MAP is correctly populated
            instinct_strength[instinct_name] = 0.0
            instinct_range[instinct_name] = 0
            instinct_std_dev[instinct_name] = 0.0
            continue

        scores = [raw_subtype_totals.get(subtype, 0) for subtype in subtype_list if subtype != "Reverse"]
        
        if not scores: # Only had "Reverse" or empty subtype_list after filtering
            instinct_strength[instinct_name] = 0.0
            instinct_range[instinct_name] = 0
            instinct_std_dev[instinct_name] = 0.0
            continue

        # Strength = mean
        mean_score = sum(scores) / len(scores) if scores else 0
        instinct_strength[instinct_name] = round(mean_score, 2) # Round to 2 decimal places as per example

        # Range = max - min
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0
        instinct_range[instinct_name] = max_score - min_score

        # Standard Deviation
        if len(scores) > 1:
            variance = sum([(s - mean_score) ** 2 for s in scores]) / (len(scores) -1) # Sample StDev
            instinct_std_dev[instinct_name] = round(math.sqrt(variance), 2)
        elif len(scores) == 1:
             instinct_std_dev[instinct_name] = 0.0 # StDev is 0 if only one subtype score
        else: # No scores
            instinct_std_dev[instinct_name] = 0.0
            
    return instinct_strength, instinct_range, instinct_std_dev

def determine_driver_instinct(instinct_strength: Dict[str, float], instinct_range: Dict[str, int]) -> str:
    """Determines Driver Instinct based on Strength + Range, then Range for tie-breaking."""
    best_driver = ""
    max_adjusted_score = -1
    max_range_for_tiebreak = -1

    for instinct_name in DRIVER_INSTINCTS_CANDIDATES: # Excludes Creation Instinct
        strength = instinct_strength.get(instinct_name, 0.0)
        range_val = instinct_range.get(instinct_name, 0)
        adjusted_score = strength + range_val

        if adjusted_score > max_adjusted_score:
            max_adjusted_score = adjusted_score
            max_range_for_tiebreak = range_val
            best_driver = instinct_name
        elif adjusted_score == max_adjusted_score:
            if range_val > max_range_for_tiebreak:
                max_range_for_tiebreak = range_val
                best_driver = instinct_name
            # If still tied, current spec doesn't define further tie-breaking.
            # First one encountered with max adjusted score and max range wins.
            # Or, could sort by name if needed, but spec says: "Tie-break: larger Range."

    return best_driver if best_driver else DRIVER_INSTINCTS_CANDIDATES[0] # Fallback

def get_endorsed_item_counts_for_creation(user_answers: List[UserAnswer]) -> Dict[str, int]:
    """Helper to count endorsed items specifically for Creation subtypes for tie-breaking."""
    creation_subtype_endorsement_counts: Dict[str, int] = defaultdict(int)
    creation_subtypes_list = INSTINCT_TO_SUBTYPES_MAP.get(CREATION_INSTINCT_NAME, [])

    for answer in user_answers:
        item_meta = ITEM_META_DICT.get(answer.slot)
        if not item_meta or item_meta.instinct != CREATION_INSTINCT_NAME:
            continue

        endorsement_value = 0
        target_subtype: Optional[str] = None

        if item_meta.answer_type == "Likert":
            score = LIKERT_SCORE_MAP.get(answer.answer, 0)
            # Reverse items for Creation instinct are not explicitly mentioned as existing.
            # Assuming standard scoring for Creation Likert items unless spec changes.
            # If a Creation item *could* be reverse, its target subtype would need to be in REVERSE_ITEM_MAPPING.
            if item_meta.reverse:
                if score <= 2 and score != 0:
                    endorsement_value = 1
                    target_subtype = REVERSE_ITEM_MAPPING.get(item_meta.slot) 
                    if not target_subtype or target_subtype not in creation_subtypes_list:
                        # print(f"Warning: Creation reverse item {item_meta.slot} mapping error or not a creation subtype.")
                        endorsement_value = 0 # Do not count if mapping error or not a creation subtype
            else:
                if score >= 4:
                    endorsement_value = 1
                target_subtype = item_meta.subtype 
                if target_subtype not in creation_subtypes_list:
                    # print(f"Warning: Creation Likert item {item_meta.slot} subtype {target_subtype} not in creation list.")
                    endorsement_value = 0 # Do not count if not a creation subtype
        
        elif item_meta.answer_type == "Scenario":
            if item_meta.scenario_map:
                chosen_subtype = item_meta.scenario_map.get(answer.answer)
                if chosen_subtype and chosen_subtype != "Neutral" and chosen_subtype in creation_subtypes_list:
                    endorsement_value = 1
                    target_subtype = chosen_subtype
        
        if endorsement_value > 0 and target_subtype and target_subtype in creation_subtypes_list:
            creation_subtype_endorsement_counts[target_subtype] += 1
            
    return dict(creation_subtype_endorsement_counts)

def determine_creation_instinct(raw_subtype_totals: Dict[str, int], user_answers: List[UserAnswer]) -> str:
    """Determines Creation Instinct based on highest raw score, with specific tie-breaking."""
    creation_subtypes = INSTINCT_TO_SUBTYPES_MAP.get(CREATION_INSTINCT_NAME, [])
    if not creation_subtypes:
        return CREATION_SUBTYPE_TIEBREAK_ORDER[0] # Fallback if no creation subtypes defined

    highest_score = -1
    tied_subtypes: List[str] = []

    for subtype in creation_subtypes:
        score = raw_subtype_totals.get(subtype, 0)
        if score > highest_score:
            highest_score = score
            tied_subtypes = [subtype]
        elif score == highest_score:
            tied_subtypes.append(subtype)

    if len(tied_subtypes) == 1:
        return tied_subtypes[0]
    
    # Tie-breaking 1: More endorsed items
    if len(tied_subtypes) > 1:
        endorsed_counts = get_endorsed_item_counts_for_creation(user_answers)
        max_endorsed_items = -1
        subtypes_after_endorsement_tiebreak: List[str] = []
        for subtype in tied_subtypes:
            count = endorsed_counts.get(subtype, 0)
            if count > max_endorsed_items:
                max_endorsed_items = count
                subtypes_after_endorsement_tiebreak = [subtype]
            elif count == max_endorsed_items:
                subtypes_after_endorsement_tiebreak.append(subtype)
        
        if len(subtypes_after_endorsement_tiebreak) == 1:
            return subtypes_after_endorsement_tiebreak[0]
        tied_subtypes = subtypes_after_endorsement_tiebreak # Carry over for next tie-break rule

    # Tie-breaking 2: Predefined order
    if len(tied_subtypes) > 1:
        for subtype_in_order in CREATION_SUBTYPE_TIEBREAK_ORDER:
            if subtype_in_order in tied_subtypes:
                return subtype_in_order
    
    return tied_subtypes[0] if tied_subtypes else CREATION_SUBTYPE_TIEBREAK_ORDER[0] # Fallback

def determine_growth_edge(instinct_strength: Dict[str, float], instinct_std_dev: Dict[str, float]) -> str:
    """Determines Growth Edge: lowest Strength AND highest std_dev (v1 logic)."""
    # Filter out Creation Instinct for Growth Edge candidates if it's not intended to be one
    # Spec: "Instinct with lowest Strength but highest st-dev between its subtypes."
    # It doesn't explicitly exclude Creation, but Growth Edge is usually about non-Creation types.
    # For now, consider all instincts from ALL_INSTINCTS.
    
    candidate_instincts = list(ALL_INSTINCTS)
    if not candidate_instincts: return "N/A"

    min_strength = float('inf')
    instincts_with_min_strength: List[str] = [] 

    for instinct_name in candidate_instincts:
        strength = instinct_strength.get(instinct_name, float('inf'))
        if strength < min_strength:
            min_strength = strength
            instincts_with_min_strength = [instinct_name]
        elif strength == min_strength:
            instincts_with_min_strength.append(instinct_name)

    if not instincts_with_min_strength: return "N/A" # Should not happen
    if len(instincts_with_min_strength) == 1:
        return instincts_with_min_strength[0] # This one has lowest strength, check its stdev (implicitly highest if only one)

    # If multiple instincts have the same lowest strength, pick the one among them with highest std_dev
    best_growth_edge = ""
    max_std_dev = -1.0

    for instinct_name in instincts_with_min_strength:
        std_dev = instinct_std_dev.get(instinct_name, 0.0)
        if std_dev > max_std_dev:
            max_std_dev = std_dev
            best_growth_edge = instinct_name
        # If std_dev is also tied, first one encountered wins (or add alphabetical tie-break)
    
    return best_growth_edge if best_growth_edge else instincts_with_min_strength[0] # Fallback

def get_dominant_subtype(instinct_name: str, raw_subtype_totals: Dict[str, int]) -> Optional[str]:
    """Determines the dominant subtype for an instinct based on highest raw score.
       Tie-breaking: first in subtype order defined in glossary (via INSTINCT_TO_SUBTYPES_MAP which is sorted).
    """
    subtypes_for_instinct = INSTINCT_TO_SUBTYPES_MAP.get(instinct_name, [])
    if not subtypes_for_instinct:
        return None

    highest_score = -1
    dominant_subtype = None

    # Iterate in the pre-sorted order for tie-breaking
    for subtype_name in subtypes_for_instinct:
        if subtype_name == "Reverse": continue # Skip "Reverse" as a dominant subtype
        score = raw_subtype_totals.get(subtype_name, 0)
        if score > highest_score:
            highest_score = score
            dominant_subtype = subtype_name
        elif score == highest_score and dominant_subtype is None: # Handles case where first subtype has highest_score
             dominant_subtype = subtype_name
    
    return dominant_subtype

def calculate_full_profile_data(user_answers: List[UserAnswer]) -> FullScoringResult:
    """Calculates all intermediate scoring results needed for the final Profile."""
    subtype_endorsements = calculate_subtype_endorsements(user_answers)
    raw_subtype_totals = get_raw_subtype_totals(subtype_endorsements)
    
    instinct_strength, instinct_range, instinct_std_dev = calculate_instinct_metrics(raw_subtype_totals)
    
    driver = determine_driver_instinct(instinct_strength, instinct_range)
    # Pass user_answers for creation tie-breaking based on endorsed items
    creation = determine_creation_instinct(raw_subtype_totals, user_answers)
    growth_edge = determine_growth_edge(instinct_strength, instinct_std_dev)
    
    return FullScoringResult(
        subtype_raw=raw_subtype_totals,
        instinct_mean=instinct_strength,
        instinct_range=instinct_range,
        instinct_std_dev=instinct_std_dev,
        driver=driver,
        creation=creation,
        growth_edge=growth_edge
    )

def assemble_final_profile(scoring_result: FullScoringResult) -> Profile:
    """Assembles the final Profile object for the API response (v1)."""
    # 1. Look-up Flowprint Label
    flowprint_info = FLOWPRINT_LABEL_DATA.get(scoring_result.creation, {}).get(scoring_result.driver)
    headline = "Default Headline - Check Flowprint Mapping" # Fallback
    signature = "Default Signature - Check Flowprint Mapping" # Fallback
    if flowprint_info:
        headline = flowprint_info.get("headline", headline)
        signature = flowprint_info.get("signature", signature)
    else:
        # This warning is helpful for debugging content issues in Flowprint_Labels.tsv
        print(f"Warning: Flowprint label not found for Creation: {scoring_result.creation}, Driver: {scoring_result.driver}")

    # 2. Build instinctBars
    instinct_bars: Dict[str, Dict[str, Optional[float | str]]] = {}
    for instinct_name in ALL_INSTINCTS:
        dominant_subtype = get_dominant_subtype(instinct_name, scoring_result.subtype_raw)
        instinct_bars[instinct_name] = {
            "percentile": None,  # v1: null
            "dominantSubtype": dominant_subtype
        }

    # 3. Clashes (v1: empty list)
    clashes: List[str] = []

    # 4. Timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    return Profile(
        headline=headline,
        signature=signature,
        driver=scoring_result.driver,
        creation=scoring_result.creation,
        growth_edge=scoring_result.growth_edge,
        instinct_bars=instinct_bars,
        clashes=clashes,
        timestamp=timestamp,
        # Populate the new detailed score fields
        all_subtype_scores=scoring_result.subtype_raw, # This comes from FullScoringResult
        instinct_strengths=scoring_result.instinct_mean # This also comes from FullScoringResult
    )


def score_answers(user_answers: List[UserAnswer]) -> Profile:
    """Main function to take user answers and return the full Profile."""
    full_scoring_data = calculate_full_profile_data(user_answers)
    final_profile = assemble_final_profile(full_scoring_data)
    return final_profile 