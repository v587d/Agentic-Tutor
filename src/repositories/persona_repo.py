from __future__ import annotations
from typing import Optional, List

from sqlalchemy import select

from src.db.db import db_manager
from src.db.models import Persona
from src.schemas.profile import ProfileConfig

async def create_persona(
    user_id: str,
    name: str,
    tags: Optional[str] = None,
    profile: Optional[dict] = None,
    is_default: bool = True,
) -> Persona:
    async with db_manager.session as session:
        persona = Persona(
            user_id=user_id,
            name=name,
            tags=tags,
            profile=profile or ProfileConfig().model_dump(),
            is_default=is_default,
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)
        return persona


async def get_persona(user_id: str) -> List[Persona]:
    async with db_manager.session as session:
        result = await session.execute(select(Persona).where(Persona.user_id == user_id))
        return list(result.scalars().all())

async def get_persona_pid(persona_id: str) -> Optional[Persona]:
    """
    根据PersonID获取画像
    
    参数:
        persona_id: 画像的唯一标识符
        
    返回:
        Optional[Persona]: 如果找到则返回画像对象，否则返回None
    """
    async with db_manager.session as session:
        result = await session.execute(select(Persona).where(Persona.id == persona_id))
        return result.scalar_one_or_none()

async def get_persona_profile(persona_id: str) -> Optional[str]:
    """
    根据persona_id获取persona的内容

    参数:
        persona_id: persona的唯一标识符

    返回:
        Optional[str]: 如果找到则返回persona内容，否则返回None
    """
    async with db_manager.session as session:
        result = await session.execute(select(Persona).where(Persona.id == persona_id))
        obj = result.scalar_one_or_none()
        return obj.content if obj else None
    
async def update_persona(
    persona_id: str,
    name: Optional[str] = None,
    tags: Optional[str] = None,
    profile: Optional[dict] = None,
    is_default: Optional[bool] = None
) -> Optional[Persona]:
    """
    更新画像信息
    
    参数:
        persona_id: 画像的唯一标识符
        name: 新的名称
        tags: 新的标签
        profile: 新的画像配置
        is_default: 是否为默认画像
        
    返回:
        Optional[Persona]: 更新后的画像对象，如果不存在则返回None
    """
    async with db_manager.session as session:
        # 获取现有画像
        result = await session.execute(select(Persona).where(Persona.id == persona_id))
        persona = result.scalar_one_or_none()
        
        if not persona:
            return None
            
        # 更新字段
        if name is not None:
            persona.name = name
        if tags is not None:
            persona.tags = tags
        if profile is not None:
            persona.profile = profile
        if is_default is not None:
            persona.is_default = is_default
            
        await session.commit()
        await session.refresh(persona)
        return persona

async def update_user_default_personas(user_id: str, is_default: bool) -> None:
    """
    更新用户的所有画像的默认状态
    
    参数:
        user_id: 用户的唯一标识符
        is_default: 要设置的默认状态
    """
    async with db_manager.session as session:
        # 获取用户的所有画像
        result = await session.execute(select(Persona).where(Persona.user_id == user_id))
        personas = result.scalars().all()
        
        # 更新所有画像的默认状态
        for persona in personas:
            persona.is_default = is_default
            
        await session.commit()