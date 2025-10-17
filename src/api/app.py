from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.routers import chat, user, session
from src.db.db import db_manager

def create_app() -> FastAPI:
    app = FastAPI(title="Agentic Tutor API", version="0.1.0")

    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/")
    async def read_root():
        return FileResponse("static/pages/chat.html")

    @app.on_event("startup")
    async def startup_event():
        # 初始化数据库
        await db_manager.initialize()  # 使用全局实例

    @app.on_event("shutdown")
    async def shutdown_event():
        # 关闭数据库连接
        await db_manager.close()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        # todo: 生成环境需修改指定域名
        # allow_origins=["http://www.smartapp.market"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(chat.router)
    app.include_router(user.router) 
    app.include_router(session.router)
    return app