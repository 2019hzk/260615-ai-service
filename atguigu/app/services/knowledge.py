from io import BytesIO

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.infrastructure.db import async_session_factory
from atguigu.app.models.enums import ToolResultCode
from atguigu.app.models.models import KnowledgeChunk


class KnowledgeService:
    """提供 PDF 知识文档上传、列表查询与知识检索。"""

    def __init__(self, session: AsyncSession | None = None):
        self.session = session

    async def upload_pdf(self, file_name: str, pdf_bytes: bytes) -> int:
        """解析上传的 PDF 文件并存入数据库。"""
        reader = PdfReader(BytesIO(pdf_bytes))
        content = "\n".join(page.extract_text() for page in reader.pages).strip()
        self.session.add(
            KnowledgeChunk(
                file_name=file_name,
                content=content,
            )
        )
        await self.session.commit()
        return 1

    async def list_chunks(self) -> list[dict]:
        """返回已入库的全部知识列表（供管理后台展示）。"""
        stmt = select(KnowledgeChunk).order_by(KnowledgeChunk.created_at.desc())
        records = (await self.session.scalars(stmt)).all()
        return [
            {
                "id": item.id,
                "file_name": item.file_name,
                "content": item.content,
                "created_at": item.created_at,
            }
            for item in records
        ]

    async def search(self) -> dict:
        """查询知识库中的知识内容。"""


        async with async_session_factory() as session:
            data = (await session.scalars(select(KnowledgeChunk.content))).all()
        return {
            "success": True,
            "code": ToolResultCode.KNOWLEDGE_SEARCH_COMPLETED,
            "message": "已找到相关知识内容",
            "data": data,
        }

