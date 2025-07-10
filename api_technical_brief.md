# NuMi Instinct Map API - Technical Brief for App Integration

*Version 1.1 (Generated: {{CURRENT_DATE}})*

## 1. Introduction

This document provides frontend and mobile engineers with the necessary information to integrate with the NuMi Instinct Map API. This API is responsible for scoring the 100-item NuMi Instinct Assessment and returning a detailed user profile.

### 1.1. API Overview

The API serves as a centralized scoring engine. Client applications (web and mobile) will:
1.  Collect the user's answers to the 100 assessment items.
2.  Send these answers, along with a `user_id`, to the API's `/submit` endpoint using a secure API key.
3.  Receive a JSON object containing the user's scored profile.
4.  Optionally, retrieve a cached profile using the `/user_id` endpoint.

The API handles all scoring logic, including item weighting, reverse-coded items, scenario-based choices, subtype totals, instinct strength calculations, and the determination of key profile aspects like Driver Instinct, Creation Instinct subtype, and Growth Edge.

---

## 2. API Environment & Authentication

### 2.1. API URL

The live API is hosted on Render. The URL will follow this structure:

*   **Base URL:** `https://numi-instinct-api.onrender.com` 

The local development URL remains `http://127.0.0.1:8000`.

### 2.2. Authentication

The API is protected by a secret API key. All requests to protected endpoints must include this key in the `X-API-Key` HTTP header.

*   **Header Name:** `X-API-Key`
*   **Header Value:** The secret API key provided for your application.

**How to get the API Key:**
The API key is managed as an environment variable in the Render dashboard for the `numi-instinct-api` service. You can find it under the **Environment** tab. It will be a securely generated random string.

**Example Request with Authentication:**
```bash
curl -X POST "https://numi-instinct-api.onrender.com/v1/instinct-map/submit" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-secret-api-key-from-render" \
     -d '{
           "user_id": "test-user-001",
           "answers": [
             {"slot": "1A", "answer": "A"},
             {"slot": "1B", "answer": "B"}
           ]
         }'
```

---

## 3. API Endpoints

### 3.1. Submit Assessment Answers

*   **Endpoint:** `POST /v1/instinct-map/submit`
*   **Method:** `POST`
*   **Description:** Submits a user's answers for scoring and profile generation. The generated profile is also cached server-side for a limited time (default 24 hours).
*   **Authentication:** **Required.** See section 2.2 for details.

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

Upon successful processing, the API returns a `Profile` object with the structure detailed in Section 4.

#### Error Responses:
*   `400 Bad Request`: If `user_id` or `answers` are missing or malformed.
*   `403 Forbidden`: If the `X-API-Key` header is missing or contains an invalid key.
*   `422 Unprocessable Entity`: If the request payload doesn't match the expected structure.
*   `500 Internal Server Error`: If an unexpected error occurs during scoring.

### 3.2. Retrieve Cached Profile

*   **Endpoint:** `GET /v1/instinct-map/{user_id}`
*   **Method:** `GET`
*   **Description:** Retrieves a previously calculated and cached Instinct Map profile for a given `user_id`.
*   **Authentication:** **Required.** See section 2.2 for details.

#### Path Parameters:
*   `user_id` (string, required): The unique identifier for the user whose profile is being requested.

#### Response Payload (200 OK - `application/json`):

Returns the `Profile` object if found. See Section 4 for details.

#### Error Responses:
*   `403 Forbidden`: If the `X-API-Key` header is missing or contains an invalid key.
*   `404 Not Found`: If no cached profile exists for the given `user_id`.
*   `422 Unprocessable Entity`: If the `user_id` path parameter is invalid.

---

## 4. Profile Object Details

The following describes each field in the JSON `Profile` object returned by the API.

1.  **`headline`: string**
    *   **Description:** The main, high-level descriptive label for the user's overall Instinct Map profile (e.g., "Sprint Builder").
    *   **Frontend Use:** Display prominently as the user's primary "type" or profile name.

2.  **`signature`: string**
    *   **Description:** A more detailed sentence or short paragraph elaborating on the `headline`.
    *   **Frontend Use:** Display underneath or alongside the headline to provide more personality and context.

3.  **`driver`: string**
    *   **Description:** The name of the user's determined **Driver Instinct** (e.g., `"Energy Rhythm"`).
    *   **Frontend Use:** Highlight as one of their core instincts.

4.  **`creation`: string**
    *   **Description:** The name of the user's determined **Creation Instinct subtype** (e.g., `"Architect"`).
    *   **Frontend Use:** Highlight as their core creative style.

5.  **`growth_edge`: string**
    *   **Description:** The name of the instinct identified as the user's **Growth Edge**.
    *   **Frontend Use:** Point out as an area for potential development.

6.  **`instinct_bars`: object (dictionary)**
    *   **Description:** A dictionary where each key is the name of one of the **10 Instincts**. The value for each instinct contains:
        *   **`percentile`: null** (or number). Currently `null`.
        *   **`dominantSubtype`: string**. The name of the subtype with the highest raw score within that instinct.
    *   **Frontend Use:** For each of the 10 instincts, display this dominant subtype.

7.  **`clashes`: array of strings**
    *   **Description:** Currently always an empty array `[]`.
    *   **Frontend Use:** Can be ignored.

8.  **`timestamp`: string (ISO 8601 format)**
    *   **Description:** The UTC date and time when the profile was calculated.
    *   **Frontend Use:** Can be displayed as "Profile generated on..." or for record-keeping.

9.  **`all_subtype_scores`: object (dictionary)**
    *   **Description:** A dictionary mapping every **subtype** to its calculated **raw score** (integer).
    *   **Example:** `{"Bursty": 5, "Steady": 2, ...}`
    *   **Frontend Use:** This provides the most granular data for detailed dashboards and charts.

10. **`instinct_strengths`: object (dictionary)**
    *   **Description:** A dictionary mapping each of the **10 Instincts** to its calculated **Strength** (float).
    *   **Example:** `{"Energy Rhythm": 3.75, "Input Style": 1.5, ...}`
    *   **Frontend Use:** This is the primary data point to drive the visual length/intensity of bars for each of the 10 main instincts in a summary view.

---

## 5. Frontend Implementation Notes

*   **Store the API Key Securely:** The `X-API-Key` should be stored securely in your app's environment configuration, not hardcoded into the source.
*   **Data for Dashboard:** The `all_subtype_scores` and `instinct_strengths` fields provide the primary data for creating detailed dashboards.
*   **Tooltips/Definitions:** The frontend will need a way to display definitions for instincts and subtypes (e.g., from a local JSON file or a separate API).
*   **Error Handling:** Implement robust error handling for API call failures, especially for `403 Forbidden` in case of an invalid key and `500 Internal Server Error`.
*   **Loading States:** Provide loading indicators while the API call to `/submit` is in progress, as scoring may take a moment. 