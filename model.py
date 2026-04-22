import torch
import torch.nn as nn
import torch.nn.functional as F

class RNAModel(nn.Module):
    def __init__(self, max_len=200):
        super().__init__()

        # 🔹 embeddings
        self.embedding = nn.Embedding(4, 32)           # A,U,G,C
        self.pos_embedding = nn.Embedding(max_len, 16)

        # 🔹 pairwise scoring (attention-achtig)
        self.pairwise = nn.Sequential(
            nn.Linear(96, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

        # 🔹 output naar coords
        self.fc = nn.Sequential(
            nn.Linear(96, 64),
            nn.ReLU(),
            nn.Linear(64, 3)
        )

    def forward(self, x):
        B, L = x.shape

        # 🔹 embeddings
        emb = self.embedding(x)  # (B, L, 32)

        positions = torch.arange(L, device=x.device).unsqueeze(0).expand(B, -1)
        pos_emb = self.pos_embedding(positions)  # (B, L, 16)

        emb = torch.cat([emb, pos_emb], dim=-1)  # (B, L, 48)

        # 🔹 pairwise interacties
        emb_i = emb.unsqueeze(2).expand(-1, -1, L, -1)
        emb_j = emb.unsqueeze(1).expand(-1, L, -1, -1)

        pair = torch.cat([emb_i, emb_j], dim=-1)  # (B, L, L, 96)

        pair_score = self.pairwise(pair).squeeze(-1)  # (B, L, L)

        # 🔴 mask: geen self-interaction
        eye = torch.eye(L, device=x.device).bool().unsqueeze(0)
        pair_score = pair_score.masked_fill(eye, -1e9)

        # 🔹 attention weights
        weights = F.softmax(pair_score, dim=-1)  # (B, L, L)

        # 🔹 weighted interaction
        interaction = torch.matmul(weights, emb)  # (B, L, 48)

        # 🔹 combine
        x = torch.cat([emb, interaction], dim=-1)  # (B, L, 96)

        coords = self.fc(x)  # (B, L, 3)

        return coords