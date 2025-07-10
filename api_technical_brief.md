# NuMi Instinct Map API - Technical Brief for Frontend Engineers

*Version 1.0 (Generated: {{CURRENT_DATE}})*

## 1. Introduction

This document provides frontend engineers with the necessary information to integrate with the NuMi Instinct Map API. This API is responsible for scoring the 100-item NuMi Instinct Assessment and returning a detailed user profile.

### 1.1. Purpose of the Assessment

The NuMi Instinct Assessment helps users understand their innate tendencies across 10 core instincts. By identifying their dominant patterns and potential areas for growth, users can gain insights into how they naturally approach various aspects of life, such as energy management, information processing, decision-making, and creation. The goal is to empower users to build a life that aligns with their natural wiring, leading to greater flow and fulfillment.

### 1.2. API Overview

The API serves as a centralized scoring engine. Frontends (web and mobile applications) will:
1.  Collect the user's answers to the 100 assessment items.
2.  Send these answers, along with a `user_id`, to the API's `/submit` endpoint.
3.  Receive a JSON object containing the user's scored profile.
4.  Optionally, retrieve a cached profile using the `/user_id` endpoint.

The API handles all scoring logic, including item weighting, reverse-coded items, scenario-based choices, subtype totals, instinct strength calculations, and the determination of key profile aspects like Driver Instinct, Creation Instinct subtype, and Growth Edge.

---

## 2. API Endpoints

**Base URL:** (To be determined by deployment, e.g., `https://api.numi.one`)
**Local Development URL:** `http://127.0.0.1:8000`

### 2.1. Submit Assessment Answers

*   **Endpoint:** `POST /v1/instinct-map/submit`
*   **Method:** `POST`
*   **Description:** Submits a user's answers for scoring and profile generation. The generated profile is also cached server-side for a limited time (default 24 hours).
*   **Authentication:** For production, this endpoint should ideally be protected. The frontend should send a JWT obtained from Supabase upon user login. The API can then be configured to validate this token. (Current version does not enforce JWT validation but expects `user_id`).

#### Request Payload (`application/json`):

```json
{
  "user_id": "string", // Required. Unique identifier for the user (e.g., Supabase user UUID).
  "answers": [
    {
      "slot": "string",  // Required. The unique identifier for the assessment item (e.g., "ER-1", "IS-6").
      "answer": "string" // Required. The user's raw answer.
                       // For Likert items: "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree".
                       // For Scenario items: The chosen option key (e.g., "A", "B", "C", "D").
    }
    // ... (array should contain 100 answer objects for a complete assessment)
  ]
}
```

#### Response Payload (200 OK - `application/json`):

Upon successful processing, the API returns a `Profile` object with the following structure (detailed in Section 3):

```json
// See Section 3 for detailed field descriptions
{
  "headline": "string",
  "signature": "string",
  "driver": "string",
  "creation": "string",
  "growth_edge": "string",
  "instinct_bars": { /* ... */ },
  "clashes": [],
  "timestamp": "string",
  "all_subtype_scores": { /* ... */ },
  "instinct_strengths": { /* ... */ }
}
```

#### Error Responses:
*   `400 Bad Request`: If `user_id` or `answers` are missing or malformed (e.g., empty answers list).
*   `422 Unprocessable Entity`: If the request payload doesn't match the expected Pydantic model structure (e.g., incorrect data types). FastAPI handles this automatically.
*   `500 Internal Server Error`: If an unexpected error occurs during scoring.

### 2.2. Retrieve Cached Profile

*   **Endpoint:** `GET /v1/instinct-map/{user_id}`
*   **Method:** `GET`
*   **Description:** Retrieves a previously calculated and cached Instinct Map profile for a given `user_id`.
*   **Authentication:** Similar to the submit endpoint, this should ideally be protected in production.

#### Path Parameters:
*   `user_id` (string, required): The unique identifier for the user whose profile is being requested.

#### Response Payload (200 OK - `application/json`):

Returns the `Profile` object (see Section 3 for details) if found.

```json
// See Section 3 for detailed field descriptions
{
  "headline": "string",
  "signature": "string",
  "driver": "string",
  "creation": "string",
  "growth_edge": "string",
  "instinct_bars": { /* ... */ },
  "clashes": [],
  "timestamp": "string",
  "all_subtype_scores": { /* ... */ },
  "instinct_strengths": { /* ... */ }
}
```

#### Error Responses:
*   `400 Bad Request`: If `user_id` is not provided in the path.
*   `404 Not Found`: If no cached profile exists for the given `user_id`.
*   `422 Unprocessable Entity`: If the `user_id` path parameter is invalid.

---

## 3. Profile Object Details

The following describes each field in the JSON `Profile` object returned by the API.

1.  **`headline`: string**
    *   **Description:** The main, high-level descriptive label for the user's overall Instinct Map profile (e.g., "Sprint Builder"). Derived from the combination of their `creation` instinct subtype and their `driver` instinct via the `Flowprint_Labels_54.tsv` lookup table.
    *   **Frontend Use:** Display prominently as the user's primary "type" or profile name.

