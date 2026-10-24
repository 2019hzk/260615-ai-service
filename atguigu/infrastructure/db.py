from typing import AsyncGenerator
from logging import getLogger

logger = getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from atguigu.common.settings import get_settings

async_engine: AsyncEngine = create_async_engine(
    url=get_settings().ai_database_url,
    echo=False
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine,
    expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    async  with  async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"操作数据库出现异常 原因:{str(e)}")
            await session.rollback()
            raise e
