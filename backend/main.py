import os
import sys
import shutil
import uuid
import asyncio
import json
import threading
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

# Add parent directory to path to import predict module
sys.path.insert(0, str(Path(__file__).parent.parent))

from predict import predict_emotion, COLORS, EMOTIONS
from backend.predict_detail import predict_image_detail, predict_video_detail
from backend.progress_tracker import progress_tracker

UPLOAD_DIR = Path(__file__).parent / "uploads"
RESULT_DIR = Path(__file__).parent.parent / "predict" / "result"
HISTORY_DIR = Path(__file__).parent / "history"

@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(exist_ok=True)
    yield

app = FastAPI(title="情感识别 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_predict_in_background(task_id, task_type, func, *args, **kwargs):
    """在后台线程中运行预测任务"""
    try:
        result = func(*args, task_id=task_id, **kwargs)
        progress_tracker.complete(task_id, result)
        # 保存历史记录
        history = {
            "task_id": task_id,
            "type": task_type,
            "detail": result
        }
        with open(HISTORY_DIR / f"{task_id}.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        progress_tracker.error(task_id, str(e))


@app.get("/")
async def root():
    return {"message": "情感识别 API 服务运行中"}


@app.get("/api/emotions")
async def get_emotions():
    """获取支持的情感类型列表"""
    emotion_labels = {
        'surprise': '惊讶', 'joy': '快乐', 'neutral': '中性',
        'sadness': '悲伤', 'anger': '愤怒', 'disgust': '厌恶', 'fear': '恐惧'
    }
    return {
        "emotions": EMOTIONS,
        "labels": emotion_labels,
        "colors": {k: list(v) for k, v in COLORS.items()}
    }


@app.post("/api/predict/image")
async def predict_image(files: List[UploadFile] = File(...)):
    """上传图片进行情感识别"""
    task_id = uuid.uuid4().hex[:8]
    task_dir = UPLOAD_DIR / task_id
    task_dir.mkdir(exist_ok=True)

    try:
        image_paths = []
        for file in files:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(400, f"文件 {file.filename} 不是图片")
            file_path = task_dir / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            image_paths.append(str(file_path).replace("\\", "/"))

        # 创建进度任务
        progress_tracker.create_task(task_id, "image", 100)

        # 后台运行预测
        thread = threading.Thread(
            target=run_predict_in_background,
            args=(task_id, "image", predict_image_detail, image_paths),
            kwargs={"batch_size": 2}
        )
        thread.start()

        return {"task_id": task_id, "message": "识别任务已启动"}
    except Exception as e:
        progress_tracker.error(task_id, str(e))
        raise HTTPException(500, f"预测失败: {str(e)}")


@app.post("/api/predict/video")
async def predict_video(
    video: UploadFile = File(...),
    subtitle: UploadFile = File(...)
):
    """上传视频和字幕进行情感识别"""
    task_id = uuid.uuid4().hex[:8]
    task_dir = UPLOAD_DIR / task_id
    task_dir.mkdir(exist_ok=True)

    try:
        if not video.filename.endswith((".mp4", ".avi", ".mov")):
            raise HTTPException(400, "视频文件格式不支持，请上传 mp4/avi/mov 格式")
        if not subtitle.filename.endswith(".srt"):
            raise HTTPException(400, "字幕文件格式不支持，请上传 srt 格式")

        video_path = task_dir / video.filename
        subtitle_path = task_dir / subtitle.filename

        with open(video_path, "wb") as f:
            f.write(await video.read())
        with open(subtitle_path, "wb") as f:
            f.write(await subtitle.read())

        # 创建进度任务
        progress_tracker.create_task(task_id, "video", 100)

        # 后台运行预测
        thread = threading.Thread(
            target=run_predict_in_background,
            args=(task_id, "video", predict_video_detail, str(task_dir)),
            kwargs={"batch_size": 2}
        )
        thread.start()

        return {"task_id": task_id, "message": "识别任务已启动"}
    except Exception as e:
        progress_tracker.error(task_id, str(e))
        raise HTTPException(500, f"预测失败: {str(e)}")


@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """获取任务进度"""
    progress = progress_tracker.get_progress(task_id)
    if not progress:
        raise HTTPException(404, "任务不存在")
    return progress


@app.get("/api/result/{file_type}/{filename}")
async def get_result(file_type: str, filename: str):
    """获取结果文件"""
    file_path = RESULT_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "结果文件不存在")

    if file_type == "image":
        media_type = "image/jpeg" if filename.endswith(".jpg") else "image/png"
    elif file_type == "video":
        media_type = "video/mp4"
    else:
        raise HTTPException(400, "不支持的文件类型")

    return FileResponse(
        file_path,
        media_type=media_type,
        headers={"Accept-Ranges": "bytes"}
    )


@app.get("/api/keyframe/{folder}/{filename}")
async def get_keyframe(folder: str, filename: str):
    """获取关键帧图片"""
    file_path = RESULT_DIR / folder / filename
    if not file_path.exists():
        raise HTTPException(404, "关键帧不存在")
    return FileResponse(file_path, media_type="image/jpeg")


@app.get("/api/history")
async def get_history():
    """获取历史记录列表"""
    history_list = []
    for file in sorted(HISTORY_DIR.glob("*.json"), reverse=True):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            history_list.append({
                "task_id": data.get("task_id"),
                "type": data.get("type"),
                "timestamp": file.stat().st_mtime
            })
    return {"history": history_list[:20]}


@app.get("/api/history/{task_id}")
async def get_history_detail(task_id: str):
    """获取历史记录详情"""
    file_path = HISTORY_DIR / f"{task_id}.json"
    if not file_path.exists():
        raise HTTPException(404, "历史记录不存在")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
