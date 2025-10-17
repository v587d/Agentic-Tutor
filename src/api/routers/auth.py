from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.repositories import user_repo
from src.utils.security import verify_token


security = HTTPBearer()
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    token = credentials.credentials  # 从请求头获取token
    username = verify_token(token)  # 验证token
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 认证失败！",
        )
        
    user = await user_repo.get_user_by_username(username)  # 获取用户信息
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在！",
        )
        
    return user