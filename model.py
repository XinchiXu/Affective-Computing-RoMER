import torch
import torch.nn as nn
import math
from torchinfo import summary


class DropPath(nn.Module):
    def __init__(self, drop_prob: float = 0.):
        super().__init__()
        self.drop_prob = drop_prob

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.drop_prob == 0. or not self.training:
            return x
        keep_prob = 1. - self.drop_prob
        shape = (x.shape[0],) + (1,) * (x.ndim - 1)
        random_tensor = keep_prob + torch.rand(shape, dtype=x.dtype, device=x.device)
        binary_mask = torch.floor(random_tensor)
        return x.div(keep_prob) * binary_mask


class LayerNorm_CF(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim), requires_grad=True)
        self.bias = nn.Parameter(torch.zeros(dim), requires_grad=True)

    def forward(self, x, eps=1e-6):
        mean = x.mean(1, keepdim=True)
        var = (x - mean).pow(2).mean(1, keepdim=True)
        x = (x - mean) / torch.sqrt(var + eps)
        x = self.weight[:, None, None] * x + self.bias[:, None, None]
        return x


class ConvNeXtBlock(nn.Module):
    def __init__(self, dim, drop_prob=0.):
        super().__init__()
        self.conv = nn.Conv2d(dim, dim, kernel_size=7, padding=3, groups=dim)
        self.block = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Linear(dim * 4, dim),
        )
        self.gamma = nn.Parameter(torch.ones((dim,)) * 1e-6, requires_grad=True)
        self.drop_path = DropPath(drop_prob) if drop_prob > 0. else nn.Identity()

    def forward(self, x):
        x0 = x
        x = self.conv(x).permute(0, 2, 3, 1)
        x = (self.gamma * self.block(x)).permute(0, 3, 1, 2)
        x = self.drop_path(x) + x0
        return x


class ConvNeXt(nn.Module):
    def __init__(self, in_chans=3, depths=(3, 3, 9, 3), dim0=96, dim=768, level=3, dp_rates=(0.2, 0.2, 0.1, 0.1)):
        super().__init__()
        self.block1 = nn.Sequential(
            nn.Conv2d(in_chans, dim0, kernel_size=4, stride=4),
            LayerNorm_CF(dim0),
        )
        drop_probs = [x.item() for x in torch.linspace(0, dp_rates[0], sum(depths))]
        self.stages = nn.ModuleList()
        for i in range(len(depths)):
            if i > 0:
                self.stages.append(nn.Sequential(
                    LayerNorm_CF(dim0 * 2 ** (i - 1)),
                    nn.Conv2d(dim0 * 2 ** (i - 1), dim0 * 2 ** i, kernel_size=2, stride=2),
                ))
            crt = sum(depths[:i]) if i > 0 else 0
            self.stages.append(nn.Sequential(
                *[ConvNeXtBlock(dim=dim0 * 2 ** i, drop_prob=drop_probs[crt + j]) for j in range(depths[i])]
            ))
        self.block2 = nn.Sequential(
            nn.LayerNorm(dim0 * 2 ** (len(depths) - 1)),
            nn.Linear(dim0 * 2 ** (len(depths) - 1), dim),
        )
        self.pos_enc = PositionalEncoding(dim, dp_rate=dp_rates[2])
        self.decoders1 = nn.ModuleList([Decoder(dim, dim * 4, 8, dp_rates[3]) for _ in range(2)])
        self.decoders2 = nn.ModuleList([Decoder(dim, dim * 4, 8, dp_rates[3]) for _ in range(2)])
        self.cls_token1 = nn.Parameter(torch.randn(1, 1, dim))
        self.cls_token2 = nn.Parameter(torch.randn(1, level, dim))
        self.level = level

    def forward(self, x, lengths):
        x = self.block1(x)
        for stage in self.stages:
            x = stage(x)
        x = x.flatten(2).permute(0, 2, 1)
        x = self.block2(x)
        x_dec = self.pos_enc(torch.cat([self.cls_token1.expand(x.shape[0], -1, -1), x], dim=1))
        for decoder in self.decoders1:
            cls_out = decoder(x_dec[:, :1], x_dec[:, 1:])
            x_dec = torch.cat([cls_out, x_dec[:, 1:]], dim=1)
        x, x_out = x_dec[:, 0], []
        for i in range(len(lengths)):
            crt = sum(lengths[:i]) if i > 0 else 0
            x_batch = x[None, crt:sum(lengths[:i + 1])]
            x_dec = torch.cat([self.cls_token2, x_batch], dim=1)
            for decoder in self.decoders2:
                cls_out = decoder(x_dec[:, :self.level], x_dec[:, self.level:])
                x_dec = torch.cat([cls_out, x_dec[:, self.level:]], dim=1)
            x_out.append(x_dec[:, :self.level])
        return torch.cat(x_out, dim=0)


