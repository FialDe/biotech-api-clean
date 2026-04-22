import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from model import RNAModel
from dataset import RNADataset, collate_fn

# =========================
# 🔹 DEVICE
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =========================
# 🔹 DATA
# =========================
dataset = RNADataset(
    "train_sequences.csv",
    "train_labels.csv"
)

loader = DataLoader(
    dataset,
    batch_size=4,
    shuffle=True,
    collate_fn=collate_fn
)

# =========================
# 🔹 MODEL
# =========================
model = RNAModel().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

# =========================
# 🔥 LOSSES
# =========================
def pairwise_dist(x):
    diff = x[:, :, None, :] - x[:, None, :, :]
    return torch.sqrt((diff ** 2).sum(-1) + 1e-8)

def distance_loss(pred, target, mask):
    D_pred = pairwise_dist(pred)
    D_true = pairwise_dist(target)

    mask2 = mask[:, :, None] * mask[:, None, :]
    return ((D_pred - D_true) ** 2 * mask2).mean()

def backbone_loss(pred, mask):
    diffs = pred[:, 1:] - pred[:, :-1]
    dist = torch.sqrt((diffs ** 2).sum(-1) + 1e-8)

    mask2 = mask[:, 1:]
    return ((dist - 1.5) ** 2 * mask2).mean()

def smoothness_loss(pred):
    return torch.mean((pred[:, 2:] - 2*pred[:, 1:-1] + pred[:, :-2])**2)

# =========================
# 🔹 TRAIN LOOP
# =========================
EPOCHS = 10   # eerst klein testen

for epoch in range(EPOCHS):

    total_loss = 0

    for x, y, mask in loader:

        x = x.to(device)
        y = y.to(device)
        mask = mask.to(device)

        # 🔥 stabiliteit
        y = y / 100.0

        pred = model(x)

        # 🔥 basis loss (masked)
        mask_exp = mask.unsqueeze(-1)

        mse = ((pred - y) ** 2 * mask_exp).mean()

        # 🔥 langzaam opbouwen
        alpha = min(1.0, epoch / 10)

        loss = mse
        loss += distance_loss(pred, y, mask) * (0.1 * alpha)
        loss += backbone_loss(pred, mask) * (0.05 * alpha)
        loss += smoothness_loss(pred) * (0.05 * alpha)

        optimizer.zero_grad()
        loss.backward()

        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch} | Loss: {total_loss/len(loader):.4f}")

# =========================
# 🔹 SAVE
# =========================
torch.save(model.state_dict(), "rna_model.pt")
print("✅ Model opgeslagen!")