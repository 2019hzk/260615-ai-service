from fastapi import APIRouter, UploadFile

from atguigu.app.dependencies import KnowledgeServiceDep, AdminDep, AdminServiceDep

router = APIRouter(prefix="/api/v1", tags=["AI Operations"])


@router.get("/admin/metrics")
async def get_admin_metrics(admin_service: AdminServiceDep, _: AdminDep) -> dict:
    """返回管理员观测面板使用的 AI Run 汇总指标。"""
    return await admin_service.get_metrics()


@router.get("/runs")
async def list_runs(admin_service: AdminServiceDep, _: AdminDep, limit: int = 50) -> list[dict]:
    """返回最近的 AI Run。"""
    return await admin_service.list_runs(limit)


@router.get("/runs/{run_id}")
async def get_run(run_id: str, admin_service: AdminServiceDep, _: AdminDep) -> dict:
    """返回一个 AI Run 及其工具调用记录。"""
    return await admin_service.get_run(run_id)


@router.get("/knowledge")
async def list_knowledge(knowledge_service: KnowledgeServiceDep, _: AdminDep) -> list[dict]:
    """返回已入库的全部知识切片列表。"""
    return await knowledge_service.list_chunks()


@router.post("/knowledge/upload")
async def upload_knowledge(
        knowledge_service: KnowledgeServiceDep,
        _: AdminDep,
        file: UploadFile,
) -> dict:
    """上传 PDF 知识库文件，完成解析、切片与 Embedding 向量化入库。"""
    pdf_bytes = await file.read()
    count = await knowledge_service.upload_pdf(file.filename, pdf_bytes)
    return {"file_name": file.filename, "chunks": count}
