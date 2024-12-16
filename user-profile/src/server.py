import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
from .models.user_profile import UserProfile, UserProfileRequest, InvestmentProfile, InvestmentProfileRequest
from dotenv import load_dotenv
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi_azure_auth import MultiTenantAzureAuthorizationCodeBearer
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

load_dotenv(override=True)
configure_azure_monitor(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"),
    enable_live_metrics=True
)

class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = [os.getenv("CORS_URL")]
    OPENAPI_CLIENT_ID: str = ""
    APP_CLIENT_ID: str = "" 
    

ENVIRONMENT=os.getenv("ENVIRONMENT")

if ENVIRONMENT != "DEVELOPMENT":
    swagger_ui_oauth2_redirect_url = "/oauth2-redirect"
    swagger_ui_init_oauth = {
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': os.getenv("OPENAPI_CLIENT_ID")
    }
else:
    swagger_ui_oauth2_redirect_url = None
    swagger_ui_init_oauth = None

settings = Settings()
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Load OpenID config on startup
    """
    await azure_scheme.openid_config.load_config()
    yield

app = FastAPI(
    title="User Profile API",
    version="1.0",
    description="API to manage a users profile along with their investment profile",
    swagger_ui_oauth2_redirect_url=swagger_ui_oauth2_redirect_url,
    swagger_ui_init_oauth=swagger_ui_init_oauth
)

FastAPIInstrumentor.instrument_app(app)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

azure_scheme = MultiTenantAzureAuthorizationCodeBearer(
    app_client_id=os.getenv("APP_CLIENT_ID"),
    scopes={
        f"api://{settings.APP_CLIENT_ID}/user_impersonation": "user_impersonation",
    },
    validate_iss=False,
    allow_guest_users=True
)

dependencies = [Security(azure_scheme)] if ENVIRONMENT != "DEVELOPMENT" else []


client = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))
db = client.users
collection = db.user_profile

def map_investment_profile_request_to_investment_profile(investment_profile_request: InvestmentProfileRequest) -> InvestmentProfile:
    return InvestmentProfile(
        investment_profile_answers=investment_profile_request.investment_profile_answers,
        investment_profile_total_score=investment_profile_request.investment_profile_total_score,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

def map_user_profile_request_to_user_profile(user_profile_request: UserProfileRequest) -> UserProfile:
    return UserProfile(
        email_address=user_profile_request.email_address,
        investment_profile=map_investment_profile_request_to_investment_profile(user_profile_request.investment_profile),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

def map_document_to_user_profile(document: dict) -> UserProfile:
    return UserProfile(
        email_address=document.get("email_address"),
        investment_profile=InvestmentProfile(
            investment_profile_answers=document.get("investment_profile").get("investment_profile_answers"),
            investment_profile_total_score=document.get("investment_profile").get("investment_profile_total_score"),
            created_at=document.get("investment_profile").get("created_at"),
            updated_at=document.get("investment_profile").get("updated_at")
        ),
        created_at=document.get("created_at"),
        updated_at=document.get("updated_at")
    )


@app.get("/api/userprofile/{email_address}/investmentprofile", response_model=InvestmentProfile, dependencies=dependencies)
async def get_investment_profile(email_address: str):
    """
    Retrieve the investment profile for a user identified by email address.

    This endpoint retrieves the investment profile of a user based on their email address.
    If the user profile does not exist, it raises a 404 error.

    Args:
        email_address (str): The email address of the user whose investment profile is to be retrieved.

    Returns:
        dict: A dictionary containing the investment profile of the user.
    """
    # Retrieve the user profile from the database
    response = collection.find_one({"email_address": email_address})

    # If the user profile does not exist, raise a 404 error
    if not response:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    user_profile = map_document_to_user_profile(response)

    # Return the investment profile of the user
    return user_profile.investment_profile.model_dump()

@app.post("/api/userprofile/", dependencies=dependencies)
async def post_investment_profile(user_profile_request: UserProfileRequest):
    """
    Create a new user profile with an investment profile.

    This endpoint creates a new user profile with the provided investment profile data.
    If a user profile with the same email address already exists, it raises a 400 error.

    Args:
        user_profile_request (UserProfileRequest): The user profile data including the investment profile.

    Returns:
        dict: A dictionary containing the ID of the newly created user profile.
    """
    # Map the request data to a UserProfile instance
    user_profile = map_user_profile_request_to_user_profile(user_profile_request)
    
    # Check if a user profile with the same email address already exists
    user_profile_exist = collection.find_one({"email_address": user_profile.email_address})
    if user_profile_exist:
        raise HTTPException(status_code=400, detail="User profile already exists")
    
    # Convert the UserProfile instance to a dictionary
    user_profile_dict = user_profile.model_dump()

    # Insert the new user profile into the database
    result = collection.insert_one(user_profile_dict)

    # Return the ID of the newly created user profile
    return {"id": str(result.inserted_id)}

@app.patch("/api/userprofile/{email_address}/investmentprofile", dependencies=dependencies)
async def patch_investment_profile(email_address: str, investment_profile_request: InvestmentProfileRequest):
    """
    Update the investment profile for a user identified by email_address.

    This endpoint allows partial updates to the investment profile of a user.
    It retrieves the existing user profile, updates the investment profile answers,
    total score, and the updated_at timestamp, and then saves the changes back to the database.

    Args:
        email_address (str): The email address of the user whose investment profile is to be updated.
        investment_profile_request (InvestmentProfileRequest): The new investment profile data.

    Returns:
        dict: A dictionary containing the number of modified documents.
    """
    # Retrieve the existing user profile from the database
    user_profile_document = collection.find_one({"email_address": email_address})
    
    # If the user profile does not exist, raise a 404 error
    if not user_profile_document:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Map the document to a UserProfile object
    user_profile = map_document_to_user_profile(user_profile_document)

    # Update the investment profile with the new data
    user_profile.investment_profile.investment_profile_answers = investment_profile_request.investment_profile_answers
    user_profile.investment_profile.investment_profile_total_score = investment_profile_request.investment_profile_total_score
    user_profile.investment_profile.updated_at = datetime.now(timezone.utc)

    # Convert the updated investment profile to a dictionary
    investment_profile_dict = user_profile.investment_profile.model_dump()
    
    # Update the user profile in the database
    result = collection.update_one(
        {"email_address": email_address}, 
        {"$set": {"investment_profile": investment_profile_dict, "updated_at": datetime.now(timezone.utc)}}
    )

    # Return the number of modified documents
    return {"modified_count": result.modified_count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7500)