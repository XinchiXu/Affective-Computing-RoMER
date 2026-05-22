import asyncio
import json
from typing import Dict, Optional
from datetime import datetime


class ProgressTracker:
    """进度追踪器"""

    def __init__(self):
        self._tasks: Dict[str, dict] = {}

    def create_task(self, task_id: str, task_type: str, total_steps: int = 100):
        """创建新任务"""
        self._tasks[task_id] = {
            "task_id": task_id,
            "type": task_type,
            "status": "running",
            "progress": 0,
            "total": total_steps,
            "current_step": "初始化",
            "message": "正在准备...",
            "start_time": datetime.now().isoformat(),
            "result": None,
            "error": None
        }

    def update(self, task_id: str, progress: int, step: str = "", message: str = ""):
        """更新进度"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task["progress"] = min(progress, task["total"])
            if step:
                task["current_step"] = step
            if message:
                task["message"] = message

    def complete(self, task_id: str, result: dict = None):
        """标记任务完成"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task["status"] = "completed"
            task["progress"] = task["total"]
            task["current_step"] = "完成"
            task["message"] = "识别完成"
            task["result"] = result
            task["end_time"] = datetime.now().isoformat()

    def error(self, task_id: str, error_msg: str):
        """标记任务失败"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task["status"] = "error"
            task["error"] = error_msg
            task["end_time"] = datetime.now().isoformat()

    def get_progress(self, task_id: str) -> Optional[dict]:
        """获取任务进度"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list:
        """获取所有任务"""
        return list(self._tasks.values())


# 全局进度追踪器实例
progress_tracker = ProgressTracker()
