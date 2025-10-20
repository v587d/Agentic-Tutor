from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """文件类型枚举"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    OTHER = "other"


# 基础文件模型
class UserFileBase(BaseModel):
    file_url: str
    file_type: FileType
    file_name: str
    file_size: int
    mime_type: str
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v):
        if v < 0:
            raise ValueError('文件大小不能为负数')
        if v > 100 * 1024 * 1024:  # 100MB
            raise ValueError('文件大小不能超过100MB')
        return v

    @field_validator('file_url')
    @classmethod
    def validate_file_url(cls, v):
        if not v:
            raise ValueError('文件URL不能为空')
        return v


# 创建文件时需要提供的模型
class UserFileCreate(UserFileBase):
    user_id: str
    session_id: Optional[str] = None
    version: int = 1
    is_active: bool = True


# 更新文件时可以提供的模型
class UserFileUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


# API响应的文件模型
class UserFilePublic(UserFileBase):
    id: str
    user_id: str
    session_id: Optional[str] = None
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 文件列表响应模型
class UserFileList(BaseModel):
    files: list[UserFilePublic]
    total: int