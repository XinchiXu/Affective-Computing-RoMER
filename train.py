import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import LinearLR, CosineAnnealingWarmRestarts
from torch.utils.data import DataLoader
from model import RoMER
from dataset import MELD, collate_fn, EMOTIONS
from sklearn.metrics import f1_score
import os, logging, argparse
from tqdm import tqdm

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
BEST_MODEL_ACC, BEST_MODEL_WF1, LAST_CHECKPOINT = './weights/best_model_acc.pth', './weights/best_model_wf1.pth', './weights/last_checkpoint.pth'
os.makedirs('./weights', exist_ok=True)


def setup_logging(log_id, log_dir='./logs'):
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(f"./logs/train_{log_id:02d}.log", encoding="utf-8", mode="a"),
            logging.StreamHandler()
        ]
    )


def train(num_epochs, batch_size, log_id):
    setup_logging(log_id=log_id)
    train_dataset, val_dataset = MELD(mode='train'), MELD(mode='val')
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)
    model = RoMER().to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01, betas=(0.9, 0.98), eps=1e-9)
    counts = torch.tensor([train_dataset.df['Emotion'].value_counts()[emotion] for emotion in EMOTIONS], device=DEVICE)
    class_weigths = counts.sum() / (len(EMOTIONS) * counts)
    criterion = nn.CrossEntropyLoss(weight=class_weigths, label_smoothing=0.1)
    iters1, iters2 = len(train_loader) * 10, len(train_loader) * 30
    warmup = LinearLR(optimizer, start_factor=0.1, total_iters=iters1)
    cosine = CosineAnnealingWarmRestarts(optimizer, T_0=iters2, T_mult=2, eta_min=1e-6)
    scheduler = optim.lr_scheduler.SequentialLR(optimizer, schedulers=[warmup, cosine], milestones=[iters1])
    crt_epoch, best_acc, best_wf1 = 0, 0.0, 0.0
    if os.path.exists(LAST_CHECKPOINT):
        checkpoint = torch.load(LAST_CHECKPOINT, map_location=DEVICE)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        crt_epoch, best_acc, best_wf1 = checkpoint['crt_epoch'], checkpoint['best_acc'], checkpoint['best_wf1']
    for epoch in range(crt_epoch, num_epochs):
        torch.cuda.empty_cache()
        model.train()
        train_loss, val_loss, total, correct, preds, labels = 0.0, 0.0, 0, 0, [], []
        tqdm.write(f"{'Epoch':>10}{'Batch':>10}{'B_size':>10}{'I_num':>10}{'I_size':>10}{'T_size':>10}{'A_size':>10}"
                   f"{'GPU_mem':>10}{'Loss':>10}{'Avg_loss':>10}{'LR':>10}")
        bar = tqdm(enumerate(train_loader), total=len(train_loader))
        for batch_idx, (imgs, text, audio, emotion, lengths) in bar:
            imgs, text, audio, emotion = imgs.to(DEVICE), text.to(DEVICE), audio.to(DEVICE), emotion.to(DEVICE)
            optimizer.zero_grad()
            output = model(imgs, lengths, text, audio)
            loss = criterion(output, emotion)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            train_loss += loss.item()
            mem = f"{torch.cuda.memory_reserved() / 1E9 if torch.cuda.is_available() else 0:.3g}G"
            lr = f"{optimizer.param_groups[0]['lr'] * 10000:.3g}e-4"
            avg_loss = train_loss / (batch_idx + 1)
            s = f"{f'{epoch + 1}/{num_epochs}':>10}{f'{batch_idx + 1}/{len(train_loader)}':>10}{text.shape[0]:>10}{imgs.shape[0]:>10}{f'c{imgs.shape[1]}hw{imgs.shape[-1]}':>10}{f'n{text.shape[1]}d{text.shape[2]}':>10}{f'n{audio.shape[1]}d{audio.shape[2]}':>10}{mem:>10}{loss.item():>10.4f}{avg_loss:>10.4f}{lr:>10}"
            bar.set_description(s)
        model.eval()
        tqdm.write(f"{'Epoch':>10}{'Batch':>10}{'B_size':>10}{'I_num':>10}{'I_size':>10}{'T_size':>10}{'A_size':>10}"
                   f"{'GPU_mem':>10}{'Loss':>10}{'Avg_loss':>10}{'Crt_acc':>10}{'Crt_wf1':>10}")
        bar = tqdm(enumerate(val_loader), total=len(val_loader))
        with torch.no_grad():
            for batch_idx, (imgs, text, audio, emotion, lengths) in bar:
                imgs, text, audio, emotion = imgs.to(DEVICE), text.to(DEVICE), audio.to(DEVICE), emotion.to(DEVICE)
                output = model(imgs, lengths, text, audio)
                loss = criterion(output, emotion)
                val_loss += loss.item()
                mem = f"{torch.cuda.memory_reserved() / 1E9 if torch.cuda.is_available() else 0:.3g}G"
                _, pred = output.max(1)
                total += emotion.shape[0]
                correct += pred.eq(emotion).sum().item()
                preds.extend(pred.cpu().numpy())
                labels.extend(emotion.cpu().numpy())
                avg_loss = val_loss / (batch_idx + 1)
                crt_acc, crt_wf1 = correct / total, f1_score(labels, preds, average='weighted')
                s = f"{f'{epoch + 1}/{num_epochs}':>10}{f'{batch_idx + 1}/{len(val_loader)}':>10}{text.shape[0]:>10}{imgs.shape[0]:>10}{f'c{imgs.shape[1]}hw{imgs.shape[-1]}':>10}{f'n{text.shape[1]}d{text.shape[2]}':>10}{f'n{audio.shape[1]}d{audio.shape[2]}':>10}{mem:>10}{loss.item():>10.4f}{avg_loss:>10.4f}{crt_acc:>10.4f}{crt_wf1:>10.4f}"
                bar.set_description(s)
        train_loss, val_loss = train_loss / len(train_loader), val_loss / len(val_loader)
        acc, wf1 = correct / total, f1_score(labels, preds, average='weighted')
        logging.info(
            f"Epoch {epoch + 1}/{num_epochs}, train_loss: {train_loss:.4f}, val_loss: {val_loss:.4f}, acc: {acc:.4f}, wf1: {wf1:.4f}")
        if acc > best_acc:
            best_acc = acc
            torch.save(model.state_dict(), BEST_MODEL_ACC)
            logging.info(f"Best model_acc saved to {BEST_MODEL_ACC} with acc: {best_acc:.4f}")
        if wf1 > best_wf1:
            best_wf1 = wf1
            torch.save(model.state_dict(), BEST_MODEL_WF1)
            logging.info(f"Best model_wf1 saved to {BEST_MODEL_WF1} with wf1: {best_wf1:.4f}")
        checkpoint = {
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'crt_epoch': epoch + 1,
            'best_acc': best_acc,
            'best_wf1': best_wf1,
        }
        torch.save(checkpoint, LAST_CHECKPOINT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--epoch', type=int, default=100)
    parser.add_argument('--bsize', type=int, default=8)
    args = parser.parse_args()
    train(num_epochs=args.epoch, batch_size=args.bsize, log_id=1)
    # python train.py --epoch 100 --bsize 8
