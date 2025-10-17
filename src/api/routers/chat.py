import re
import json
import hashlib
import time
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from src.schemas.chat import ChatReq
from src.db.models import User
from src.api.deps import get_agent
from src.api.routers.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

def validate_session_key(session_key: str) -> bool:
    """
    验证会话密钥的格式和时效性
    """
    try:
        # 检查格式
        pattern = r'^session_\d+_[a-z0-9]+_[A-Za-z0-9+/]{8}$'
        if not re.match(pattern, session_key):
            return False
            
        # 解析时间戳
        parts = session_key.split('_')
        timestamp = int(parts[1])
        
        # 检查时效性（24小时）
        current_time = int(time.time() * 1000)
        if current_time - timestamp > 24 * 60 * 60 * 1000:
            return False
            
        return True
    except Exception:
        return False

async def sse_stream(req: ChatReq):
    # 验证会话密钥
    if not validate_session_key(req.session_id):
        raise ValueError("Invalid session ID")
        
    # 验证指令长度和内容
    if not req.instruction or len(req.instruction) > 20000:
        raise ValueError("Invalid instruction")
        
    # 检查敏感内容
    forbidden_words = ["password", "token", "secret"]
    if any(word in req.instruction.lower() for word in forbidden_words):
        raise ValueError("Instruction contains forbidden content")

    async with get_agent(session_id=req.session_id, user_id=req.user_id) as agent:
        last_chunk = None
        async for chunk in agent.stream_reply(req.instruction):
            last_chunk = chunk
            yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
        if last_chunk:
            usage = json.dumps(last_chunk.usage)
            yield f"data: {usage}\n\n"

@router.post("/stream")
def chat_stream(
    req: ChatReq, 
    # current_user: User = Depends(get_current_user)
):
    return StreamingResponse(
        sse_stream(req),
        media_type="text/event-stream",
    )


