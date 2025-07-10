# NuMi Instinct Map API

This project implements the backend microservice for the NuMi Instinct Map assessment.
It provides an API to submit user answers and retrieve their scored psychological profile.

## Project Structure

```
/
├── app/
│   ├── data/                     # CSV/TSV data files (assessment questions, mappings)
│   │   ├── assessment_questions.csv
│   │   ├── Flowprint_Labels.tsv
│   │   ├── scenario_mapping.json
│   │   └── Subtype_Glossary.csv
│   ├── tests/                    # Unit tests
│   │   └── test_scoring_engine.py
│   ├── config.py                 # Configuration settings (paths, constants)
│   ├── data_loader.py            # Loads and prepares all static data
│   ├── main.py                   # FastAPI application, API endpoints
│   ├── models.py                 # Pydantic data models
│   ├── profile_store.py          # Profile caching (in-memory)
│   └── scoring_engine.py         # Core scoring logic
├── requirements.txt            # Python package dependencies
└── README.md                   # This file
```

(Note: The `app/` subdirectory is conceptual for organization if deploying as a module or within a larger structure. For a simple FastAPI service, these files might live at the root alongside `main.py` if preferred, with `DATA_PATH` in `config.py` adjusted accordingly. The current setup assumes `main.py` and other .py files are at the root, and `data/` is a subdirectory at that same root level.)

## Setup and Running

1.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the FastAPI application:**
    ```bash
    uvicorn main:app --reload
    ```
    The application will typically be available at `http://127.0.0.1:8000`.
    API documentation (Swagger UI) will be at `http://127.0.0.1:8000/docs`.

4.  **Environment Variables:**
    *   `NUMI_DATA_PATH`: (Optional) Absolute path to the `data` directory if it's not in the default location (`./data/` relative to where the app is run).
    *   `NUMI_PROFILE_TTL_SECONDS`: (Optional) TTL for cached profiles in seconds. Defaults to 86400 (24 hours).

## Running Tests

To run the unit tests:

1.  Ensure you are in the project root directory with the virtual environment activated.
2.  Run the tests using Python's `unittest` module:
    ```bash
    python -m unittest discover -s tests
    ```
    Or, to run a specific test file:
    ```bash
    python -m unittest tests.test_scoring_engine
    ```

## API Endpoints

*   **`POST /v1/instinct-map/submit`**: Submits assessment answers.
    *   **Request Body**: 
        ```json
        {
          "user_id": "string",
          "answers": [
            {
              "slot": "string",
              "answer": "string"
            }
          ]
        }
        ```
    *   **Response**: `Profile` JSON object.

*   **`GET /v1/instinct-map/{user_id}`**: Retrieves a cached profile.
    *   **Response**: `Profile` JSON object or 404 if not found.

## Data Files

Located in the `data/` directory (or `NUMI_DATA_PATH`):

*   `assessment_questions.csv`: The 100 assessment items, their instincts, subtypes, and answer types.
*   `scenario_mapping.json`: Maps options (A,B,C,D) of scenario questions to specific subtypes.
*   `Flowprint_Labels.tsv`: Lookup table for Creation Instinct × Driver Instinct → Headline Label & Signature Sentence.
*   `Subtype_Glossary.csv`: Definitions for each subtype.

These files are loaded into memory when the application starts. 