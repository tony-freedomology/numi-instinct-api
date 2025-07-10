
# NuMi Instinct Assessment — Engineer On‑Boarding Guide  
*Generated 2025‑06‑02*

---

## 0. TL;DR
You are about to turn a 100‑item psychometric assessment into a production feature inside the NuMi mobile & web apps.  
All the heavy research (question list, scoring rules, output schema) is locked.  
Your mission: **deliver an end‑to‑end pipeline** that (1) presents the items, (2) stores responses, (3) scores them exactly as specified, and (4) serves the Instinct Map JSON for our UI & PDF generator.

Everything you need lives in four source files plus this doc:

| File | Purpose |
|------|---------|
| `assessment_questions.csv` | 100 rows → Item → Instinct → Subtype (+ meta columns) |
| `Flowprint_Labels_54.tsv` | Lookup table: Creation × Driver → headline label + signature |
| `Subtype_Glossary.csv` | One‑liner definitions for every subtype (tooltips & copy). |
| `instinct_map_scoring.md` | Scoring blueprint (algorithms, maths, QA checks). |

---

## 1. High‑Level Flow

```mermaid
graph TD
  A[Client UI\n(question form)] -->|answers[]| B(API: /submit)
  B --> C[Scoring Service]
  C -->|JSON profile| D[Client UI\n(report screen)]
  C -->|PDF payload| E[Generator]
  C -->|events| F[Analytics/Warehouse]
```

1. **User completes form** → local array of `{slot, answer}`.  
2. **/submit** endpoint validates & forwards to Scoring service.  
3. **Scoring service** does all work in `instinct_map_scoring.md`.  
4. Returns compact JSON → UI renders 9‑box, bars, copy.  
5. Same JSON drives PDF render and long‑form email.

---

## 2. Data Models (canonical Python)

```python
class ItemMeta(BaseModel):
    slot: str              # "ER-1"
    instinct: str          # "Energy Rhythm"
    subtype: str           # "Bursty"
    reverse: bool          # True if subtype == "Reverse"
    answer_type: str       # "Likert" | "Scenario"
    scenario_map: dict[str, str] | None  # for scenarios

class UserAnswer(BaseModel):
    slot: str
    answer: str            # raw text or key ("A")

class Profile(BaseModel):
    subtype_raw: dict[str,int]
    instinct_strength: dict[str,float]
    instinct_range: dict[str,int]
    driver: str
    creation: str
    growth_edge: str
    percentiles: dict[str,int]
    headline: str
    signature: str
    clashes: list[str]
```

---

## 3. Scoring Logic (summary)

*Use `instinct_map_scoring.md` for full detail.*

| Stage | What happens |
|-------|--------------|
| Item → Subtype | +1 endorsement if Likert ≥4 (≤2 for Reverse) or Scenario choice. |
| Raw Subtype Totals | Sum (0‑10, Social 0‑8, Creation 0‑12). |
| Instinct Strength & Range | Mean & span of its subtypes. |
| Driver | Highest **Strength + Range** among 9 non‑Creation instincts. |
| Creation | Highest raw among six creation subtypes. |
| Growth Edge | Lowest Strength **and** highest σ. |
| Percentiles | Map raw totals to norms once ≥1 k users. |
| Output | Flowprint label lookup; emit JSON contract. |

---

## 4. UX Requirements

* **Form**: one item per screen (mobile) or 5‑pack (desktop) with progress bar.  
* **Scenario items** render A‑D radio blocks; Likert = 5‑point buttons.  
* **Hard cookie save** after each answer (resume protection).  
* **Total time** ≤ 8 min @ 100 items.

---

## 5. API Contract

### POST `/v1/instinct-map/submit`

```json
{
  "user_id": "uuid",
  "answers": [{"slot":"ER-1", "answer":"Strongly Agree"}, …]
}
```

Returns **200** with payload:

```json
{
  "profile": { /* see scoring doc example */ }
}
```

### GET `/v1/instinct-map/{user_id}`  
Returns cached profile (for share links / PDF).

---

## 6. Milestones

| # | Deliverable | Notes |
|---|-------------|-------|
| 0 | Repo bootstrap | FastAPI + Poetry. |
| 1 | Ingest `assessment_questions.csv` → ItemMeta | Unit tests for mapping. |
| 2 | Scoring engine | Use golden‑path fixtures. |
| 3 | REST endpoints | Auth middleware placeholder. |
| 4 | Front‑end survey flow | Tailwind + Zustand state. |
| 5 | Report UI | 9‑box heat‑map, bars, copy. |
| 6 | PDF generator | Puppeteer/WeasyPrint. |
| 7 | Norms & reliability job | Cron + warehouse export. |
| 8 | Beta flag & logging | Collect ≥1 k completions. |

---

## 7. Initial Prompt for the LLM Engineer

```prompt
You are the NuMi Instinct Map full‑stack engineer.

Context files mounted at /mnt/data:
  • assessment_questions.csv
  • Flowprint_Labels_54.tsv
  • Subtype_Glossary.csv
  • instinct_map_scoring.md

Goal: create a micro‑service that accepts a user’s 100 answers, scores them exactly per instinct_map_scoring.md, and returns the JSON profile contract.

Your first tasks:
1. Load assessment_questions.csv and build the ItemMeta mapping (identify reverse items, scenario option → subtype maps).
2. Implement item‑level scoring, raw subtype totals, instinct strength/range, Driver, Creation, Growth‑Edge selection.
3. Validate with unit tests using the sample answer sets (all agree, all disagree, mixed).
4. Expose POST /v1/instinct-map/submit and GET /v1/instinct-map/{user_id}.
5. Return JSON identical to the example in Section 5.
6. Ask clarifying questions only if the spec blocks you; otherwise proceed.

Do **not** change any text of the questions or scoring math. When in doubt, reference instinct_map_scoring.md.
```

Copy the above block into your chat with the engineer to spin them up immediately.

---

## 8. Slack Channels

* **#instinct‑product** – wording & copy.  
* **#instinct‑eng** – code, CI, deploy.  
* **#instinct‑science** – psychometrics & stats.

---

Happy building!  
