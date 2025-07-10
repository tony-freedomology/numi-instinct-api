from fastapi import FastAPI, HTTPException, Body, Depends
from typing import List, Dict
import logging

from models import UserAnswer, Profile # Pydantic models
from scoring_engine import score_answers
from profile_store import profile_store_instance, ProfileStore
# data_loader and config are implicitly loaded/used by scoring_engine and profile_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NuMi Instinct Map API",
    version="1.0.0",
    description="API for submitting NuMi Instinct Assessment answers and retrieving profiles."
)

# Dependency for profile store (allows for easier testing and future replacement)
async def get_profile_store() -> ProfileStore:
    return profile_store_instance

@app.post("/v1/instinct-map/submit", response_model=Profile)
async def submit_assessment(
    user_id: str = Body(..., embed=True, description="Unique identifier for the user"), 
    answers: List[UserAnswer] = Body(..., embed=True, description="List of user answers to assessment questions"),
    store: ProfileStore = Depends(get_profile_store)
):
    """
    Accepts a user's 100 answers to the NuMi Instinct Assessment, 
    scores them, and returns the JSON profile. The profile is also cached.
    """
    logger.info(f"Received submission for user_id: {user_id} with {len(answers)} answers.")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required.")
    if not answers or len(answers) == 0: # Basic check, could be more specific e.g. == 100
        raise HTTPException(status_code=400, detail="Answers list cannot be empty.")
    
    # Validate number of answers if required (e.g. must be 100)
    # For now, proceeding if any answers are provided.
    # num_expected_questions = len(ITEM_META_DICT) # from data_loader
    # if len(answers) != num_expected_questions:
    #     logger.warning(f"User {user_id} submitted {len(answers)} answers, expected {num_expected_questions}.")
        # Depending on strictness, could raise HTTPException here

    try:
        # Score the answers
        profile_data = score_answers(answers)
        
        # Save/cache the profile
        store.save_profile(user_id, profile_data)
        logger.info(f"Profile calculated and cached for user_id: {user_id}")
        
        return profile_data
    except Exception as e:
        logger.error(f"Error processing submission for user_id {user_id}: {str(e)}", exc_info=True)
        # Consider what type of error to return. 
        # If it's a data validation issue with answers, could be 400 or 422.
        # If it's an internal server error during scoring, 500.
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing the assessment: {str(e)}")

@app.get("/v1/instinct-map/{user_id}", response_model=Profile)
async def get_assessment_profile(
    user_id: str,
    store: ProfileStore = Depends(get_profile_store)
):
    """
    Retrieves a previously calculated and cached Instinct Map profile for a given user_id.
    """
    logger.info(f"Attempting to retrieve profile for user_id: {user_id}")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id path parameter is required.")

    profile = store.get_profile(user_id)
    
    if profile:
        logger.info(f"Profile found for user_id: {user_id}")
        return profile
    else:
        logger.warning(f"Profile not found for user_id: {user_id}")
        raise HTTPException(status_code=404, detail="Profile not found for the given user_id. Please submit the assessment first.")

# A simple root endpoint for health check or basic info
@app.get("/")
async def root():
    return {"message": "Welcome to the NuMi Instinct Map API. See /docs for details."}

# It might be useful to add a startup event to pre-load data if not already handled by module-level calls
# in data_loader.py. However, data_loader.py already loads data when imported.
# @app.on_event("startup")
# async def startup_event():
#     logger.info("Application startup: Pre-loading assessment data...")
#     # This will trigger the lru_cache in data_loader
#     load_assessment_questions()
#     load_flowprint_labels()
#     load_subtype_glossary()
#     load_scenario_mapping()
#     get_instinct_to_subtypes_map()
#     logger.info("Assessment data loaded.")

if __name__ == "__main__":
    import uvicorn
    # Ensure the data directory is correctly located relative to this main.py if not using NUMI_DATA_PATH
    # This is more for local dev; in Docker, paths should be set up correctly.
    # from config import DATA_PATH # To print and check
    # print(f"Using DATA_PATH: {DATA_PATH}")
    uvicorn.run(app, host="0.0.0.0", port=8000) 