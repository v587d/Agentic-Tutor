from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from src.agents.host_agent import HostAgent

@asynccontextmanager
async def get_agent(
    session_id: str, 
    user_id: Optional[str] = None,
) -> AsyncGenerator[HostAgent, None]:
    agent = HostAgent(
        stream=True, 
        session_id=session_id, 
        user_id=user_id,
        
    )
    # 每次请求新建一个带持久化 session 的 HostAgent
    try:
        yield agent
    finally:
        # 如有需要可在此做清理
        pass