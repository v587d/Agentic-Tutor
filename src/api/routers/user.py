from typing import List

from fastapi import APIRouter, HTTPException, status, Response, Depends
from fastapi.security import HTTPBearer
from src.repositories import user_repo, persona_repo
from src.schemas.user import UserCreate, UserUpdate, UserPublic, UserLogin, UserAuthResponse
from src.schemas.persona import PersonaCreate, PersonaPublic, PersonaUpdate
from src.utils.security import verify_password, create_access_token
from src.db.models import User
from src.utils.logger import logger
from src.api.routers.auth import get_current_user

router = APIRouter(prefix="/user", tags=["user"])
# security = HTTPBearer()  # 创建Bearer认证实例

@router.post("/register", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate):
    """
    创建新用户。
    """
    if await user_repo.get_user_by_username(user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken!",
        )
    if user_in.email and await user_repo.get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already in use!",
        )
    
    user = await user_repo.create_user(user_in)
    # 创建默认persona
    await persona_repo.create_persona(
        user_id=user.id,
        name="default_persona",
        is_default=True
    )

    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserPublic.model_validate(user)
    }

@router.post("/login", response_model=UserAuthResponse, status_code=status.HTTP_200_OK)
async def login(user_in: UserLogin):
    """用户登录"""
    user = await user_repo.get_user_by_username(user_in.username)  # 获取用户
    if not user or not verify_password(user_in.password, user.hashed_password):  # 验证密码
        logger.warning(f"用户【{user_in.username}】登录失败!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or password is incorrect!",
        )
    logger.info(f"用户【{user_in.username}】登录成功!")
    access_token = create_access_token(data={"sub": user.username})  # 创建token
    await user_repo.update_last_login(user.id)  # 更新最后登录时间
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserPublic.model_validate(user)  # 返回用户信息
    }

@router.get("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

@router.post("/persona", response_model=PersonaPublic, status_code=status.HTTP_200_OK)
async def create_persona(
    persona_in: PersonaCreate,
    current_user: User = Depends(get_current_user)
):
    """
    创建新的用户画像
    """
    # 检查是否已存在同name persona
    existing_personas = await persona_repo.get_persona(current_user.id)
    if any(p.name == persona_in.name for p in existing_personas):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The name of persona already exists!"
        )
    
    # 确保用户只能有一个默认画像
    if persona_in.is_default:
        # 将该用户的其他画像设为非默认
        await persona_repo.update_user_default_personas(current_user.id, False)

    # 创建新的画像
    persona = await persona_repo.create_persona(
        user_id=current_user.id,
        name=persona_in.name,
        tags=persona_in.tags,
        profile=persona_in.profile,
        is_default=persona_in.is_default
    )
    
    return PersonaPublic.model_validate(persona)

@router.get("/persona", response_model=List[PersonaPublic], status_code=status.HTTP_200_OK)
async def get_user_personas(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的所有画像
    """
    personas = await persona_repo.get_persona(current_user.id)
    return [PersonaPublic.model_validate(p) for p in personas]

@router.get("/persona/{persona_id}", response_model=PersonaPublic, status_code=status.HTTP_200_OK)
async def get_persona(
    persona_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取特定画像信息
    """
    persona = await persona_repo.get_persona_pid(persona_id)
    
    # 检查画像是否存在
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found!"
        )
    
    # 检查用户是否有权限访问该画像
    if persona.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this persona!"
        )
    
    return PersonaPublic.model_validate(persona)

@router.put("/persona/{persona_id}", response_model=PersonaPublic, status_code=status.HTTP_200_OK)
async def update_persona(
    persona_in: PersonaUpdate,
    persona_id: str, 
    current_user: User = Depends(get_current_user)
):
    """
    更新用户画像
    """
    # 获取现有画像
    persona = await persona_repo.get_persona_pid(persona_id)
    
    # 检查画像是否存在
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found!"
        )
    
    # 检查用户是否有权限更新该画像
    if persona.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this persona!"
        )
    
    # 如果要更新name，检查新name是否已被该用户的其他persona使用
    if persona_in.name and persona_in.name != persona.name:
        existing_personas = await persona_repo.get_persona(current_user.id)
        if any(p.name == persona_in.name for p in existing_personas):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The name of persona already exists!"
            )

    # 如果设置为默认，则将其他画像设为非默认
    if persona_in.is_default and not persona.is_default:
        await persona_repo.update_user_default_personas(current_user.id, False)
    
    # 更新画像
    updated_persona = await persona_repo.update_persona(
        persona_id=persona_id,
        name=persona_in.name,
        tags=persona_in.tags,
        profile=persona_in.profile,
        is_default=persona_in.is_default
    )
    
    return PersonaPublic.model_validate(updated_persona)


@router.get("/{user_id}", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def get_user(user_id: str):
    """
    根据ID获取用户信息。
    """
    user = await user_repo.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found!")
    
    return user

@router.put("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def update_user(user_in: UserUpdate, current_user: User = Depends(get_current_user)):
    """
    更新当前用户信息。
    """
    # 检查新的 username 或 email 是否已被其他用户占用
    if user_in.username and (existing_user := await user_repo.get_user_by_username(user_in.username)) and existing_user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken!")
    if user_in.email and (existing_user := await user_repo.get_user_by_email(user_in.email)) and existing_user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken!")

    updated_user = await user_repo.update_user(current_user.id, user_in)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    """
    删除用户。
    """
    # success = await user_repo.delete_user(user_id)
    # if not success:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户未找到")
    # return Response(status_code=status.HTTP_204_NO_CONTENT)
    pass

