import re
from typing import Optional

from pydantic import BaseModel, field_validator


class ChatReq(BaseModel):
    instruction: str
    session_id: str = "default"
    user_id:Optional[str] = None

    @field_validator('instruction')
    @classmethod
    def validate_instruction(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Instruction cannot be empty')
        if len(v) > 20000:
            raise ValueError('Instruction too long')
        return v.strip()

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        if not v:
            raise ValueError('Session ID is required')
        pattern = r'^session_\d+_[a-z0-9]+_[A-Za-z0-9+/]{8}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid session ID format')
        return v