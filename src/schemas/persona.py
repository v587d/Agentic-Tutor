from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel

from src.schemas.profile import ProfileConfig

class PersonaCreate(BaseModel):
    name: str
    tags: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    is_default: bool = True

class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    tags: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None

class PersonaPublic(BaseModel):
    id: str
    user_id: str
    name: str
    tags: Optional[str] = None
    profile: ProfileConfig
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
