from __future__ import annotations
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import select, update

from src.db.db import db_manager
from src.db.models import User, ChatSession, ChatMessage
from src.schemas.user import UserCreate, UserUpdate
from src.utils.security import get_password_hash

async def get_user(user_id: str) -> Optional[User]:
    """根据ID获取用户"""
    async with db_manager.session as session:
        return await session.get(User, user_id) # session.get() 是 SQLAlchemy 的主键查询方法

async def get_user_by_email(email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    if not email:  # 添加空值检查
        return None
    async with db_manager.session as session:
        stmt = select(User).where(User.email == email) # stmt是“statement”的缩写
        return (await session.execute(stmt)).scalar_one_or_none()

async def get_user_by_username(username: str) -> Optional[User]:
    """根据用户名获取用户"""
    async with db_manager.session as session:
        stmt = select(User).where(User.username == username)
        return (await session.execute(stmt)).scalar_one_or_none()

async def create_user(user_in: UserCreate) -> User:
    """创建新用户"""
    hashed_password = get_password_hash(user_in.password)
    user = User(
        username=user_in.username,
        email=user_in.email,
        display_name=user_in.display_name,
        hashed_password=hashed_password,
        last_login_at=datetime.now(timezone.utc)  # 使用UTC时间
    )
    async with db_manager.session as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

async def update_user(user_id: str, user_in: UserUpdate) -> Optional[User]:
    """更新用户信息"""
    update_data = user_in.model_dump(exclude_unset=True) #exclude_unset=True 参数：只包含那些明确设置了值的字段；排除那些使用默认值或未设置的字段
    if not update_data:
        return await get_user(user_id) # 没有要更新的字段，直接返回当前用户

    async with db_manager.session as session:
        stmt = update(User).where(User.id == user_id).values(**update_data)
        result = await session.execute(stmt)
        if result.rowcount == 0:
            return None # 用户不存在
        await session.commit()
    
    return await get_user(user_id)

async def update_last_login(user_id: str) -> None:
    """更新用户最后登录时间"""
    async with db_manager.session as session:
        stmt = update(User).where(User.id == user_id).values(last_login_at=datetime.now(timezone.utc))
        await session.execute(stmt)
        await session.commit()

async def get_chat_sessions(user_id: str) -> List[ChatSession]:
    """获取用户所有对话"""
    async with db_manager.session as session:
        result = await session.execute(
            select(ChatSession, ChatMessage.content)
            .outerjoin(ChatMessage, ChatSession.last_msg_id == ChatMessage.id)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        sessions = []
        for session_row, last_msg in result:
            session_row.last_msg = last_msg
            sessions.append(session_row)
        return sessions