import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from fastapi import UploadFile, HTTPException, status

from src.config.settings import settings
from src.schemas.file import FileType
from src.utils.logger import logger


class FileUploadError(Exception):
    """文件上传错误"""
    pass


def get_file_type_from_mime(mime_type: str) -> FileType:
    """根据MIME类型获取文件类型枚举"""
    if mime_type.startswith('image/'):
        return FileType.IMAGE
    elif mime_type.startswith('audio/'):
        return FileType.AUDIO
    elif mime_type.startswith('video/'):
        return FileType.VIDEO
    elif mime_type in ['application/pdf', 'text/plain', 'application/msword', 
                      'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        return FileType.DOCUMENT
    else:
        return FileType.OTHER


def validate_file(file: UploadFile) -> None:
    """验证上传的文件"""
    # 检查文件大小
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小不能超过 {settings.MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    # 检查MIME类型
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持的文件类型: {file.content_type}"
        )


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    # 保留文件扩展名
    name, ext = os.path.splitext(filename)
    # 只保留字母、数字、下划线、连字符和点号
    safe_name = "".join(c for c in name if c.isalnum() or c in ('_', '-', ' '))
    safe_name = safe_name.replace(' ', '_')  # 将空格替换为下划线
    return f"{safe_name}{ext}"


def get_user_file_path(user_id: str, session_id: Optional[str], filename: str) -> Path:
    """获取用户文件的存储路径，确保目录存在"""
    upload_dir = Path(settings.UPLOAD_DIR)
    
    if session_id:
        # 有会话ID：存储在会话目录中
        user_dir = upload_dir / user_id / session_id
    else:
        # 无会话ID：存储在用户个人文件目录中
        user_dir = upload_dir / user_id / "personal"
    
    # 确保目录存在
    user_dir.mkdir(parents=True, exist_ok=True)
    
    return user_dir / filename


async def save_uploaded_file(
    file: UploadFile,
    user_id: str,
    session_id: Optional[str] = None
) -> Tuple[str, str, int, FileType]:
    """保存上传的文件并返回文件信息"""
    
    # 验证文件
    validate_file(file)
    
    # 生成安全的文件名
    file_id = str(uuid.uuid4())
    safe_filename = sanitize_filename(file.filename)
    stored_filename = f"{file_id}_{safe_filename}"
    
    # 获取存储路径
    file_path = get_user_file_path(user_id, session_id, stored_filename)
    
    # 确保目录存在
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 保存文件
        with file_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 获取文件大小
        file_size = len(content)
        
        # 获取文件类型
        file_type = get_file_type_from_mime(file.content_type)
        
        logger.info(f"文件上传成功: user_id={user_id}, session_id={session_id}, "
                   f"filename={file.filename}, size={file_size}, type={file_type}")
        
        return str(file_path), file.filename, file_size, file_type
        
    except Exception as e:
        logger.error(f"文件保存失败: {str(e)}")
        # 如果文件已部分写入，尝试删除
        if file_path.exists():
            try:
                file_path.unlink()
            except:
                pass
        raise FileUploadError(f"文件保存失败: {str(e)}")


def get_file_download_url(file_path: str) -> str:
    """生成文件下载URL"""
    # 使用文件路径作为标识符，确保唯一性
    return file_path


async def delete_user_file(file_path: str) -> bool:
    """删除用户文件，移动到temp文件夹"""
    try:
        path = Path(file_path)
        if path.exists():
            # 创建temp目录路径（放在项目根目录下，不在static目录中）
            temp_dir = Path("temp_deleted_files")
            temp_dir.mkdir(exist_ok=True)
            
            # 生成temp目录中的新文件名（保持原文件名但添加时间戳避免冲突）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"{timestamp}_{path.name}"
            temp_path = temp_dir / temp_filename
            
            # 移动文件到temp目录
            shutil.move(str(path), str(temp_path))
            logger.info(f"文件已移动到temp文件夹: {file_path} -> {temp_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"文件删除失败 {file_path}: {str(e)}")
        return False


def ensure_upload_directories():
    """确保上传目录存在"""
    upload_dir = Path(settings.UPLOAD_DIR)
    
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"上传目录已确保存在: {upload_dir}")
