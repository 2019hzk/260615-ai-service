import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from atguigu.agent.agent import build_agent
from atguigu.app.routers import run, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lifespan(app: FastAPI):
    logger.info("初始化智能专家智能体成功")
    app.state.agent = build_agent()  # type:ignore
    yield


app = FastAPI(title="Ecommerce AI Service", lifespan=lifespan)
app.include_router(run.router)
app.include_router(admin.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
