import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
class Settings(BaseSettings):
    API_KEY: str = os.getenv("API_KEY")
    API_BASE: str = os.getenv("API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen3-max")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "kidsaitutoristhebestaicompansionforyourkidslearning")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

# 全局配置实例
settings = Settings()
