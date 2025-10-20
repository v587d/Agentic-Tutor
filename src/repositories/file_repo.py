from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy import select, update, and_, func, desc
from sqlalchemy.orm import joinedload

# from src.db.db import db_manager
# from src.db.models import UserFile
from ..db import db_manager, UserFile
# from src.schemas.file import FileType, UserFileCreate, UserFileUpdate
from ..schemas import FileType

async def create_user_file(
    user_id: str,
    session_id: Optional[str],
    file_url: str,
    file_type: FileType,
    file_name: str,
    file_size: int,
    mime_type: str,
    description: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    version: int = 1,
    is_active: bool = True
) -> UserFile:
    """
    创建用户文件记录
    
    参数:
        user_id: 用户ID
        session_id: 会话ID
        file_url: 文件存储路径
        file_type: 文件类型
        file_name: 原始文件名
        file_size: 文件大小（字节）
        mime_type: MIME类型
        description: 文件描述（可选）
        meta: 元数据（可选）
        version: 版本号（默认1）
        is_active: 是否活跃（默认True）
    
    返回:
        UserFile: 创建的文件对象
    """
    async with db_manager.session as session:
        user_file = UserFile(
            user_id=user_id,
            session_id=session_id,
            file_url=file_url,
            file_type=file_type,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            description=description,
            meta=meta,
            version=version,
            is_active=is_active
        )
        session.add(user_file)
        await session.commit()
        await session.refresh(user_file)
        return user_file


async def get_user_file(file_id: str) -> Optional[UserFile]:
    """
    根据文件ID获取文件
    
    参数:
        file_id: 文件ID
    
    返回:
        Optional[UserFile]: 文件对象，如果不存在则返回None
    """
    async with db_manager.session as session:
        return await session.get(UserFile, file_id)


async def update_user_file(
    file_id: str,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    meta: Optional[Dict[str, Any]] = None
) -> Optional[UserFile]:
    """
    更新文件信息
    
    参数:
        file_id: 文件ID
        description: 新的文件描述（可选）
        is_active: 是否活跃（可选）
        meta: 新的元数据（可选）
    
    返回:
        Optional[UserFile]: 更新后的文件对象，如果文件不存在则返回None
    """
    async with db_manager.session as session:
        # 获取现有文件
        user_file = await session.get(UserFile, file_id)
        if not user_file:
            return None
        
        # 更新字段
        if description is not None:
            user_file.description = description
        if is_active is not None:
            user_file.is_active = is_active
        if meta is not None:
            user_file.meta = meta
        
        await session.commit()
        await session.refresh(user_file)
        return user_file


async def delete_user_file(file_id: str) -> bool:
    """
    软删除文件（设置is_active为False）
    
    参数:
        file_id: 文件ID
    
    返回:
        bool: 删除是否成功
    """
    async with db_manager.session as session:
        user_file = await session.get(UserFile, file_id)
        if not user_file:
            return False
        
        user_file.is_active = False
        await session.commit()
        return True


