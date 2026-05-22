import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
import os, random, warnings
import pandas as pd

warnings.filterwarnings("ignore")

EMOTIONS = ['surprise', 'joy', 'neutral', 'sadness', 'anger', 'disgust', 'fear']
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class MELD(Dataset):
    def __init__(self, mode='train', meld_dir='./data/MELD', max_frames=64):
        self.path = f'{meld_dir}/{mode}'
        self.max_frames = max_frames
        self.df = pd.read_csv(f'{self.path}/{mode}.csv')
        self.text_embeddings = torch.load(f'{self.path}/{mode}_text.pt')
        self.audio_embeddings = torch.load(f'{self.path}/{mode}_audio.pt')
        if mode == 'train':
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.RandomCrop(224),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(15),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
                transforms.RandomGrayscale(p=0.2),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])

    def __len__(self):
        return len(self.df)

    def _sample(self, imgs):
        k, n = len(imgs), self.max_frames
        # return imgs if k <= n else [imgs[i * (k - 1) // (n - 1)] for i in range(n)]  # Method 1
        # return imgs if k <= n else [imgs[i] for i in sorted(random.sample(range(k), n))]  # Method 2
        return imgs if k <= n else imgs[random.randint(0, k - n):][:n]  # Method 3

    def __getitem__(self, idx):
        dia, utt = self.df['Dialogue_ID'].iloc[idx], self.df['Utterance_ID'].iloc[idx]
        imgs, imgs_path, seed = [], f'{self.path}/images/dia{dia}_utt{utt}', random.randint(0, 2 ** 32)
        for img_path in self._sample(os.listdir(imgs_path)):
            random.seed(seed)
            torch.manual_seed(seed)
            imgs.append(self.transform(Image.open(f"{imgs_path}/{img_path}").convert('RGB')))
        text_embedding = self.text_embeddings[None, idx] if random.random() > -0.3 else torch.zeros((1, 768))
        audio_embedding = self.audio_embeddings[None, idx] if random.random() > -0.3 else torch.zeros((1, 768))
        emotion = EMOTIONS.index(self.df['Emotion'].iloc[idx])
        return torch.stack(imgs, dim=0), text_embedding, audio_embedding, emotion


def collate_fn(batch):
    images, texts, audios, emotions = zip(*batch)
    lengths = [img.shape[0] for img in images]
    return torch.cat(images), torch.stack(texts), torch.stack(audios), torch.tensor(emotions), torch.tensor(lengths)
