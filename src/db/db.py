from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event

from src.db.models import Base

# SQLite 文件放在项目根目录的 database/agentic_tutor.db
ROOT_DIR = Path(__file__).parent.parent.parent
DB_DIR = os.path.join(ROOT_DIR, "database")

os.makedirs(DB_DIR, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DB_DIR}/agentic_tutor.db")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# SQLite 优化：WAL、降低同步级别、开启外键
@event.listens_for(engine.sync_engine, "connect")
def _sqlite_on_connect(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class DatabaseManager:
    """
    数据库管理器类，实现单例模式，用于管理数据库连接和会话。
    使用单例模式确保全局只有一个数据库管理器实例。
    """
    _instance: Optional["DatabaseManager"] = None  # 类变量，用于存储单例实例
    _initialized: bool = False  # 类变量，标记数据库是否已初始化

    def __new__(cls, *args, **kwargs) -> "DatabaseManager":
        """
        重写__new__方法实现单例模式。
        如果类实例不存在，则创建新实例；否则返回已存在的实例。
        参数:
            *args: 位置参数
            **kwargs: 关键字参数
        返回:
            DatabaseManager: 单例实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)  # 创建新实例
        return cls._instance  # 返回单例实例

    async def initialize(self):
        """
        异步初始化数据库连接。
        如果数据库尚未初始化，则调用init_db()进行初始化，并设置初始化标志为True。
        """
        if not self._initialized:
            await init_db()  # 初始化数据库
            self._initialized = True  # 设置初始化标志

    @property
    def session(self) -> AsyncSession:

        """
        获取数据库会话的属性方法。
        每次调用此属性都会返回一个新的数据库会话。
        如果数据库尚未初始化，则先进行初始化。

        返回:
        AsyncSession: 异步数据库会话对象
        """
        if not self._initialized:
            # 这里需要同步初始化，因为属性方法不能是异步的
            # 我们可以使用事件循环来运行异步初始化
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.initialize())
        return SessionLocal()  # 创建并返回新的数据库会话

    async def close(self):
        """关闭数据库连接"""
        if self._initialized:
            await engine.dispose()
            self._initialized = False

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

db_manager = DatabaseManager()