async def get_files_by_user_id(
    user_id: str,
    include_inactive: bool = False
) -> List[UserFile]:
    """
    按用户ID查询文件
    
    参数:
        user_id: 用户ID
        include_inactive: 是否包含非活跃文件（默认False）
    
    返回:
        List[UserFile]: 文件列表
    """
    async with db_manager.session as session:
        stmt = select(UserFile).where(UserFile.user_id == user_id)
        if not include_inactive:
            stmt = stmt.where(UserFile.is_active == True)
        stmt = stmt.order_by(desc(UserFile.created_at))
        
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_files_by_session_id(
    session_id: str,
    include_inactive: bool = False
) -> List[UserFile]:
    """
    按会话ID查询文件
    
    参数:
        session_id: 会话ID
        include_inactive: 是否包含非活跃文件（默认False）
    
    返回:
        List[UserFile]: 文件列表
    """
    async with db_manager.session as session:
        stmt = select(UserFile).where(UserFile.session_id == session_id)
        if not include_inactive:
            stmt = stmt.where(UserFile.is_active == True)
        stmt = stmt.order_by(desc(UserFile.created_at))
        
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_files_by_user_and_session(
    user_id: str,
    session_id: str,
    include_inactive: bool = False
) -> List[UserFile]:
    """
    按用户和会话查询文件
    
    参数:
        user_id: 用户ID
        session_id: 会话ID
        include_inactive: 是否包含非活跃文件（默认False）
    
    返回:
        List[UserFile]: 文件列表
    """
    async with db_manager.session as session:
        stmt = select(UserFile).where(
            and_(
                UserFile.user_id == user_id,
                UserFile.session_id == session_id
            )
        )
        if not include_inactive:
            stmt = stmt.where(UserFile.is_active == True)
        stmt = stmt.order_by(desc(UserFile.created_at))
        
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_files_by_type(
    user_id: str,
    file_type: FileType,
    include_inactive: bool = False
) -> List[UserFile]:
    """
    按文件类型查询
    
    参数:
        user_id: 用户ID
        file_type: 文件类型
        include_inactive: 是否包含非活跃文件（默认False）
    
    返回:
        List[UserFile]: 文件列表
    """
    async with db_manager.session as session:
        stmt = select(UserFile).where(
            and_(
                UserFile.user_id == user_id,
                UserFile.file_type == file_type
            )
        )
        if not include_inactive:
            stmt = stmt.where(UserFile.is_active == True)
        stmt = stmt.order_by(desc(UserFile.created_at))
        
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_active_files(user_id: str) -> List[UserFile]:
    """
    查询用户的活跃文件
    
    参数:
        user_id: 用户ID
    
    返回:
        List[UserFile]: 活跃文件列表
    """
    return await get_files_by_user_id(user_id, include_inactive=False)


async def create_file_version(
    original_file_id: str,
    new_file_url: str,
    description: Optional[str] = None
) -> Optional[UserFile]:
    """
    创建文件新版本
    
    参数:
        original_file_id: 原始文件ID
        new_file_url: 新版本文件URL
        description: 新版本描述（可选）
    
    返回:
        Optional[UserFile]: 新版本文件对象，如果原始文件不存在则返回None
    """
    async with db_manager.session as session:
        # 获取原始文件
        original_file = await session.get(UserFile, original_file_id)
        if not original_file:
            return None
        
        # 创建新版本
        new_version = UserFile(
            user_id=original_file.user_id,
            session_id=original_file.session_id,
            file_url=new_file_url,
            file_type=original_file.file_type,
            file_name=original_file.file_name,
            file_size=original_file.file_size,
            mime_type=original_file.mime_type,
            description=description or original_file.description,
            meta=original_file.meta,
            version=original_file.version + 1,
            is_active=True
        )
        
        session.add(new_version)
        await session.commit()
        await session.refresh(new_version)
        return new_version


async def get_file_versions(file_id: str) -> List[UserFile]:
    """
    获取文件的所有历史版本
    
    参数:
        file_id: 文件ID
    
    返回:
        List[UserFile]: 文件版本列表（按版本号降序排列）
    """
    async with db_manager.session as session:
        # 获取当前文件
        current_file = await session.get(UserFile, file_id)
        if not current_file:
            return []
        
        # 查询相同用户、会话、文件名的所有版本
        stmt = select(UserFile).where(
            and_(
                UserFile.user_id == current_file.user_id,
                UserFile.session_id == current_file.session_id,
                UserFile.file_name == current_file.file_name
            )
        ).order_by(desc(UserFile.version))
        
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def restore_user_file(file_id: str) -> bool:
    """
    恢复软删除的文件
    
    参数:
        file_id: 文件ID
    
    返回:
        bool: 恢复是否成功
    """
    async with db_manager.session as session:
        user_file = await session.get(UserFile, file_id)
        if not user_file:
            return False
        
        user_file.is_active = True
        await session.commit()
        return True


