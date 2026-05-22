import sys, os, cv2, numpy as np, torch, importlib.util, warnings, shutil, subprocess, glob, python_speech_features
from scipy.io import wavfile
from tqdm import tqdm
warnings.filterwarnings("ignore", category=UserWarning)

ASD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'TalkNet-ASD')
PRETRAIN = os.path.join(ASD_DIR, 'pretrain_TalkSet.model')


# --- importlib loader (bypasses sys.path entirely) ---
def _load(path, mod_name='_tmp', pkg=None):
    spec = importlib.util.spec_from_file_location(mod_name, path,
            submodule_search_locations=[os.path.dirname(path)] if pkg else None)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = pkg or ''
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# --- Load S3FD package ---
_s3fd_dir = os.path.join(ASD_DIR, 'model', 'faceDetector', 's3fd')
_s3fd_pkg = type(sys)('s3fd')
_s3fd_pkg.__path__ = [_s3fd_dir]
_s3fd_pkg.__package__ = 's3fd'
sys.modules['s3fd'] = _s3fd_pkg
_load(os.path.join(_s3fd_dir, 'box_utils.py'), 's3fd.box_utils', pkg='s3fd')
_load(os.path.join(_s3fd_dir, 'nets.py'), 's3fd.nets', pkg='s3fd')
_ns = {'__name__': 's3fd', '__package__': 's3fd', '__builtins__': __builtins__,
       'S3FDNet': sys.modules['s3fd.nets'].S3FDNet,
       'nms_': sys.modules['s3fd.box_utils'].nms_}
_orig_cwd = os.getcwd()
os.chdir(ASD_DIR)  # S3FD checks weight path relative to cwd
exec(open(os.path.join(_s3fd_dir, '__init__.py')).read(), _ns)
os.chdir(_orig_cwd)
S3FD = _ns['S3FD']

# --- Load talkNet and dependencies via importlib ---
# Remove script dir from sys.path to prevent local model.py from shadowing ASD's model/
_script_dir = sys.path.pop(0) if sys.path else ''
sys.modules['loss'] = _load(os.path.join(ASD_DIR, 'loss.py'))

_model_pkg = type(sys)('model')
_model_pkg.__path__ = [os.path.join(ASD_DIR, 'model')]
_model_pkg.__package__ = 'model'
sys.modules['model'] = _model_pkg
sys.modules['model.talkNetModel'] = _load(os.path.join(ASD_DIR, 'model', 'talkNetModel.py'))

sys.modules['talkNet'] = _load(os.path.join(ASD_DIR, 'talkNet.py'), 'talkNet')
talkNet = sys.modules['talkNet'].talkNet

# Restore script dir
sys.path.insert(0, _script_dir)

# --- Globals ---
_det = None
_speaker_net = None


def _get_detector():
    global _det
    if _det is None:
        orig_cwd = os.getcwd()
        os.chdir(ASD_DIR)
        try:
            _det = S3FD(device='cuda' if torch.cuda.is_available() else 'cpu')
        finally:
            os.chdir(orig_cwd)
    return _det


def _get_speaker_net():
    global _speaker_net
    if _speaker_net is None:
        _speaker_net = talkNet()
        _speaker_net.loadParameters(PRETRAIN)
        _speaker_net.eval()
    return _speaker_net


