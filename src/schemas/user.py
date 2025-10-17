from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

# 基础用户模型
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v and (len(v) < 6 or len(v) > 30):
            raise ValueError('用户名长度必须在6-30个字符之间')
        return v

    # @field_validator('email', mode='before')
    # @classmethod
    # def set_email_from_username(cls, v, values):
    #     if v is None and 'username' in values.data:
    #         try:
    #             # 尝试将 username 转换为 EmailStr
    #             return EmailStr(values.data['username'])
    #         except ValueError:
    #             # 如果不是有效邮箱，保持 None
    #             return None
    #     return v

    # @field_validator('display_name', mode='before')
    # @classmethod
    # def set_default_display_name(cls, v, values):
    #     if v is None and 'username' in values.data and values.data['username']:
    #         username = values.data['username']
    #         # 如果第一个字符是字母，则使用其大写形式
    #         if username[0].isalpha():
    #             return username[0].upper()
    #         # 如果是数字或特殊字符，则使用默认前缀
    #         return "U"  # U代表User
    #     return v    

# 创建用户时需要提供的模型
class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少为8个字符")
        if len(v) > 20:
            raise ValueError("密码长度不能超过20个字符")
        return v
    
class UserLogin(BaseModel):
    username: str
    password: str

# 更新用户时可以提供的模型
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    display_name: Optional[str] = None

# API响应的用户模型 (不含密码)
class UserPublic(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    """
    from_attributes = True的作用：
    # 假设你有一个从数据库获取的SQLAlchemy User对象
    user_from_db = session.query(User).first()

    # 有了from_attributes = True，你可以直接这样转换：
    user_public = UserPublic.from_orm(user_from_db)  # 或 UserPublic.model_validate(user_from_db)

    # 而不需要手动转换：
    user_public = UserPublic(
        id=user_from_db.id,
        email=user_from_db.email,
        username=user_from_db.username,
        created_at=user_from_db.created_at,
        updated_at=user_from_db.updated_at
    )
    """

class UserAuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserPublic