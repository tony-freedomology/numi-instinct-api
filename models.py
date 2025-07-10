from pydantic import BaseModel
from typing import Optional, Dict, List

class ItemMeta(BaseModel):
    slot: str              # "ER-1"
    instinct: str          # "Energy Rhythm"
    subtype: str           # "Bursty"
    reverse: bool          # True if subtype == "Reverse"
    answer_type: str       # "Likert" | "Scenario"
    # scenario_map only for AnswerType=="Scenario"
    scenario_map: Optional[Dict[str, str]] = None  # "A"->"Bursty", ...

class UserAnswer(BaseModel):
    slot: str
    answer: str            # raw text or key ("A")

class Profile(BaseModel):
    headline: str
    signature: str
    driver: str
    creation: str
    growth_edge: str # For v1, this might be a placeholder or determined by simple logic
    instinct_bars: Dict[str, Dict[str, Optional[float | str]]] # e.g. {"Energy Rhythm": {"percentile": None, "dominantSubtype": "Bursty"}}
    clashes: List[str] # For v1, this will be an empty list
    timestamp: str
    # New fields for detailed scores
    all_subtype_scores: Optional[Dict[str, int]] = None
    instinct_strengths: Optional[Dict[str, float]] = None

# Internal models for scoring process, not directly part of API output structure from instinct_map_scoring.md Section 2
# but useful for internal calculations and Profile construction.
class SubtypeRawScores(BaseModel):
    subtype_raw: Dict[str, int]          # "Bursty"->4 ...

class InstinctMetrics(BaseModel):
    instinct_mean: Dict[str, float]
    instinct_range: Dict[str, int]
    # Standard deviation will be needed for Growth Edge
    instinct_std_dev: Optional[Dict[str, float]] = None

class FullScoringResult(SubtypeRawScores, InstinctMetrics):
    driver: str
    creation: str
    growth_edge: str
    # Percentiles will be added in v2
    # percentiles: Dict[str,int] 