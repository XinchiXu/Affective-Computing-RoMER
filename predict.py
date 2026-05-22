import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image, ImageDraw, ImageFont
from model import RoMER
from dataset import EMOTIONS
from transformers import AutoTokenizer, AutoModel, AutoFeatureExtractor
from detect import detect_face_image, detect_face_video
import librosa
import cv2
import os, warnings
import hashlib, time, uuid, requests
from tqdm import tqdm

warnings.filterwarnings("ignore")

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_PATH = './weights/best_model_acc.pth'
model = RoMER().to(DEVICE)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()
ROBERTA_PATH, HUBERT_PATH = './data/roberta-base', './data/hubert-base'
tokenizer = AutoTokenizer.from_pretrained(ROBERTA_PATH)
roberta = AutoModel.from_pretrained(ROBERTA_PATH).to(DEVICE).eval()
extractor = AutoFeatureExtractor.from_pretrained(HUBERT_PATH, sampling_rate=16000)
hubert = AutoModel.from_pretrained(HUBERT_PATH).to(DEVICE).eval()
COLORS = {'surprise': (249, 134, 168), 'joy': (154, 219, 197), 'neutral': (251, 241, 215), 'sadness': (132, 119, 198),
          'anger': (254, 141, 111), 'disgust': (178, 207, 152), 'fear': (114, 188, 236)}


def translate(text, appKey='', appSecret=''):
    q = text[:10] + str(len(text)) + text[-10:] if len(text) > 20 else text
    salt, curtime = str(uuid.uuid4()), str(int(time.time()))
    sign = hashlib.sha256((appKey + q + salt + curtime + appSecret).encode()).hexdigest()
    r = requests.post('https://openapi.youdao.com/api', data={
        'q': text, 'from': 'auto', 'to': 'en',
        'appKey': appKey, 'salt': salt, 'sign': sign,
        'signType': 'v3', 'curtime': curtime
    })
    return r.json().get('translation', [''])[0]


class MEDataset(Dataset):
    def __init__(self, type='images', paths=None, max_frames=64):
        self.type = type
        self.paths = paths
        self.max_frames = max_frames
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        imgs, text_embedding, audio_embedding = [], torch.zeros((1, 768)), torch.zeros((1, 768))
        if self.type == 'images':
            imgs.append(self.transform(Image.open(self.paths[idx]).convert('RGB')))
        elif self.type == 'video':
            path = f"./predict/temp/images/{self.paths[idx]}"
            for img in os.listdir(path)[:self.max_frames]:
                imgs.append(self.transform(Image.open(f"{path}/{img}").convert('RGB')))
            with open(f'./predict/temp/texts/{self.paths[idx]}.txt', 'r', encoding='utf-8') as f:
                text_input = tokenizer([translate(f.read())], padding=True, truncation=True, return_tensors='pt')
            text_embedding = roberta(**{k: v.to(DEVICE) for k, v in text_input.items()}).last_hidden_state[:, 0, :]
            audio, _ = librosa.load(f'./predict/temp/audios/{self.paths[idx]}.wav', sr=16000)
            audio_input = extractor(audio, return_tensors='pt', sampling_rate=16000)
            audio_embedding = hubert(**{k: v.to(DEVICE) for k, v in audio_input.items()}).last_hidden_state.mean(1)
        return torch.stack(imgs, dim=0), text_embedding, audio_embedding


def collate_fn(batch):
    images, texts, audios = zip(*batch)
    lengths = [img.shape[0] for img in images]
    return torch.cat(images), torch.stack(texts), torch.stack(audios), torch.tensor(lengths)


@torch.no_grad()
def get_emotions(type, paths, batch_size):
    face_dataset = MEDataset(type=type, paths=paths)
    dataloader = DataLoader(face_dataset, batch_size=batch_size, collate_fn=collate_fn, shuffle=False)
    results, scores = [], []
    for imgs, text, audio, lengths in tqdm(dataloader):
        imgs, text, audio = imgs.to(DEVICE), text.to(DEVICE), audio.to(DEVICE)
        output = model(imgs, lengths, text, audio)
        probs = torch.softmax(output, dim=1)
        conf, pred = probs.max(1)
        results.extend(pred.tolist())
        scores.extend(conf.tolist())
    return [EMOTIONS[r] for r in results], scores


def predict_emotion(type='images', paths=None, batch_size=2):
    if type == 'images':
        faces = detect_face_image(paths)
        face_paths = [f['crop_path'] for f in faces]
        emotions, scores = get_emotions(type, face_paths, batch_size)
        for idx1, img_path in enumerate(paths):
            img = Image.open(img_path)
            draw = ImageDraw.Draw(img)
            for idx2, face in enumerate(faces):
                if face['image_id'] == idx1:
                    text, color = f'{emotions[idx2]} {scores[idx2]:.2f}', COLORS[emotions[idx2]]
                    draw.rectangle([face['left'], face['top'], face['right'], face['bottom']], outline=color, width=2)
                    font = ImageFont.truetype("arial.ttf", size=20)
                    draw.text((face['right'] + 2, face['top']), text, fill=color, font=font)
            img.save(f"./predict/result/{img_path.split('/')[-1]}")
    elif type == 'video':
        tqdm.write('[预处理] 正在根据字幕文件切分视频并提取人脸')
        faces = [f for f in detect_face_video(folder_path=paths) if len(f['faces']) > 0]
        face_paths = [f['id'] for f in faces]
        tqdm.write('[模型提取] 正在获取各视频分段中说话人的面部表情')
        emotions, scores = get_emotions(type, face_paths, batch_size)
        tqdm.write('[可视化结果] 正在绘制识别结果并导出视频')
        video_name = [f for f in os.listdir(paths) if f.endswith('.mp4')][0]
        cap = cv2.VideoCapture(f'{paths}/{video_name}')
        fps, frames = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w, h, frame_idx = int(cap.get(3)), int(cap.get(4)), 0
        out = cv2.VideoWriter(f'./predict/result/{video_name}', cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
        with tqdm(total=frames) as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                t = frame_idx / fps
                for idx, face in enumerate(faces):
                    text, color = f'{emotions[idx]} {scores[idx]:.2f}', COLORS[emotions[idx]][::-1]
                    (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
                    if face['start'] <= t <= face['end']:
                        for f in face['faces']:
                            if f['time'] <= t <= f['time'] + 0.2 and f['time'] + 0.2 <= face['end']:
                                cv2.rectangle(frame, (f['left'], f['top']), (f['right'], f['bottom']), color, 2)
                                cv2.putText(frame, text, (f['right'] + 2, f['top'] + text_h), cv2.FONT_HERSHEY_SIMPLEX,
                                            1, color, 2)
                out.write(frame)
                frame_idx += 1
                pbar.update(1)
            cap.release()
            out.release()
        tqdm.write(f'[完成] 结果视频已保存到: ./predict/result/{video_name}')


if __name__ == '__main__':
    images = [f'./predict/images/{img}' for img in os.listdir('./predict/images/')]
    predict_emotion(type='images', paths=images)
    paths = './predict/videos/1'
    predict_emotion(type='video', paths=paths)
