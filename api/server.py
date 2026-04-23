from __future__ import annotations

"""Story2Proposal 的 HTTP API 入口。

这一层只负责三件事：
- 创建 FastAPI 应用
- 暴露给前端可调用的路由
- 把请求分发到 repository 层

它不承载具体业务逻辑；真正的 stories / runs 读写和运行管理都在
`api/repository.py` 里。
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import ResearchStory

from .models import RunCreateRequest, RunDetailResponse, RunItemResponse
from .repository import RunRepository, StoryRepository

# API 应用本体。
app = FastAPI(title="Story2Proposal API")
# 允许前端开发服务器直接访问这里的接口。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stories = StoryRepository()
runs = RunRepository()


@app.get("/api/health")
def health() -> dict[str, str]:
    """最小健康检查接口。"""
    return {"status": "ok"}


@app.get("/api/stories", response_model=list[ResearchStory])
def list_stories() -> list[ResearchStory]:
    """返回当前 stories 目录中的全部 `ResearchStory`。"""
    return stories.list()


@app.post("/api/stories", response_model=ResearchStory)
def save_story(payload: ResearchStory) -> ResearchStory:
    """保存或覆盖一份 `ResearchStory`。"""
    return stories.save(payload)


@app.get("/api/runs", response_model=list[RunItemResponse])
def list_runs() -> list[RunItemResponse]:
    """返回所有可见的 run 摘要。"""
    return runs.list()


@app.post("/api/runs", response_model=RunDetailResponse)
def create_run(payload: RunCreateRequest) -> RunDetailResponse:
    """基于一份 `ResearchStory` 启动新的 run。"""
    return runs.create(payload.story, payload.model)


@app.get("/api/runs/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str) -> RunDetailResponse:
    """返回某个 run 的详细状态和聚合产物。"""
    try:
        return runs.get(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}") from exc


if __name__ == "__main__":
    import uvicorn

    # 本地直接执行时，启动单进程 API server。
    uvicorn.run("api.server:app", host="127.0.0.1", port=8000, reload=False)