def detect_face_image(image_paths, conf_th=0.9, save_dir='./predict/temp/images'):
    """Detect faces, classify speaking, crop and save face images.

    Args:
        image_paths: list of image file paths
        conf_th: face detection confidence threshold
        save_dir: root directory to save cropped faces

    Returns:
        list of dicts, each with keys:
            image_id, face_id, top, bottom, left, right, speaking, crop_path
    """
    # Clear and recreate save directory
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)
    os.makedirs(save_dir, exist_ok=True)

    det = _get_detector()
    net = _get_speaker_net()
    all_results = []
    for img_idx, image_path in enumerate(image_paths):
        image = cv2.imread(image_path)
        if image is None:
            continue
        h, w = image.shape[:2]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        bboxes = det.detect_faces(rgb, conf_th=conf_th, scales=[1])

        img_dir = os.path.join(save_dir, str(img_idx)).replace('\\', '/')
        os.makedirs(img_dir, exist_ok=True)

        for face_idx, bbox in enumerate(bboxes):
            x1, y1, x2, y2, conf = bbox
            # Expand bbox by 20%
            bw, bh = x2 - x1, y2 - y1
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            ew, eh = bw * 1.2, bh * 1.2
            ex1 = max(0, int(cx - ew / 2))
            ey1 = max(0, int(cy - eh / 2))
            ex2 = min(w, int(cx + ew / 2))
            ey2 = min(h, int(cy + eh / 2))

            face_crop = image[ey1:ey2, ex1:ex2]
            face_resized = cv2.resize(face_crop, (112, 112))
            speaking = _infer_speaking(net, face_resized)

            crop_path = f'{img_dir}/{face_idx}.jpg'
            cv2.imwrite(crop_path, face_crop)

            all_results.append({
                'image_id': img_idx,
                'face_id': face_idx,
                'top': int(y1), 'bottom': int(y2),
                'left': int(x1), 'right': int(x2),
                'speaking': speaking,
                'crop_path': crop_path,
            })
    return all_results


def _infer_speaking(net, face_bgr):
    """Visual-only speaking inference for single face image."""
    gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
    face_resized = cv2.resize(gray, (112, 112))
    frames = np.stack([face_resized] * 25, axis=0)
    vid = torch.FloatTensor(frames).unsqueeze(0)
    if torch.cuda.is_available():
        vid = vid.cuda()
    with torch.no_grad():
        visEmb = net.model.forward_visual_frontend(vid)
        visEmb = net.model.forward_visual_backend(visEmb)
        logits = net.lossV.FC(visEmb)
        score = torch.softmax(logits, dim=-1)[:, 1].mean().item()
    return score > 0.5


def _infer_speaking_av(net, audio_path, face_sequence):
    """Full audio-visual speaking inference using TalkNet.

    Args:
        net: talkNet model
        audio_path: path to 16kHz mono WAV
        face_sequence: list of grayscale 112x112 face crops (one per video frame)

    Returns:
        list of per-frame speaking scores (float), or empty list on failure
    """
    if len(face_sequence) < 1:
        return []
    try:
        sr, audio = wavfile.read(audio_path)
        if audio.ndim > 1:
            audio = audio[:, 0]
        audio = audio.astype(np.float32)
        mfcc = python_speech_features.mfcc(audio, sr, numcep=13, winlen=0.025, winstep=0.010)
    except Exception:
        return []

    videoFeature = np.array(face_sequence)
    length = min((mfcc.shape[0] - mfcc.shape[0] % 4) / 100, videoFeature.shape[0] / 25)
    if length < 0.04:
        return []
    audioFeature = mfcc[:int(round(length * 100)), :]
    videoFeature = videoFeature[:int(round(length * 25)), :, :]

    inputA = torch.FloatTensor(audioFeature).unsqueeze(0)
    inputV = torch.FloatTensor(videoFeature).unsqueeze(0)
    if torch.cuda.is_available():
        inputA, inputV = inputA.cuda(), inputV.cuda()

    with torch.no_grad():
        embedA = net.model.forward_audio_frontend(inputA)
        embedV = net.model.forward_visual_frontend(inputV)
        embedA, embedV = net.model.forward_cross_attention(embedA, embedV)
        out = net.model.forward_audio_visual_backend(embedA, embedV)
        score = net.lossAV.forward(out, labels=None)
    return score.tolist()