class PositionalEncoding(nn.Module):
    def __init__(self, dim, max_len=5000, dp_rate=0.):
        super().__init__()
        self.dropout = nn.Dropout(dp_rate)
        pe = torch.zeros(max_len, dim)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, dim, 2).float() * (-math.log(10000.0) / dim))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class MultiHeadAttention(nn.Module):
    def __init__(self, dim, num_heads, dp_rate=0.):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.d_k = dim // num_heads
        self.w_q = nn.Linear(dim, dim)
        self.w_k = nn.Linear(dim, dim)
        self.w_v = nn.Linear(dim, dim)
        self.fc = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(dp_rate)

    def forward(self, q, k, v):
        batch_size = q.shape[0]
        q = self.w_q(q).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        k = self.w_k(k).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        v = self.w_v(v).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)
        attn = self.dropout(torch.softmax(scores, dim=-1))
        context = torch.matmul(attn, v)
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.dim)
        return self.fc(context)


class FeedForward(nn.Module):
    def __init__(self, dim, dim_ff, dp_rate=0.):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(dim, dim_ff),
            nn.ReLU(),
            nn.Dropout(dp_rate),
            nn.Linear(dim_ff, dim),
        )

    def forward(self, x):
        return self.block(x)


class Decoder(nn.Module):
    def __init__(self, dim, dim_ff, num_heads, dp_rate=0.):
        super().__init__()
        self.multihead_attn1 = MultiHeadAttention(dim, num_heads, dp_rate)
        self.multihead_attn2 = MultiHeadAttention(dim, num_heads, dp_rate)
        self.dropout1 = nn.Dropout(dp_rate)
        self.dropout2 = nn.Dropout(dp_rate)
        self.block = nn.Sequential(
            FeedForward(dim, dim_ff, dp_rate),
            nn.Dropout(dp_rate),
        )
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
        self.norm3 = nn.LayerNorm(dim)

    def forward(self, x, enc_out):
        x = x + self.dropout1(self.multihead_attn1(self.norm1(x), self.norm1(x), self.norm1(x)))
        x = x + self.dropout2(self.multihead_attn2(self.norm2(x), enc_out, enc_out))
        x = x + self.block(self.norm3(x))
        return x


class RoMER(nn.Module):
    def __init__(self, dim=768, dim_ff=None, num_heads=8, num_layers=2, num_classes=7,
                 dp_rates=((0.2, 0.2, 0.1, 0.1), 0.1, 0.2)):
        super().__init__()
        dim_ff = dim_ff or dim * 4
        self.encoder = ConvNeXt(in_chans=3, dp_rates=dp_rates[0])
        self.decoders1 = nn.ModuleList([Decoder(dim, dim_ff, num_heads, dp_rates[1]) for _ in range(num_layers)])
        self.decoders2 = nn.ModuleList([Decoder(dim, dim_ff, num_heads, dp_rates[1]) for _ in range(num_layers)])
        self.header = nn.Sequential(
            nn.Flatten(),
            nn.Linear(dim * 5, dim),
            nn.LayerNorm(dim),
            nn.GELU(),
            nn.Dropout(dp_rates[2]),
            nn.Linear(dim, num_classes)
        )
        self.missing_text_token = nn.Parameter(torch.randn(1, 768))
        self.missing_audio_token = nn.Parameter(torch.randn(1, 768))

    def forward(self, image, lengths, text, audio):
        image_enc = self.encoder(image, lengths)
        text_dec = torch.stack([
            self.missing_text_token if torch.all(text[i] == 0).item() else text[i] for i in range(len(lengths))
        ])
        audio_dec = torch.stack([
            self.missing_audio_token if torch.all(audio[i] == 0).item() else audio[i] for i in range(len(lengths))
        ])
        text_audio_dec = torch.cat([text_dec, audio_dec], dim=1)
        for decoder in self.decoders1:
            text_audio_dec = decoder(text_audio_dec, image_enc)
        for decoder in self.decoders2:
            image_enc = decoder(image_enc, text_audio_dec)
        fused = torch.cat([image_enc, text_audio_dec], dim=1)
        return self.header(fused)


if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = RoMER().to(device)
    input1 = torch.randn(10, 3, 224, 224).to(device)
    input2 = torch.tensor([4, 4, 2]).to(device)
    input3 = torch.randn(3, 1, 768).to(device)
    input4 = torch.randn(3, 1, 768).to(device)
    print(summary(model, input_data=[input1, input2, input3, input4]))
