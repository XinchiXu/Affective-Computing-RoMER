import torch
from transformers import AutoTokenizer, AutoModel, AutoFeatureExtractor
import librosa
import os, warnings, shutil
import pandas as pd
from tqdm import tqdm

warnings.filterwarnings("ignore")

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
ROBERTA_PATH, HUBERT_PATH = './data/roberta-base', './data/hubert-base'
if not os.path.exists(ROBERTA_PATH):
    AutoTokenizer.from_pretrained('roberta-base').save_pretrained('./data/roberta-base')
    AutoModel.from_pretrained('roberta-base').save_pretrained('./data/roberta-base')
if not os.path.exists(HUBERT_PATH):
    AutoFeatureExtractor.from_pretrained("facebook/hubert-base-ls960").save_pretrained("./data/hubert-base")
    AutoModel.from_pretrained("facebook/hubert-base-ls960").save_pretrained("./data/hubert-base")
tokenizer = AutoTokenizer.from_pretrained(ROBERTA_PATH)
roberta = AutoModel.from_pretrained(ROBERTA_PATH).to(DEVICE).eval()
extractor = AutoFeatureExtractor.from_pretrained(HUBERT_PATH, sample_rate=16000)
hubert = AutoModel.from_pretrained(HUBERT_PATH).to(DEVICE).eval()


def extract(mode='train', data_dir='./data/MELD'):
    df = pd.read_csv(f'{data_dir}/{mode}/{mode}.csv')
    texts, audios = [], []
    for i in tqdm(range(len(df)), desc=mode):
        dia, utt = df['Dialogue_ID'].iloc[i], df['Utterance_ID'].iloc[i]
        inp = tokenizer([df['Utterance'].iloc[i]], return_tensors='pt')
        with torch.no_grad():
            texts.append(roberta(**{k: v.to(DEVICE) for k, v in inp.items()}).last_hidden_state[0, 0].cpu())
        try:
            audio, _ = librosa.load(f'{data_dir}/{mode}/audios/dia{dia}_utt{utt}.wav', sr=16000)
            inp = extractor(audio, return_tensors='pt', sampling_rate=16000)
            with torch.no_grad():
                audios.append(hubert(**{k: v.to(DEVICE) for k, v in inp.items()}).last_hidden_state.mean(1)[0].cpu())
        except:
            audios.append(torch.zeros(768))
    torch.save(torch.stack(texts), f'{data_dir}/{mode}/{mode}_text.pt')
    torch.save(torch.stack(audios), f'{data_dir}/{mode}/{mode}_audio.pt')


def process(csv_path, img_path, audio_path, out_path, out_csv):
    df = pd.read_csv(csv_path)
    indexs = []
    for i in range(len(df)):
        dia, utt = df['Dialogue_ID'].iloc[i], df['Utterance_ID'].iloc[i]
        if os.path.exists(os.path.join(img_path, f"dia{dia}_utt{utt}")):
            if len(os.listdir(os.path.join(img_path, f"dia{dia}_utt{utt}"))) > 0:
                if not os.path.exists(os.path.join(audio_path, f"dia{dia}_utt{utt}.wav")):
                    os.remove(os.path.join(audio_path, f"dia{dia}_utt{utt}.wav"))
                    indexs.append(i)
                else:
                    shutil.copytree(os.path.join(img_path, f"dia{dia}_utt{utt}"),
                                    os.path.join(out_path, f"dia{dia}_utt{utt}"), dirs_exist_ok=True)
            else:
                if os.path.exists(os.path.join(audio_path, f"dia{dia}_utt{utt}.wav")):
                    os.remove(os.path.join(audio_path, f"dia{dia}_utt{utt}.wav"))
                indexs.append(i)
        else:
            if os.path.exists(os.path.join(audio_path, f"dia{dia}_utt{utt}.wav")):
                os.remove(os.path.join(audio_path, f"dia{dia}_utt{utt}.wav"))
            indexs.append(i)
    df = df.drop(index=indexs) if len(indexs) > 0 else df
    df.to_csv(out_csv, index=False)


if __name__ == '__main__':
    for mode in ['train', 'val']:
        extract(mode)