def _get_video_duration(video_path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    return float(subprocess.check_output(cmd).strip())


def _iou(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter + 1e-6)


def _track_faces(dets_per_frame, iou_thres=0.3):
    """Simple IoU-based face tracking across frames.
    Returns list of tracks, each track = {'bbox': last_bbox, 'frames': [...]}
    """
    tracks = []
    for frame_dets in dets_per_frame:
        used = set()
        for fdet in frame_dets:
            best_iou, best_idx = 0, -1
            for ti, t in enumerate(tracks):
                if ti in used:
                    continue
                iou = _iou(fdet['bbox'], t['bbox'])
                if iou > best_iou:
                    best_iou, best_idx = iou, ti
            if best_iou >= iou_thres:
                tracks[best_idx]['bbox'] = fdet['bbox']
                tracks[best_idx]['frames'].append(fdet)
                used.add(best_idx)
            else:
                tracks.append({
                    'bbox': fdet['bbox'],
                    'frames': [fdet],
                })
    return tracks


def _parse_srt(srt_path):
    """Parse SRT subtitle file. Returns list of dicts: {id, start, end, text}."""
    entries = []
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    blocks = content.split('\n\n')
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        idx = int(lines[0].strip())
        time_parts = lines[1].strip().split(' --> ')
        start = _srt_time_to_sec(time_parts[0].strip())
        end = _srt_time_to_sec(time_parts[1].strip())
        text = '\n'.join(lines[2:]).strip()
        entries.append({'id': idx, 'start': start, 'end': end, 'text': text})
    return entries


def _srt_time_to_sec(t):
    """Convert SRT time 'HH:MM:SS,mmm' to seconds."""
    h, m, rest = t.split(':')
    s, ms = rest.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def detect_face_video(folder_path, conf_th=0.9,
                      image_dir='./predict/temp/images',
                      audio_dir='./predict/temp/audios',
                      text_dir='./predict/temp/texts'):
    """Detect speaking faces per SRT subtitle segment.

    Args:
        folder_path: folder containing one .mp4 and one .srt file
        conf_th: face detection confidence threshold

    Returns:
        list of dicts: {id, start, end, text, faces}
        where faces is a list of per-frame dicts: {time, top, bottom, left, right}
    """
    for d in [image_dir, audio_dir, text_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)

    tmp_dir = './predict/temp/_tmp_seg'
    os.makedirs(tmp_dir, exist_ok=True)

    # Find mp4 and srt files
    mp4_files = glob.glob(os.path.join(folder_path, '*.mp4'))
    srt_files = glob.glob(os.path.join(folder_path, '*.srt'))
    if not mp4_files or not srt_files:
        raise FileNotFoundError(f"Need one .mp4 and one .srt in {folder_path}")
    video_path = mp4_files[0]
    srt_path = srt_files[0]

    # Parse subtitles
    entries = _parse_srt(srt_path)

    det = _get_detector()
    net = _get_speaker_net()
    fps = 25.0
    sample_interval = 0.2

    all_results = []

    for entry in tqdm(entries):
        sid = entry['id']
        t_start = entry['start']
        t_end = entry['end']

        # Save subtitle text
        with open(f'{text_dir}/{sid}.txt', 'w', encoding='utf-8') as f:
            f.write(entry['text'])

        # Extract audio
        audio_path = f'{audio_dir}/{sid}.wav'
        subprocess.run(['ffmpeg', '-y', '-i', video_path,
                        '-ss', str(t_start), '-to', str(t_end),
                        '-ac', '1', '-ar', '16000', '-vn',
                        '-acodec', 'pcm_s16le', audio_path,
                        '-loglevel', 'error'])

        # Extract video clip
        clip_path = f'{tmp_dir}/seg.mp4'
        subprocess.run(['ffmpeg', '-y', '-i', video_path,
                        '-ss', str(t_start), '-to', str(t_end),
                        '-r', str(fps), '-c:v', 'libx264', '-preset', 'ultrafast',
                        clip_path, '-loglevel', 'error'])

        # Read all frames
        all_frames = []
        cap = cv2.VideoCapture(clip_path)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            all_frames.append(frame)
        cap.release()

        if not all_frames:
            all_results.append({'id': sid, 'start': t_start, 'end': t_end,
                                'text': entry['text'], 'faces': []})
            continue

        h, w = all_frames[0].shape[:2]
        n_total = len(all_frames)

        # Detect faces every 0.2s
        dets_per_frame = []
        detect_indices = list(range(0, n_total, int(fps * sample_interval)))
        for fi, idx in enumerate(detect_indices):
            rgb = cv2.cvtColor(all_frames[idx], cv2.COLOR_BGR2RGB)
            bboxes = det.detect_faces(rgb, conf_th=conf_th, scales=[1])
            frame_dets = []
            for bbox in bboxes:
                x1, y1, x2, y2, conf = bbox
                frame_dets.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'frame_idx': fi, 'vid_idx': idx, 'h': h, 'w': w,
                })
            dets_per_frame.append(frame_dets)

        # Track faces
        tracks = _track_faces(dets_per_frame, iou_thres=0.3)

        seg_faces = []
        img_dir = f'{image_dir}/{sid}'
        os.makedirs(img_dir, exist_ok=True)

        # Run AV inference per tracked person
        person_av_scores = {}
        for person_id, track in enumerate(tracks):
            det_bboxes = {f['frame_idx']: f for f in track['frames']}
            face_sequence = []
            for frame in all_frames:
                nearest_fi = min(det_bboxes.keys(),
                                 key=lambda k: abs(detect_indices[k] - len(face_sequence)),
                                 default=None)
                if nearest_fi is None:
                    continue
                bbox = det_bboxes[nearest_fi]['bbox']
                x1, y1, x2, y2 = bbox
                bw, bh = x2 - x1, y2 - y1
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                ew, eh = bw * 1.2, bh * 1.2
                ex1 = max(0, int(cx - ew / 2))
                ey1 = max(0, int(cy - eh / 2))
                ex2 = min(w, int(cx + ew / 2))
                ey2 = min(h, int(cy + eh / 2))
                face = frame[ey1:ey2, ex1:ex2]
                if face.size == 0:
                    continue
                face_resized = cv2.resize(face, (224, 224))
                gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
                face_sequence.append(gray[56:168, 56:168])
            av_scores = _infer_speaking_av(net, audio_path, face_sequence)
            person_av_scores[person_id] = (track, av_scores, det_bboxes)

        # For each 0.2s slot: save speaking face, or fallback to any face
        for fi in range(len(detect_indices)):
            vid_idx = detect_indices[fi]
            best_person = None
            best_fdet = None
            best_score = -999

            # Find the speaking face with highest score
            for pid, (track, av_scores, det_bboxes) in person_av_scores.items():
                if fi not in det_bboxes:
                    continue
                fdet = det_bboxes[fi]
                vidx = fdet['vid_idx']
                score = av_scores[vid_idx] if av_scores and vidx < len(av_scores) else -999
                if score > best_score:
                    best_score = score
                    best_person = pid
                    best_fdet = fdet

            # If no tracked face at this slot, pick from any person with nearest detection
            if best_fdet is None:
                for pid, (track, av_scores, det_bboxes) in person_av_scores.items():
                    if not det_bboxes:
                        continue
                    nearest_fi = min(det_bboxes.keys(), key=lambda k: abs(k - fi))
                    fdet = det_bboxes[nearest_fi]
                    vidx = fdet['vid_idx']
                    score = av_scores[vidx] if av_scores and vidx < len(av_scores) else -999
                    if score > best_score:
                        best_score = score
                        best_person = pid
                        best_fdet = fdet

            if best_fdet is None:
                continue

            x1, y1, x2, y2 = best_fdet['bbox']
            bw, bh = x2 - x1, y2 - y1
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            ew, eh = bw * 1.2, bh * 1.2
            ex1 = max(0, int(cx - ew / 2))
            ey1 = max(0, int(cy - eh / 2))
            ex2 = min(w, int(cx + ew / 2))
            ey2 = min(h, int(cy + eh / 2))
            face_crop = all_frames[vid_idx][ey1:ey2, ex1:ex2]
            crop_path = f'{img_dir}/{best_person}_{fi}.jpg'
            cv2.imwrite(crop_path, face_crop)
            seg_faces.append({
                'time': round(vid_idx / fps + t_start, 2),
                'top': y1, 'bottom': y2, 'left': x1, 'right': x2,
            })

        all_results.append({
            'id': sid, 'start': t_start, 'end': t_end,
            'text': entry['text'], 'faces': seg_faces,
        })

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return all_results


def _main():
    if len(sys.argv) < 2:
        print("Usage: python detect.py <image|folder>")
        sys.exit(1)
    path = sys.argv[1]
    if os.path.isdir(path):
        results = detect_face_video(path)
        for r in results:
            print(f"[{r['id']}] {r['start']:.1f}-{r['end']:.1f}s "
                  f"faces={len(r['faces'])} text={r['text'][:30]}")
    else:
        results = detect_face_image([path])
        for r in results:
            print(r)
    if not results:
        print("No faces detected.")

if __name__ == '__main__':
    _main()
