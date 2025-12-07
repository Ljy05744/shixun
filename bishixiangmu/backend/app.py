"""
AI增强型任务管理系统 - 后端API主程序
使用 FastAPI + SQLite + AI 解析
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional, List
import uvicorn

# 导入自定义模块
from database import (
    init_database, get_all_tasks, get_task_by_id,
    create_task, update_task, delete_task, get_task_stats
)
from ai_parser import AITaskParser

# ========== 初始化应用 ==========
app = FastAPI(
    title="AI增强型任务管理系统",
    description="支持自然语言解析的智能任务管理API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_database()

# 初始化AI解析器
ai_parser = AITaskParser()

# ========== 数据模型定义 ==========
class TaskStatus(str):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")
    status: str = Field("pending", description="任务状态: pending, in_progress, completed")
    due_date: Optional[date] = Field(None, description="截止日期")
    priority: int = Field(3, ge=1, le=5, description="优先级: 1-5，1最高")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed)$")
    due_date: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=5)

class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PriorityRecommendation(BaseModel):
    current_priority: int
    recommended_priority: int
    reason: str
    confidence: float = Field(0.0, ge=0.0, le=1.0)

class NaturalLanguageRequest(BaseModel):
    text: str = Field(..., description="自然语言描述的任务")

class AIResponse(BaseModel):
    success: bool
    result: TaskBase
    message: str

class StatsResponse(BaseModel):
    total: int
    completed: int
    pending: int
    in_progress: int
    overdue: int
    completion_rate: float

# ========== API路由定义 ==========

@app.get("/", tags=["根路径"])
async def root():
    """API根路径，返回基本信息"""
    return {
        "message": "🎉 AI增强型任务管理系统API",
        "version": "1.0.0",
        "author": "深势科技笔试项目",
        "endpoints": {
            "文档": "/docs",
            "健康检查": "/health",
            "任务列表": "/api/tasks",
            "AI解析": "/api/ai/parse",
            "统计信息": "/api/stats"
        }
    }

@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ai-task-manager"
    }

@app.get("/api/tasks", response_model=List[TaskResponse], tags=["任务管理"])
async def read_tasks(status: Optional[str] = None):
    """
    获取任务列表

    - **status**: 可选，按状态筛选 (pending, in_progress, completed)
    """
    try:
        tasks = get_all_tasks(status)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")

@app.get("/api/tasks/{task_id}", response_model=TaskResponse, tags=["任务管理"])
async def read_task(task_id: int):
    """
    获取单个任务详情
    """
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@app.post("/api/tasks", response_model=TaskResponse, tags=["任务管理"])
async def create_new_task(task: TaskCreate):
    """
    创建新任务
    """
    try:
        task_data = task.model_dump()
        new_task = create_task(task_data)
        return new_task
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建任务失败: {str(e)}")

@app.put("/api/tasks/{task_id}", response_model=TaskResponse, tags=["任务管理"])
async def update_existing_task(task_id: int, task_update: TaskUpdate):
    """
    更新任务信息
    """
    update_data = {k: v for k, v in task_update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="没有提供更新数据")

    updated_task = update_task(task_id, update_data)
    if not updated_task:
        raise HTTPException(status_code=404, detail="任务不存在或更新失败")

    return updated_task

@app.delete("/api/tasks/{task_id}", tags=["任务管理"])
async def remove_task(task_id: int):
    """
    删除任务
    """
    success = delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {"success": True, "message": "任务删除成功", "task_id": task_id}

@app.post("/api/ai/parse", response_model=AIResponse, tags=["AI功能"])
async def parse_natural_language(request: NaturalLanguageRequest):
    """
    AI解析自然语言为任务

    示例输入:
    ```
    {
        "text": "明天下午3点开会讨论项目进度"
    }
    ```
    """
    try:
        # 使用AI解析器解析文本
        parsed_data = ai_parser.parse(request.text)

        # 验证数据
        validated_data = ai_parser.validate_task_data(parsed_data)

        return AIResponse(
            success=True,
            result=TaskBase(**validated_data),
            message="AI解析成功" if ai_parser.use_real_api else "模拟AI解析成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI解析失败: {str(e)}")

@app.post("/api/ai/create", response_model=TaskResponse, tags=["AI功能"])
async def create_task_from_natural_language(request: NaturalLanguageRequest):
    """
    直接从自然语言创建任务（一步完成）
    """
    try:
        # 解析自然语言
        parsed_data = ai_parser.parse(request.text)
        validated_data = ai_parser.validate_task_data(parsed_data)

        # 创建任务
        new_task = create_task(validated_data)

        return new_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@app.get("/api/stats", response_model=StatsResponse, tags=["统计"])
async def get_statistics():
    """
    获取任务统计信息
    """
    try:
        stats = get_task_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 在现有API路由后添加：

@app.get("/api/tasks/{task_id}/priority-recommendation", response_model=PriorityRecommendation, tags=["AI功能"])
async def get_priority_recommendation(task_id: int):
    """
    获取任务的AI优先级推荐
    """
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 使用AI解析器推荐优先级
    recommended = ai_parser.recommend_priority(task)

    # 生成推荐理由
    reasons = {
        1: "任务紧急，建议立即处理",
        2: "任务重要，建议优先处理",
        3: "任务正常，可按计划处理",
        4: "任务不急，可以稍后处理",
        5: "任务无时间限制，空闲时处理"
    }

    # 计算置信度（基于截止日期和关键词）
    confidence = 0.7  # 基础置信度
    if task.get("due_date"):
        confidence += 0.2
    if task.get("description") and len(task.get("description", "")) > 10:
        confidence += 0.1

    return PriorityRecommendation(
        current_priority=task.get("priority", 3),
        recommended_priority=recommended,
        reason=reasons.get(recommended, "基于AI分析推荐"),
        confidence=min(confidence, 1.0)
    )


@app.put("/api/tasks/{task_id}/auto-prioritize", response_model=TaskResponse, tags=["AI功能"])
async def auto_prioritize_task(task_id: int):
    """
    让AI自动调整任务优先级
    """
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取AI推荐优先级
    recommended = ai_parser.recommend_priority(task)

    # 更新任务优先级
    update_data = {"priority": recommended}
    updated_task = update_task(task_id, update_data)

    if not updated_task:
        raise HTTPException(status_code=500, detail="优先级更新失败")

    return updated_task

# ========== 启动服务器 ==========
if __name__ == "__main__":
    print("=" * 70)
    print("🤖 AI增强型任务管理系统 - 后端服务器")
    print("=" * 70)
    print("作者: 深势科技笔试项目")
    print("技术栈: FastAPI + SQLite + AI解析")
    print("=" * 70)
    print("📌 服务器地址: http://localhost:8080")
    print("📚 交互式文档: http://localhost:8080/docs")
    print("📖 ReDoc文档: http://localhost:8080/redoc")
    print("=" * 70)
    print("📋 可用端点:")
    print("  GET  /                    - API信息")
    print("  GET  /health              - 健康检查")
    print("  GET  /api/tasks           - 获取任务列表")
    print("  POST /api/tasks           - 创建任务")
    print("  POST /api/ai/parse        - AI解析自然语言")
    print("  POST /api/ai/create       - AI直接创建任务")
    print("  GET  /api/stats           - 统计信息")
    print("=" * 70)
    print("按下 Ctrl+C 停止服务器")
    print("=" * 70)

    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )