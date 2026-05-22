import os
import sys
import cv2
import shutil
import torch
import numpy as np
from pathlib import Path
from typing import Optional
from torch.utils.data import DataLoader
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent))

from predict import (
    detect_face_image, detect_face_video,
    COLORS, EMOTIONS, MEDataset, collate_fn, DEVICE, model
)
from dataset import EMOTIONS as EMOTIONS_LIST
from backend.progress_tracker import progress_tracker
from tqdm import tqdm


def get_emotions_with_probs(type, paths, batch_size):
    """获取情感识别结果及完整概率分布"""
    face_dataset = MEDataset(type=type, paths=paths)
    dataloader = DataLoader(face_dataset, batch_size=batch_size, collate_fn=collate_fn, shuffle=False)
    results, scores, all_probs = [], [], []

    for imgs, text, audio, lengths in tqdm(dataloader):
        imgs, text, audio = imgs.to(DEVICE), text.to(DEVICE), audio.to(DEVICE)
        output = model(imgs, lengths, text, audio)
        probs = torch.softmax(output, dim=1)
        conf, pred = probs.max(1)
        results.extend(pred.tolist())
        scores.extend(conf.tolist())
        all_probs.extend(probs.cpu().tolist())

    emotions = [EMOTIONS[r] for r in results]
    # 构建概率分布字典
    prob_distributions = []
    for prob in all_probs:
        dist = {EMOTIONS[i]: round(p, 4) for i, p in enumerate(prob)}
        prob_distributions.append(dist)

    return emotions, scores, prob_distributions


def extract_keyframes(video_path: str, output_dir: str, num_frames: int = 6):
    """从视频中提取关键帧"""
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # 均匀采样关键帧
    frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
    keyframes = []

    for idx, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            filename = f"frame_{idx:02d}.jpg"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, frame)
            keyframes.append({
                "filename": filename,
                "time": round(frame_idx / fps, 2) if fps > 0 else 0,
                "url": f"/api/keyframe/{os.path.basename(output_dir)}/{filename}"
            })

    cap.release()
    return keyframes


def generate_annotated_video(folder_path, faces, emotions, scores, video_name, task_id=None):
    """生成标注视频（不重复调用 predict_emotion）"""
    import subprocess
    from predict import COLORS

    video_path = os.path.join(folder_path, video_name)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w, h = int(cap.get(3)), int(cap.get(4))

    # 先生成临时视频（使用 mp4v 编码）
    temp_path = os.path.join('.', 'predict', 'result', f'temp_{video_name}')
    result_path = os.path.join('.', 'predict', 'result', video_name)
    out = cv2.VideoWriter(temp_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    frame_idx = 0
    with tqdm(total=total_frames) as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            t = frame_idx / fps

            # 更新进度（每100帧更新一次）
            if task_id and frame_idx % 100 == 0:
                progress = 70 + int(20 * frame_idx / total_frames)
                progress_tracker.update(task_id, progress, "视频处理",
                                       f"正在生成标注视频... {frame_idx}/{total_frames}")

            for idx, face in enumerate(faces):
                if idx >= len(emotions):
                    continue
                text = f'{emotions[idx]} {scores[idx]:.2f}'
                color = COLORS[emotions[idx]][::-1]  # BGR for OpenCV
                (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)

                if face['start'] <= t <= face['end']:
                    for f in face['faces']:
                        if f['time'] <= t <= f['time'] + 0.2 and f['time'] + 0.2 <= face['end']:
                            cv2.rectangle(frame, (f['left'], f['top']), (f['right'], f['bottom']), color, 2)
                            cv2.putText(frame, text, (f['right'] + 2, f['top'] + text_h),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            out.write(frame)
            frame_idx += 1
            pbar.update(1)

    cap.release()
    out.release()

    # 使用 ffmpeg 转换为 H.264 编码（浏览器兼容）
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_path,
            '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '23', '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            result_path
        ], capture_output=True, check=True)
        # 删除临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # 如果 ffmpeg 失败，直接使用原始文件
        if os.path.exists(temp_path):
            os.rename(temp_path, result_path)

    return result_path


def predict_image_detail(paths, batch_size=2, task_id=None):
    """图片情感识别，返回详细结果及概率分布"""
    if task_id:
        progress_tracker.update(task_id, 10, "人脸检测", "正在检测人脸...")

    faces = detect_face_image(paths)
    face_paths = [f['crop_path'] for f in faces]

    if task_id:
        progress_tracker.update(task_id, 40, "情感识别", f"检测到 {len(faces)} 张人脸，正在识别情感...")

    emotions, scores, prob_distributions = get_emotions_with_probs('images', face_paths, batch_size)

    if task_id:
        progress_tracker.update(task_id, 80, "结果整理", "正在整理识别结果...")

    # 获取图片尺寸
    image_sizes = {}
    for path in paths:
        try:
            img = Image.open(path)
            image_sizes[os.path.basename(path)] = img.size  # (width, height)
        except:
            pass

    results = []
    for idx, face in enumerate(faces):
        img_path = paths[face['image_id']]
        filename = os.path.basename(img_path)
        results.append({
            'image_id': face['image_id'],
            'filename': filename,
            'face_id': face['face_id'],
            'bbox': {
                'top': face['top'],
                'bottom': face['bottom'],
                'left': face['left'],
                'right': face['right']
            },
            'image_size': image_sizes.get(filename, (640, 480)),
            'emotion': emotions[idx],
            'confidence': round(scores[idx], 4),
            'color': list(COLORS[emotions[idx]]),
            'probabilities': prob_distributions[idx]
        })

    # 统计情感分布
    emotion_counts = {}
    for e in EMOTIONS_LIST:
        count = sum(1 for r in results if r['emotion'] == e)
        if count > 0:
            emotion_counts[e] = count

    if task_id:
        progress_tracker.update(task_id, 100, "完成", "识别完成")

    return {
        'details': results,
        'summary': {
            'total_faces': len(results),
            'emotion_distribution': emotion_counts,
            'images_processed': len(paths)
        }
    }


def predict_video_detail(folder_path, batch_size=2, task_id=None):
    """视频情感识别，返回详细结果及概率分布"""

    if task_id:
        progress_tracker.update(task_id, 5, "预处理", "正在解析字幕文件...")

    tqdm.write('[预处理] 正在根据字幕文件切分视频并提取人脸')

    if task_id:
        progress_tracker.update(task_id, 10, "人脸检测", "正在检测视频中的人脸，这可能需要几分钟...")

    faces = [f for f in detect_face_video(folder_path=folder_path) if len(f['faces']) > 0]
    face_paths = [f['id'] for f in faces]

    if task_id:
        progress_tracker.update(task_id, 40, "人脸检测", f"检测到 {len(faces)} 个视频片段")

    tqdm.write('[模型提取] 正在获取各视频分段中说话人的面部表情')
    emotions, scores, prob_distributions = get_emotions_with_probs('video', face_paths, batch_size)
    tqdm.write(', '.join([e for e in emotions]))

    if task_id:
        progress_tracker.update(task_id, 50, "情感识别", "情感识别完成")

    # 构建详细结果
    segments = []
    for idx, face in enumerate(faces):
        segments.append({
            'id': face['id'],
            'start': round(face['start'], 2),
            'end': round(face['end'], 2),
            'duration': round(face['end'] - face['start'], 2),
            'text': face['text'],
            'emotion': emotions[idx],
            'confidence': round(scores[idx], 4),
            'color': list(COLORS[emotions[idx]]),
            'face_count': len(face['faces']),
            'probabilities': prob_distributions[idx]
        })

    # 情感分布统计
    emotion_counts = {}
    emotion_duration = {}
    for seg in segments:
        e = seg['emotion']
        emotion_counts[e] = emotion_counts.get(e, 0) + 1
        emotion_duration[e] = emotion_duration.get(e, 0) + seg['duration']

    # 情感变化时间线
    timeline = [{
        'time': seg['start'],
        'emotion': seg['emotion'],
        'confidence': seg['confidence']
    } for seg in segments]

    if task_id:
        progress_tracker.update(task_id, 60, "视频处理", "正在生成标注视频...")

    # 生成结果视频（直接调用，不重复预测）
    video_name = [f for f in os.listdir(folder_path) if f.endswith('.mp4')][0]
    result_path = generate_annotated_video(folder_path, faces, emotions, scores, video_name, task_id)

    if task_id:
        progress_tracker.update(task_id, 90, "关键帧提取", "正在提取关键帧...")

    # 提取关键帧
    keyframe_dir = os.path.join('.', 'predict', 'result', f'keyframes_{video_name.split(".")[0]}')
    keyframes = []
    if result_path and os.path.exists(result_path):
        keyframes = extract_keyframes(result_path, keyframe_dir, num_frames=8)

    if task_id:
        progress_tracker.update(task_id, 100, "完成", "识别完成")

    return {
        'video_filename': video_name,
        'segments': segments,
        'keyframes': keyframes,
        'summary': {
            'total_segments': len(segments),
            'total_duration': round(sum(s['duration'] for s in segments), 2),
            'emotion_counts': emotion_counts,
            'emotion_duration': {k: round(v, 2) for k, v in emotion_duration.items()},
            'timeline': timeline
        }
    }
