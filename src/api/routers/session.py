from typing import List

from fastapi import APIRouter, HTTPException, status, Depends

from src.db.models import User
from src.schemas.session import SessionPublic
from src.api.routers.auth import get_current_user
from src.repositories import user_repo, chat_repo

router = APIRouter(prefix="/session", tags=["session"])

@router.get("/uid/{user_id}", response_model=List[SessionPublic], status_code=status.HTTP_200_OK)
async def get_chat_sessions(
    user_id: str, 
    current_user: User = Depends(get_current_user)
):
    """获取用户的所有会话"""
    sessions = await user_repo.get_chat_sessions(current_user.id)
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Chat sessions Not Found!"
        )
    return [SessionPublic.model_validate(sess) for sess in sessions]

@router.get("/msgs/{session_id}", status_code=status.HTTP_200_OK)
async def get_chat_messages(
    session_id: str, 
    current_user: User = Depends(get_current_user)
):
    """获取会话中的消息"""
    messages = await chat_repo.get_chat_messages_by_sid(session_id)
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Chat messages Not Found!"
        )
    return messages