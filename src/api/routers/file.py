from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse

from src.db.models import User
from src.schemas.file import UserFilePublic, FileType
from src.repositories import file_repo
from src.api.routers.auth import get_current_user
from src.utils.file_utils import (
    save_uploaded_file, 
    get_file_download_url,
    delete_user_file as delete_file_from_storage,
    ensure_upload_directories,
    FileUploadError
)
from src.utils.logger import logger

router = APIRouter(prefix="/file", tags=["file"])


@router.post("/upload", response_model=UserFilePublic, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="上传的文件"),
    session_id: Optional[str] = Form(None, description="会话ID（可选）"),
    description: Optional[str] = Form(None, description="文件描述"),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件

    一次调用只允许上传一个文件，文件大小限制为100MB，支持的文件类型包括：
    - 图片: jpeg, png, gif, webp
    - 音频: mp3, wav, ogg
    - 视频: mp4, webm
    - 文档: pdf, txt, doc, docx

    如果提供session_id，文件将关联到指定会话；否则作为用户个人文件存储。
    """
    try:
        # 确保上传目录存在
        ensure_upload_directories()

        # 处理 session_id：空字符串转换为 None
        if session_id == "":
            session_id = None

        # 保存文件到存储系统
        file_path, original_filename, file_size, file_type = await save_uploaded_file(
            file, current_user.id, session_id
        )

        # 生成文件下载URL
        file_url = get_file_download_url(file_path)

        # 创建数据库记录
        user_file = await file_repo.create_user_file(
            user_id=current_user.id,
            session_id=session_id,
            file_url=file_url,
            file_type=file_type,
            file_name=original_filename,
            file_size=file_size,
            mime_type=file.content_type,
            description=description
        )

        logger.info(f"文件记录创建成功: file_id={user_file.id}, user_id={current_user.id}, "
                   f"session_id={session_id or 'personal'}")

        return UserFilePublic.model_validate(user_file)

    except FileUploadError as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"文件上传系统错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件上传失败，请稍后重试"
        )


@router.get("/download/{file_path:path}")
async def download_file(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """
    下载文件
    
    只有文件的所有者才能下载文件
    """
    try:
        # 从文件路径中提取信息来验证权限
        # 文件路径格式: static/uploading/{user_id}/{session_id}/{file_id}_{filename}
        # 或: static/uploading/{user_id}/personal/{file_id}_{filename}
        # 注意：Windows系统使用\分隔符，需要处理两种分隔符
        normalized_path = file_path.replace('\\', '/')
        path_parts = normalized_path.split('/')
        
        if len(path_parts) < 4 or path_parts[0] != 'static' or path_parts[1] != 'uploading':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无效的文件路径"
            )
        
        file_user_id = path_parts[2]
        
        # 检查权限
        if file_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此文件"
            )
        
        # 检查文件是否存在
        import os
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 获取原始文件名
        filename_part = path_parts[-1]
        original_filename = '_'.join(filename_part.split('_')[1:])  # 移除UUID前缀
        
        # 返回文件
        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type="application/octet-stream"  # 通用MIME类型
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件下载失败"
        )


@router.get("/list", response_model=List[UserFilePublic])
async def list_files(
    session_id: Optional[str] = None,
    include_personal: bool = True,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    获取文件列表
    
    可以按会话ID筛选文件，或获取个人文件
    """
    try:
        if session_id:
            # 获取指定会话的文件
            files = await file_repo.get_files_by_user_and_session(
                current_user.id, session_id, include_inactive
            )
        elif include_personal:
            # 获取用户的个人文件（无session_id的文件）
            files = await file_repo.get_personal_files(
                current_user.id, include_inactive
            )
        else:
            # 获取用户的所有文件（包括会话文件和个人文件）
            files = await file_repo.get_files_by_user_id(
                current_user.id, include_inactive
            )
        
        return [UserFilePublic.model_validate(f) for f in files]
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文件列表失败"
        )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除文件（软删除）
    
    将文件标记为非活跃状态，并将物理文件移动到temp文件夹
    """
    try:
        # 获取文件记录
        user_file = await file_repo.get_user_file(file_id)
        if not user_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限
        if user_file.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此文件"
            )
        
        # 从file_url中提取实际文件路径
        # file_url格式: /file/download/{file_path}
        # file_path = user_file.file_url.replace("/file/download/", "")
        file_path = user_file.file_url
        
        # 移动物理文件到temp文件夹
        await delete_file_from_storage(file_path)
        
        # 软删除数据库记录
        success = await file_repo.delete_user_file(file_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件删除失败"
            )
        
        logger.info(f"文件删除成功: file_id={file_id}, user_id={current_user.id}, file_moved_to_temp=True")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件删除失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件删除失败"
        )


@router.get("/stats")
async def get_file_stats(current_user: User = Depends(get_current_user)):
    """
    获取用户文件统计信息
    """
    try:
        stats = await file_repo.get_user_file_stats(current_user.id)
        return stats
    except Exception as e:
        logger.error(f"获取文件统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文件统计失败"
        )