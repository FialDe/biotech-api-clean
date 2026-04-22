import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from model import RNAModel
from dataset import RNADataset, collate_fn

# =========================
# 🔹 DEVICE
# =========================
device = torch.device("cpu")

# =========================
# 🔹 DATA
# =========================
dataset = RNADataset(
    "train_sequences.csv",
    "train_labels.csv"
)

# 🔥 kortere sequences (CPU friendly)
def limit_length(x, y, max_len=120):
    L = min(x.shape[0], max_len)
    return x[:L], y[:L]

class SmallDataset(torch.utils.data.Dataset):
    def __init__(self, base_dataset):
        self.base = base_dataset

    def __len__(self):
        return len(self.base)

    def __getitem__(self, idx):
        x, y = self.base[idx]
        return limit_length(x, y)

small_dataset = SmallDataset(dataset)

loader = DataLoader(
    small_dataset,
    batch_size=1,
    shuffle=True,
    collate_fn=collate_fn
)

# =========================
# 🔹 MODEL
# =========================
model = RNAModel().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

# =========================
# 🔹 LOSSES
# =========================
def neighbor_dist_loss(coords, mask):
    diff = coords[:,1:] - coords[:,:-1]
    dist = torch.sqrt((diff**2).sum(-1) + 1e-8)

    valid = mask[:,1:] * mask[:,:-1]

    TARGET = 1.5 / 100.0  # 🔥 belangrijk

    loss = ((dist - TARGET)**2) * valid
    return loss.sum() / valid.sum()

# =========================
# 🔹 TRAIN LOOP
# =========================
EPOCHS = 5

for epoch in range(EPOCHS):

    total_loss = 0

    for x, y, mask in loader:

        x = x.to(device)
        y = y.to(device)
        mask = mask.to(device)

        # 🔹 schaal targets
        y = y / 100.0

        pred = model(x)

        # 🔹 stabiliteit
        pred = torch.clamp(pred, -5, 5)

        mask_exp = mask.unsqueeze(-1)

        # 🔹 MSE met correct mask
        diff = (pred - y) ** 2
        diff = diff * mask_exp
        loss_mse = diff.sum() / mask_exp.sum()

        # 🔹 distance loss
        loss_dist = neighbor_dist_loss(pred, mask)

        # 🔹 totale loss
        loss = loss_mse + 0.5 * loss_dist

        optimizer.zero_grad()
        loss.backward()

        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch} | Loss: {total_loss/len(loader):.4f}")

# =========================
# 🔹 SAVE
# =========================
torch.save(model.state_dict(), "rna_model_cpu.pt")
print("✅ Model opgeslagen!")