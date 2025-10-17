from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class SessionPublic(BaseModel):
    id: str
    session_key: str
    user_id: str
    persona_id:Optional[str] = None
    last_msg: Optional[str] = None  # 新增字段
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
