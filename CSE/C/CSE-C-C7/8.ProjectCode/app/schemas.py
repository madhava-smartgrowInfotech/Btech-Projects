from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    confirm_password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ProfileIn(BaseModel):
    education: str = ""
    skill_level: str = "Beginner"
    interests: str = ""
    preferred_topics: str = ""
    learning_style: str = "Self-paced"
    goals: str = ""
    course_preferences: str = ""
    weekly_hours: float = 5.0
    age_band: str = "25-34"
    gender: str = "Prefer not to say"

class InteractionIn(BaseModel):
    course_id: str = ""
    event_type: str
    value: float = 1.0

class RefreshIn(BaseModel):
    top_n: int = 8
