from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from enum import Enum

from pydantic import BaseModel, Field, field_validator

class PreferredModality(str, Enum):
    VISUAL = "visual" 
    AUDITORY = "auditory" 
    KINESTHETIC = "kinesthetic" 
    READING = "reading" 
    INTERACTIVE = "interactive"

class Pace(str, Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"

class ScaffoldingLevel(str, Enum):
    LOW = "low" 
    MEDIUM = "medium" 
    HIGH = "high"

class ExamplesPreference(str, Enum):
    REAL_LIFE = "real_life" 
    ABSTRACT = "abstract" 
    ACADEMIC = "academic" 
    INTERACTIVE = "interactive" 

class ErrorCorrectionStyle(str, Enum):
    SOCRATIC = "socratic" 
    DIRECT = "direct" 
    GENTLE = "gentle" 
    STEP_BY_STEP = "step_by_step"

class Tone(str, Enum):
    ENCOURAGING = "encouraging"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    STRICT = "strict"
    HUMOROUS = "humorous"
    CALM = "calm"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"

class PraiseFrequency(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

class QuizStyle(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

class ContentLevel(str, Enum):
    K12_SAFE = "k12-safe"
    GENERAL_SAFE = "general-safe"

class IdentityConfig(BaseModel):
    nickname: str = Field(default="Sweetie", description="用户昵称")
    birth_month: str = Field(default="", description="出生月份")
    grade_level: str = Field(default="", description="年级")
    locale: str = Field(default="CN", description="地区")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    primary_language: str = Field(default="zh-CN", description="主要语言")
    bilingual: bool = Field(default=False, description="是否双语")
    CEFR_level: str = Field(default="A2", description="CEFR等级")

class LearningConfig(BaseModel):
    strengths: List[str] = Field(default_factory=list, description="学习优势")
    challenges: List[str] = Field(default_factory=list, description="学习挑战")
    goals: Dict[str, str] = Field(default_factory=lambda: {"short_term": "", "long_term": ""})
    subjects_focus: List[str] = Field(default_factory=list, description="关注的学科")
    preferred_modalities: List[PreferredModality] = Field(
        default_factory=list,
        description="""用户的偏好模态，例如视觉、听觉、动觉等，可以多选
        - visual（视觉型）：喜欢看图表、视频等，对色彩敏感，善于空间想象等
        - auditory（听觉型）：喜欢听讲解、音频等，对声音敏感，善于听觉记忆等
        - kinesthetic（动觉型）：喜欢动手实践、操作等
        - reading（阅读型）：喜欢文字阅读
        - interactive（互动型）：喜欢讨论、问答等
        """
    )
    pace: Pace = Field(default=Pace.NORMAL,description="学习节奏，慢、中、快")
    scaffolding_level: ScaffoldingLevel = Field(
        default=ScaffoldingLevel.MEDIUM,
        description="“脚手架”（scaffolding）指的是为学习者提供的临时支持，帮助他们完成超出当前能力范围的任务。比如，老师可能会通过提示、引导性问题或分步指导来帮助学生逐步掌握知识。学习支架强度：low(少量提示)、medium(适度指导)、high(详细步骤指导)"
    )
    examples_preference: ExamplesPreference = Field(
        default=ExamplesPreference.REAL_LIFE,
        description="举例偏好：real_life(生活实例)、abstract(抽象例子)、academic(学术案例)、interactive(互动示例)"
    )
    error_correction_style: ErrorCorrectionStyle = Field(
        default=ErrorCorrectionStyle.SOCRATIC,
        description="纠错方式：socratic(提问引导)、direct(直接指正)、gentle(温和鼓励)、step_by_step(逐步分析)"
    )

class MotivationConfig(BaseModel):
    tone: Tone = Field(default=Tone.ENCOURAGING, description="语气")
    praise_frequency: PraiseFrequency = Field(default=PraiseFrequency.MODERATE, description="表扬频率")
    gamification: bool = Field(default=False, description="是否启用“积分/徽章/闯关")
    interests: List[str] = Field(default_factory=list, description="兴趣")
    emotion_checkin: bool = Field(default=True, description="是否开场情绪问候")
    growth_mindset: bool = Field(default=True, description="强化成长型思维")
    reward_scheme: str = Field(default="", description="简单奖励规则（例：完成3题给1枚徽章）")

class RoutinesConfig(BaseModel):
    session_length_max: int = Field(default=60, description="单次最大会话时长（分钟）")
    break_interval_min: int = Field(default=15, description="休息间隔（分钟）")
    study_schedule: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "Mon": ["19:00-20:00"],
            "Sat": ["10:00-11:00"]
        },
        description="每周可用时段"
    )
    homework_policy: str = Field(default="Don't give direct answers, provide hints and key concepts", description="作业政策")
    offline_suggestions: bool = Field(default=True, description="在适当的时候提供这些离线学习建议，减少对AI的依赖")

    @field_validator('session_length_max')
    @classmethod
    def validate_session_length(cls, v):
        if not (5 <= v <= 180):
            raise ValueError('session_length_max must be between 5 and 180 minutes')
        return v

    @field_validator('break_interval_min')
    @classmethod
    def validate_break_interval(cls, v):
        if not (5 <= v <= 45):
            raise ValueError('break_interval_min must be between 5 and 45 minutes')
        return v

class CommunicationConfig(BaseModel):
    emoji: bool = Field(default=True, description="是否使用表情符号")
    step_by_step: bool = Field(default=True, description="是否逐步讲解")
    ask_before_answer: bool = Field(default=True, description="是否在回答前提问")

class AssessmentConfig(BaseModel):
    quiz_style: QuizStyle = Field(default=QuizStyle.MULTIPLE_CHOICE, description="测验类型")
    adapt_difficulty: bool = Field(default=True, description="根据学生的表现自动调整题目难度")
    mastery_threshold: float = Field(default=0.8, description="掌握度阈值")
    spaced_repetition: bool = Field(default=True, description="是否使用间隔重复，根据遗忘曲线，在适当的时间间隔重复练习")

    @field_validator('mastery_threshold')
    @classmethod
    def validate_mastery_threshold(cls, v):
        if not (0.5 <= v <= 1.0):
            raise ValueError('mastery_threshold must be between 0.5 and 1.0')
        return v

class SafetyConfig(BaseModel):
    external_links_allowed: bool = Field(default=False, description="是否允许外部链接")
    content_level: ContentLevel = Field(default=ContentLevel.K12_SAFE, description="内容等级")
    prohibited_topics: List[str] = Field(
        default_factory=lambda: ["Violent", "Adult"],
        description="禁止的话题"
    )

class MetaConfig(BaseModel):
    version: str = Field(default="1.0")
    notes: str = Field(default="")

class ProfileConfig(BaseModel):
    identity: IdentityConfig = Field(default_factory=IdentityConfig)
    learning: LearningConfig = Field(default_factory=LearningConfig)
    motivation: MotivationConfig = Field(default_factory=MotivationConfig)
    communication: CommunicationConfig = Field(default_factory=CommunicationConfig)
    routines: RoutinesConfig = Field(default_factory=RoutinesConfig)
    assessment: AssessmentConfig = Field(default_factory=AssessmentConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    meta: MetaConfig = Field(default_factory=MetaConfig)

    class Config:
        use_enum_values = True # 这个设置允许在序列化时使用枚举的实际值，而不是枚举对象本身。
        arbitrary_types_allowed = True # 这个设置允许模型接受任意类型的字段
        json_schema_extra = {
            "example": {
                "identity": {
                    "nickname": "小明",
                    "grade_level": "初中"
                },
                "learning": {
                    "pace": "normal",
                    "strengths": ["数学", "物理"]
                }
            }
        }