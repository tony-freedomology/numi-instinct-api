
# NuMi Instinct Map – Scoring Blueprint  
*Version 1.0 — 2025‑06‑02*

---

## 1. Purpose
This document tells an engineer **exactly** how to transform a user’s raw answers from the 100‑item NuMi Instinct Assessment into:

* Raw subtype scores  
* Nine **Driver** instincts + one **Creation** instinct  
* Growth‑edge flags & clash alerts  
* All visual & text output needed for the Instinct Map report (headline label, 9‑box heat‑map, bars, coaching copy keys)

It assumes the engineer already has the three data files delivered earlier:

| File | Role |
|------|------|
| `assessment_questions.csv` | 100 rows → Item → Instinct → Subtype (+ meta columns) |
| `Flowprint_Labels_54.tsv` | Lookup table: Creation × Driver → headline label + signature |
| `Subtype_Glossary.csv` | One‑liners for tooltips & copy generation |

---

## 2. Data Structures

```python
# Pydantic‑style outline
class Response(BaseModel):
    slot: str          # e.g. "ER-1"
    answer: str        # raw text of selected choice

class ItemMeta(BaseModel):
    slot: str
    instinct: str      # e.g. "Energy Rhythm"
    subtype: str       # e.g. "Bursty"
    reverse: bool      # True if Subtype == "Reverse"
    answer_type: str   # "Likert" | "Scenario"
    # scenario_map only for AnswerType=="Scenario"
    scenario_map: dict[str, str] | None  # "A"→"Bursty", ...

class Profile(BaseModel):
    subtype_raw: dict[str, int]          # "Bursty"→4 ...
    instinct_mean: dict[str, float]
    instinct_range: dict[str, int]
    driver: str
    creation: str
    growth_edge: str
```

---

## 3. Item‑Level Scoring

### 3.1 Likert Items  
* Map **Strongly Disagree…Strongly Agree** → **1‑5**.  
* **Endorsement rule**  
  * *Normal items*: **+1** to the target subtype if score ≥ 4.  
  * *Reverse items*: **+1** if score ≤ 2 _(mirror logic)_.  
  * Otherwise **0**.

### 3.2 Scenario Items (`AnswerType == "Scenario"`)  
Each option represents a subtype. Give **+1** to the subtype chosen.

---

## 4. Raw Subtype Scores
Sum endorsements per subtype.

| Instinct | Items | Score Range |
|----------|-------|-------------|
| Energy Rhythm, … Pattern Instinct | 10 | 0 – 10 |
| Social Instinct | 8 | 0 – 8 |
| Creation Instinct | 12 | 0 – 12 |

---

## 5. Instinct‑Level Metrics

For each of the **10 instincts**:

1. **Strength = mean** of its subtype raw scores.  
2. **Range = (max – min)** among its subtypes.

---

## 6. Selecting Key Instincts

### 6.1 Driver Instinct  
* Compute **Adjusted Score = Strength + Range** for the **nine non‑Creation instincts**.  
* Highest Adjusted Score → **Driver**.  
* Tie‑break: larger *Range*.  
* _Yes, Social can win Driver → (6 Creation × 9 Drivers = 54 headline labels)._

### 6.2 Creation Instinct  
Highest raw among the six Creation subtypes. Tie → subtype with largest **z‑score** once norms exist.

### 6.3 Growth Edge  
Instinct with **lowest Strength** *but* **highest st‑dev** between its subtypes.  
Fallback: any instinct where one subtype ≥ 75th pct and its polar opposite ≤ 25th pct.

---

## 7. Normalisation (after 1 k+ completions)

1. Store population means & SDs per subtype.  
2. Convert future raw scores → **z‑scores → percentiles**.  
3. Refresh norms quarterly.

---

## 8. Reliability & QA (batch job)

* Cronbach’s α per instinct; flag < .70.  
* Scenario / Likert cross‑check consistency.  
* Trap items for social desirability (list T‑IDs).

---

## 9. Output Assembly Pipeline

1. Look‑up **Flowprint Label**  

```python
label_row = flow_df[
    (flow_df["Creation Instinct"] == creation) &
    (flow_df["Driver Instinct"]   == driver)
]
headline = label_row["Flowprint Label"].iloc[0]
signature = label_row["Signature Sentence"].iloc[0]
```

2. Build **9‑Box** heat‑map data = percentile bars for each instinct.  
3. Highlight **Driver** (bold border) & **Growth Edge** (orange border).  
4. If |z| > 1.5 between any 2 subtypes in same instinct → “instinct clash” list.  
5. Package into JSON for the front‑end:

```json
{
  "headline": "...",
  "signature": "...",
  "driver": "Energy Rhythm",
  "creation": "Architect",
  "growthEdge": "Environment Response",
  "instinctBars": {
    "Energy Rhythm": {"percentile": 84, "dominantSubtype": "Bursty"},
    "...": "..."
  },
  "clashes": ["Pattern Instinct"],
  "timestamp": "2025-06-02T14:32:00Z"
}
```

---

## 10. Implementation Checklist

- [ ] Import **assessment_questions.csv** and populate `ItemMeta` table (with scenario maps hard‑coded).  
- [ ] Build parser that ingests user answers → `Response[]`.  
- [ ] Apply **Section 3** rules to produce `subtype_raw`.  
- [ ] Derive instinct metrics → pick **Driver / Creation / Growth Edge**.  
- [ ] Plug Creation × Driver into `Flowprint_Labels_54.tsv`.  
- [ ] Convert raw → percentiles once `norms.json` is populated.  
- [ ] Emit the JSON package for UI & PDF generator.

---

## 11. Future‑Proofing

* **Version tags** on every question so future rewrites don’t break historical scores.  
* Telemetry events: _itemLoaded, itemAnswered, formSubmitted, labelGenerated_.  
* AB‑test space available on 5 “experimental” items per release.

---

### Contact
*Product Lead*: Greg  
*Tech Lead*: Tony  
*Data Science*: (TBD)  

---

> “The Instinct Map is that moment you look in a mirror and see yourself—finally—and the reflection tells you **exactly** how to build a life that flows.”