async def get_user_file_stats(user_id: str) -> Dict[str, Any]:
    """
    获取用户文件统计信息
    
    参数:
        user_id: 用户ID
    
    返回:
        Dict[str, Any]: 统计信息字典
    """
    async with db_manager.session as session:
        # 总文件数
        total_stmt = select(func.count(UserFile.id)).where(UserFile.user_id == user_id)
        total_result = await session.execute(total_stmt)
        total_files = total_result.scalar_one()
        
        # 活跃文件数
        active_stmt = select(func.count(UserFile.id)).where(
            and_(
                UserFile.user_id == user_id,
                UserFile.is_active == True
            )
        )
        active_result = await session.execute(active_stmt)
        active_files = active_result.scalar_one()
        
        # 按文件类型统计
        type_stmt = select(
            UserFile.file_type,
            func.count(UserFile.id).label('count')
        ).where(
            and_(
                UserFile.user_id == user_id,
                UserFile.is_active == True
            )
        ).group_by(UserFile.file_type)
        
        type_result = await session.execute(type_stmt)
        type_stats = {row.file_type: row.count for row in type_result}
        
        # 总文件大小
        size_stmt = select(func.sum(UserFile.file_size)).where(
            and_(
                UserFile.user_id == user_id,
                UserFile.is_active == True
            )
        )
        size_result = await session.execute(size_stmt)
        total_size = size_result.scalar_one() or 0
        
        return {
            "total_files": total_files,
            "active_files": active_files,
            "inactive_files": total_files - active_files,
            "type_stats": type_stats,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }


async def get_files_paginated(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    include_inactive: bool = False
) -> Tuple[List[UserFile], int]:
    """
    分页查询用户文件
    
    参数:
        user_id: 用户ID
        page: 页码（从1开始）
        page_size: 每页大小
        include_inactive: 是否包含非活跃文件（默认False）
    
    返回:
        Tuple[List[UserFile], int]: (文件列表, 总记录数)
    """
    async with db_manager.session as session:
        # 基础查询
        base_stmt = select(UserFile).where(UserFile.user_id == user_id)
        if not include_inactive:
            base_stmt = base_stmt.where(UserFile.is_active == True)
        
        # 计算总数
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await session.execute(count_stmt)
        total_count = total_result.scalar_one()
        
        # 分页查询
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(desc(UserFile.created_at)).offset(offset).limit(page_size)
        
        result = await session.execute(stmt)
        files = list(result.scalars().all())
        
        return files, total_count


async def delete_files_batch(file_ids: List[str]) -> int:
    """
    批量删除文件
    
    参数:
        file_ids: 文件ID列表
    
    返回:
        int: 成功删除的文件数量
    """
    async with db_manager.session as session:
        stmt = update(UserFile).where(
            UserFile.id.in_(file_ids)
        ).values(is_active=False)
        
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount


async def update_files_batch(
    file_ids: List[str],
    updates: Dict[str, Any]
) -> int:
    """
    批量更新文件

    参数:
        file_ids: 文件ID列表
        updates: 更新字段字典

    返回:
        int: 成功更新的文件数量
    """
    async with db_manager.session as session:
        stmt = update(UserFile).where(
            UserFile.id.in_(file_ids)
        ).values(**updates)

        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount


async def get_personal_files(
    user_id: str,
    include_inactive: bool = False
) -> List[UserFile]:
    """
    获取用户的个人文件（无session_id的文件）

    参数:
        user_id: 用户ID
        include_inactive: 是否包含非活跃文件（默认False）

    返回:
        List[UserFile]: 个人文件列表
    """
    async with db_manager.session as session:
        stmt = select(UserFile).where(
            and_(
                UserFile.user_id == user_id,
                UserFile.session_id.is_(None)
            )
        )
        if not include_inactive:
            stmt = stmt.where(UserFile.is_active == True)
        stmt = stmt.order_by(desc(UserFile.created_at))

        result = await session.execute(stmt)
        return list(result.scalars().all())