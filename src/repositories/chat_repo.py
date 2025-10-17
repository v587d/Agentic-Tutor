from __future__ import annotations
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update

from src.db.db import db_manager
from src.db.models import ChatSession, ChatMessage

async def get_or_create_session(
    session_key: str,
    user_id: Optional[str] = None,
    # persona_id: Optional[str] = None,
) -> ChatSession:
    """
    获取或创建一个新的会话
    该函数用于根据session_key查找已存在的会话，如果不存在则创建一个新的会话。
    参数:
        session_key: 会话的唯一标识符
        agent_name: AI代理的名称
        model_name: 使用的AI模型名称
        user_id: 可选，用户标识符
        persona_id: 可选，用户画像标识符
    返回:
        ChatSession: 返回会话对象，可能是新创建的或已存在的
    """
    async with db_manager.session as session:
        result = await session.execute(
            select(ChatSession).where(ChatSession.session_key == session_key)
        )
        row = result.scalar_one_or_none()

        if row is None:
            row = ChatSession(
                session_key=session_key,
                user_id=user_id,
                # persona_id=persona_id,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return row


async def add_message(
    session_pk: str,  # 会话的主键ID，用于标识消息所属的会话
    role: str,  # 消息发送者的角色，例如"user"、"assistant"等
    content: str,  # 消息的具体内容
    name: Optional[str] = None,  # content的前10个字符
    input_tokens: Optional[int] = None,  
    output_tokens: Optional[int] = None,  
    response_time: Optional[float] = None,  
    meta: Optional[Dict[str, Any]] = None,  # 可选参数，包含消息的元数据，以字典形式存储
) -> ChatMessage:  # 返回类型为ChatMessage对象，表示添加到数据库的消息记录

    """
    异步添加一条消息到数据库的函数

    该函数使用异步方式将消息记录添加到数据库中，包括提交事务和刷新对象。
    使用了SessionLocal()作为会话管理，确保数据库连接的正确使用。

    参数:
        session_pk: 会话ID
        role: 消息角色
        content: 消息内容

    返回:
        ChatMessage: 包含所有添加信息的消息对象
    """
    async with db_manager.session as session:
        msg = ChatMessage(
            session_id=session_pk,
            role=role,
            content=content,
            name=name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_time=response_time,
            meta=meta,
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)

        # 更新会话的 last_msg_id
        await session.execute(
            update(ChatSession)
            .where(ChatSession.id == session_pk)
            .values(last_msg_id=msg.id)
        )
        await session.commit()

        return msg


async def get_last_messages(session_pk: str, limit: int = 20) -> List[ChatMessage]:

    """
    异步获取指定会话的最后几条消息记录

    参数:
        session_pk: 会话的唯一标识符
        limit: 要获取的消息数量，默认为20

    返回:
        List[ChatMessage]: 按创建时间正序排列的消息列表
    """
    async with db_manager.session as session:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_pk)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        rows.reverse()
        return rows


async def get_chat_messages_by_sid(session_id: str) -> List[ChatMessage]:
    """
    异步获取指定会话的所有消息记录

    参数:
        session_id: 会话的唯一标识符

    返回:
        List[ChatMessage]: 按创建时间正序排列的消息列表
    """
    async with db_manager.session as session:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        rows = list(result.scalars().all())
        return rows