2.  **`signature`: string**
    *   **Description:** A more detailed sentence or short paragraph elaborating on the `headline` (e.g., "You channel burst-mode energy to architect systems that stand the test of time..."). Also from `Flowprint_Labels_54.tsv`.
    *   **Frontend Use:** Display underneath or alongside the headline to provide more personality and context.

3.  **`driver`: string**
    *   **Description:** The name of the user's determined **Driver Instinct** (e.g., `"Energy Rhythm"`, `"Input Style"`). This is one of the nine non-Creation instincts that most strongly characterizes their general approach.
    *   **Frontend Use:** Highlight as one of their core instincts. Use for specific descriptions or coaching related to this Driver.

4.  **`creation`: string**
    *   **Description:** The name of the user's determined **Creation Instinct subtype** (e.g., `"Architect"`, `"Storyteller"`). This describes their primary mode of creating or bringing things into the world.
    *   **Frontend Use:** Highlight as their core creative style. Use for specific descriptions or coaching related to this Creation subtype.

5.  **`growth_edge`: string**
    *   **Description:** The name of the instinct identified as the user's **Growth Edge**. (v1 logic: lowest Strength AND highest standard deviation between its subtypes).
    *   **Frontend Use:** Point out as an area for potential development or awareness. Descriptions for this instinct can be framed as growth opportunities.

6.  **`instinct_bars`: object (dictionary)**
    *   **Description:** A dictionary where each key is the name of one of the **10 Instincts** (e.g., `"Energy Rhythm"`, `"Input Style"`, ..., `"Creation Instinct"`). The value for each instinct is another dictionary containing:
        *   **`percentile`: null (or number)**
            *   **v1:** Always `null`.
            *   **Future:** Will hold the user's percentile score (0-100) for that instinct once norming data is available.
            *   **Frontend Use (v1):** Since `percentile` is null, hide numeric percentile labels. Bars can be scaled based on the `instinct_strengths` field (see below) to represent raw strength (typically 0-10 range).
        *   **`dominantSubtype`: string (or null)**
            *   The name of the subtype with the highest raw score within that instinct. If all subtypes score 0, it's the first subtype from the glossary for that instinct (tie-breaker).
            *   **Frontend Use:** For each of the 10 instincts, display this dominant subtype (e.g., "Within Energy Rhythm, your dominant tendency is Bursty."). This is key for a multi-faceted profile view.

7.  **`clashes`: array of strings**
    *   **Description:**
        *   **v1:** Always an empty array `[]`.
        *   **Future:** Will list names of instincts where the user has a significant internal "clash" (e.g., very high score in one subtype and very low in its polar opposite within the same instinct, based on z-scores).
    *   **Frontend Use (v1):** Can be ignored or a note like "No significant internal clashes detected at this stage."

8.  **`timestamp`: string (ISO 8601 format)**
    *   **Description:** The UTC date and time when the profile was calculated (e.g., `"2025-06-03T17:18:45.355792+00:00"`).
    *   **Frontend Use:** Can be displayed as "Profile generated on..." or for record-keeping.

9.  **`all_subtype_scores`: object (dictionary)**
    *   **Description:** A dictionary where each key is the name of a defined **subtype** (e.g., `"Bursty"`, `"Steady"`, `"Analyzer"`, `"Architect"`) across all instincts, and the value is its calculated **raw score** (integer, typically 0-10, but can vary per instinct based on number of items).
    *   **Example:** `{"Bursty": 5, "Steady": 2, "Cyclical": 0, ...}`
    *   **Frontend Use:** This provides the most granular data. Use this to:
        *   Render detailed bar charts showing the scores for *all* subtypes within each instinct.
        *   Allow users to see their specific scores for non-dominant subtypes.
        *   Build rich, interactive dashboards exploring the nuances of their profile.

10. **`instinct_strengths`: object (dictionary)**
    *   **Description:** A dictionary where each key is the name of one of the **10 Instincts**, and the value is its calculated **Strength** (float, typically in a 0-10 range, representing the mean of its subtype scores).
    *   **Example:** `{"Energy Rhythm": 3.75, "Input Style": 1.5, ...}`
    *   **Frontend Use:** This is the primary data point to drive the visual length/intensity of bars for each of the 10 main instincts in a summary dashboard view, as per the original spec ("UI will scale bars off raw Strength (0-10)").

---

## 4. Frontend Implementation Notes

*   **Data for Dashboard:** The `all_subtype_scores` and `instinct_strengths` fields provide rich data for creating detailed dashboards. The `dominantSubtype` within `instinct_bars` gives a quick summary for each instinct.
*   **Displaying Instincts:** It's recommended to display all 10 instincts, showing the user's `dominantSubtype` within each and a visual representation of the `instinct_strengths`.
*   **Tooltips/Definitions:** The frontend will need access to the `Subtype_Glossary.csv` content (or a JSON version of it) to display definitions for instincts and subtypes when a user hovers over or clicks on them.
*   **Error Handling:** Implement appropriate error handling for API call failures (network errors, 4xx/5xx responses).
*   **Loading States:** Provide loading indicators while the API call to `/submit` is in progress, as scoring might take a moment.

---

This brief should provide a solid foundation for integrating with the NuMi Instinct Map API. Please refer to the Pydantic models in `models.py` in the API codebase for the canonical schema definitions. 