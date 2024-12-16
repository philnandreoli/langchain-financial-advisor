from pydantic import BaseModel, Field
from typing import List
from .question_answer import QuestionAnswer
from datetime import datetime

class InvestmentProfileRequest(BaseModel):
    investment_profile_answers: List[QuestionAnswer] = Field(..., title="investment_profile_answers", description="The answers to the investment profile questions")
    investment_profile_total_score: int = Field(..., title="investment_profile_total_score", description="The total score of the investment profile")

class InvestmentProfile(BaseModel):
    investment_profile_answers: List[QuestionAnswer] = Field(..., title="investment_profile_answers", description="The answers to the investment profile questions")
    investment_profile_total_score: int = Field(..., title="investment_profile_total_score", description="The total score of the investment profile")
    created_at: datetime = Field(..., title="created_at", description="The date and time the investment profile was created")
    updated_at: datetime = Field(..., title="updated_at", description="The date and time the investment profile was last updated")

class UserProfile(BaseModel):
    email_address: str = Field(..., title="email_address", description="The email address of the user")
    investment_profile: InvestmentProfile = Field(..., title="investment_profile", description="The investment profile of the user")
    created_at: datetime = Field(..., title="created_at", description="The date and time the user profile was created")
    updated_at: datetime = Field(..., title="updated_at", description="The date and time the user profile was last updated")

class UserProfileRequest(BaseModel):
    email_address: str = Field(..., title="email_address", description="The email address of the user")
    investment_profile: InvestmentProfileRequest = Field(..., title="investment_profile", description="The investment profile of the user")