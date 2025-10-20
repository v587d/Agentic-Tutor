from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, text, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from ..schemas import (
    LearningConfig, 
    ProfileConfig, 
    FileType,
)
from ..utils import logger


def gen_uuid_str() -> str:
    return str(uuid.uuid4())

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid_str)
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(128))
    email: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(32))

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"),
        onupdate=text("(CURRENT_TIMESTAMP)"),
    )

    personas: Mapped[List["Persona"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="raise"
    )
    sessions: Mapped[List["ChatSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="raise"
    )
    files: Mapped[List["UserFile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="raise"
    )


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64))  
     # 结构化画像（编辑、版本管理、可查询/可控）。通过mapped_column(JSON)可以直接存储和查询JSON数据。
    profile: Mapped[ProfileConfig] = mapped_column(JSON, default=ProfileConfig().model_dump())
    tags: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # 可选标签，逗号分隔
    is_default: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"),
        onupdate=text("(CURRENT_TIMESTAMP)"),
    )

    user: Mapped[User] = relationship(back_populates="personas")

    # 复合索引，避免用户创建同名画像
    __table_args__ = (
        Index("ix_personas_user_name", "user_id", "name", unique=True),
        Index("ix_personas_user_default", "user_id", "is_default"),
    )

    @classmethod
    def get_default_template(cls) -> Dict[str, Any]:
        return {
            "name": "default_profile",
            "profile": ProfileConfig().model_dump()
        }

    def compile_profile_prompt(self) -> str:
        # 获取字段的description
        def get_field_description(model_class: type, field_name: str) -> str:
            return model_class.model_fields[field_name].description or ""
        
        if self.profile is None:
            self.profile = ProfileConfig().model_dump()
        # 将字典转换为ProfileConfig对象
        profile_config = ProfileConfig.model_validate(self.profile)
        # identity
        nickname = profile_config.identity.nickname
        birth_month = profile_config.identity.birth_month
        grade_level = profile_config.identity.grade_level
        locale = profile_config.identity.locale
        timezone = profile_config.identity.timezone
        primary_language = profile_config.identity.primary_language
        CEFR_level = profile_config.identity.CEFR_level
        # learning
        strengths = profile_config.learning.strengths
        challenges = profile_config.learning.challenges
        goals = profile_config.learning.goals
        subjects_focus = profile_config.learning.subjects_focus
        preferred_modalities = profile_config.learning.preferred_modalities
        pace = profile_config.learning.pace.value
        scaffolding_level = profile_config.learning.scaffolding_level.value
        examples_preference = profile_config.learning.examples_preference.value
        error_correction_style = profile_config.learning.error_correction_style.value
        # motivation
        tone = profile_config.motivation.tone.value
        praise_frequency = profile_config.motivation.praise_frequency.value
        interests = profile_config.motivation.interests
        emotion_checkin = profile_config.motivation.emotion_checkin
        growth_mindset = profile_config.motivation.growth_mindset
        # communication
        emoji = profile_config.communication.emoji
        step_by_step = profile_config.communication.step_by_step
        ask_first = profile_config.communication.ask_before_answer
        # routines
        # assessment
        # agent
        external_links_allowed = profile_config.safety.external_links_allowed
        # safety
        content_level = profile_config.safety.content_level.value
        prohibited_topics = profile_config.safety.prohibited_topics
        # others
        notes = profile_config.meta.notes
        lines = []
        
        lines.append(f"你是一名面向`K-12`用户的耐心AI导师，请用`{tone}`的语气，并称呼用户为`{nickname}`。")
        
        if birth_month:
            lines.append(f"生日：`{birth_month}`。")
       
        if grade_level:
            lines.append(f"年级：`{grade_level}`。")
        
        lines.append(f"用户母语：`{primary_language}`，地区：`{locale}`，时区：`{timezone}`。")
        
        if CEFR_level:
            lines.append(f"用户阅读水平：CEFR框架-`{CEFR_level}`级别。")
        
        if interests:
            lines.append(f"用户兴趣爱好：`{'、'.join(interests)}`。")
        
        # preferences
        if strengths:
            lines.append(f"用户自我评价-优势：`{'、'.join(strengths)}`。")
       
        if challenges:
            lines.append(f"用户自我评价-挑战：`{'、'.join(challenges)}`。")
       
        if goals and goals.get("short_term"):
            lines.append(f"用户的短期目标： `{goals.get('short_term')}`。")
        
        if goals and goals.get("long_term"):
            lines.append(f"用户的长期目标：`{goals.get('long_term')}`。")
        
        if subjects_focus:
            lines.append(f"用户关注的学科：`{'、'.join(subjects_focus)}`。")
        
        if preferred_modalities:
            lines.append(
                f"与AI交互偏好：`{'、'.join(preferred_modalities)}`。"
                f"（字段解释：{get_field_description(LearningConfig, "preferred_modalities")}）"
            )

        lines.append(f"学习节奏：`{pace}`。（字段解释：{get_field_description(LearningConfig, "pace")}）")
        
        lines.append(f"提供学习支架(Scaffolding_level)：`{scaffolding_level}`。（字段解释：{get_field_description(LearningConfig, "scaffolding_level")}）")
        
        lines.append(f"当需要举例说明时，符合以下用户偏好：`{examples_preference}`。（字段解释：{get_field_description(LearningConfig, "examples_preference")}）")
        
        lines.append(f"错误纠正风格：`{error_correction_style}`。（字段解释：{get_field_description(LearningConfig, "error_correction_style")}）")
        # motivation
        lines.append(f"表扬用户频率：`{praise_frequency}`。")
        
        if emotion_checkin:
            lines.append(f"对话开始先用一句轻松的问候了解用户状态，鼓励表达感受。用户未回应无需再问。")
        
        if growth_mindset:
            lines.append(f"鼓励用户保持积极的学习态度，并强调学习过程中的进步。")
        # communication
        if emoji:
            lines.append(f"在对话中使用emoji表情，降低长篇文字压迫感。")
        
        lines.append(
            f"讲解方式：{'逐步讲解，避免直接给出最终答案。' if step_by_step else '整体讲解，明确答案。'}"
        )
        
        if ask_first:
            lines.append("在给出答案前，先提出1-2个澄清问题以了解用户思路。")
        # assessment (主要面向Agents)
        # agent (主要面向Agents)
        # safety
        lines.append(f"严格遵循`{content_level}`内容等级，不涉及以下话题：`{', '.join(prohibited_topics) if prohibited_topics else '无'}`。")
        
        if not external_links_allowed:
            lines.append(f"禁止使用外部链接，除非有明确指示。")
        # meta
        if notes:
            lines.append(f"用户额外备注：{notes}")
        # 在最后统一添加换行
        prompt = "\n".join(lines) + "\n"
        return prompt

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid_str)
    # 前端传入的会话标识；唯一（避免重复创建）
    session_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    # 新增字段：最后一条消息的ID
    last_msg_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )

    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    # persona_id: Mapped[Optional[str]] = mapped_column(ForeignKey("personas.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"),
        onupdate=text("(CURRENT_TIMESTAMP)"),
    )

    """
    当关系是"一对多"时，"一"的一方用复数形式（如 sessions）
    当关系是"多对一"时，"多"的一方用单数形式（如 session）
    当关系是可选的或单向时，可以不使用 back_populates
    """
    user: Mapped[Optional[User]] = relationship(back_populates="sessions")
    # persona: Mapped[Optional[Persona]] = relationship()
    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="session", 
        cascade="all, delete-orphan", 
        lazy="raise",
        foreign_keys="ChatMessage.session_id"  # 明确指定使用 session_id 作为外键
    )

     # 添加与最后一条消息的关系
    last_message: Mapped[Optional["ChatMessage"]] = relationship(
        foreign_keys=[last_msg_id],
        primaryjoin="ChatSession.last_msg_id == ChatMessage.id"
    )
    files: Mapped[List["UserFile"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="raise"
    )

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid_str)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)

    role: Mapped[str] = mapped_column(String(32))  # user / assistant / system / tool
    content: Mapped[str] = mapped_column(Text)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(nullable=True)  
    output_tokens: Mapped[Optional[int]] = mapped_column(nullable=True)  
    response_time: Mapped[Optional[float]] = mapped_column(nullable=True)  

    # 避免与 Base.metadata 冲突：Python属性叫 meta，列名仍叫 "metadata"
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"))

    session: Mapped[ChatSession] = relationship(
        back_populates="messages",
        foreign_keys=[session_id]
    )

    __table_args__ = (
        Index("ix_chat_messages_session_time", "session_id", "created_at"),
    )

class UserFile(Base):
    __tablename__ = "user_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[Optional[str]] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=True)
    
    file_url: Mapped[str] = mapped_column(String(512))  # 文件在服务器上的存储路径
    file_type: Mapped[FileType] = mapped_column(String(32))  # 文件类型枚举
    file_name: Mapped[str] = mapped_column(String(255))  # 原始文件名
    file_size: Mapped[int] = mapped_column(Integer)  # 文件大小（字节）
    mime_type: Mapped[str] = mapped_column(String(128))  # MIME类型
    
    version: Mapped[int] = mapped_column(Integer, default=1)  # 版本号
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否活跃
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 文件描述
    
    # 避免与 Base.metadata 冲突：Python属性叫 meta，列名仍叫 "metadata"
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("(CURRENT_TIMESTAMP)"),
        onupdate=text("(CURRENT_TIMESTAMP)"),
    )

    user: Mapped[User] = relationship(back_populates="files")
    session: Mapped[ChatSession] = relationship(back_populates="files")

    __table_args__ = (
        Index("ix_user_files_user_session", "user_id", "session_id"),
        Index("ix_user_files_file_type", "file_type"),
        Index("ix_user_files_created_at", "created_at"),
    )
