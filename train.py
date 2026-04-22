import torch
import torch.nn as nn
import math
import random
from model import RNAModel

# =========================
# 🔹 DEVICE
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =========================
# 🔹 MODEL
# =========================
model = RNAModel().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
loss_fn = nn.MSELoss()

# =========================
# 🔹 HELPER (RNA pairing)
# =========================
def is_pair(a, b):
    return (
        (a == 0 and b == 1) or  # A-U
        (a == 1 and b == 0) or
        (a == 2 and b == 3) or  # G-C
        (a == 3 and b == 2)
    )

# =========================
# 🔹 DATA GENERATOR
# =========================
def generate_data(seq_len=40):
    x = torch.randint(0, 4, (seq_len,))

    coords = []

    for i in range(seq_len):
        influence = 0

        for j in range(seq_len):
            dist = abs(i - j) + 1

            if is_pair(x[i].item(), x[j].item()):
                influence += 2.0 / dist
            else:
                influence -= 0.5 / dist

        coords.append([
            math.sin(i / 4),
            math.cos(i / 4),
            influence * 2.0 + (x[i].float() / 3.0) + random.uniform(-0.1, 0.1)
        ])

    y = torch.tensor(coords, dtype=torch.float32)

    return x, y

# =========================
# 🔥 EXTRA LOSS (later)
# =========================
def pairwise_dist(x):
    diff = x[:, :, None, :] - x[:, None, :, :]
    return torch.sqrt((diff ** 2).sum(-1) + 1e-8)

def distance_loss(pred, target):
    D_pred = pairwise_dist(pred)
    D_true = pairwise_dist(target)
    return torch.mean((D_pred - D_true) ** 2)

def backbone_loss(pred):
    diffs = pred[:, 1:, :] - pred[:, :-1, :]
    dist = torch.sqrt((diffs ** 2).sum(-1) + 1e-8)
    return torch.mean((dist - 1.5) ** 2)

# 🔥 NIEUW — smoothness
def smoothness_loss(pred):
    return torch.mean(
        (pred[:, 2:] - 2 * pred[:, 1:-1] + pred[:, :-2]) ** 2
    )

def step_loss(pred):
    steps = pred[:, 1:] - pred[:, :-1]
    return torch.mean(torch.abs(steps))


# =========================
# 🔹 TRAIN LOOP
# =========================
EPOCHS = 1500

for epoch in range(EPOCHS):

    # 🔹 random sequence length
    x, y = generate_data(seq_len=random.randint(30, 100))

    x = x.unsqueeze(0).to(device)   # (1, L)
    y = y.unsqueeze(0).to(device)   # (1, L, 3)

    # 🔥 NORMALISATIE (belangrijk!)
    y = y / 5.0

    pred = model(x)

    # =========================
    # 🔥 FASE 1 (stabiel trainen)
    # =========================
    loss = loss_fn(pred, y)

    # =========================
    # 🔥 FASE 2 (na ~500 epochs activeren)
    # =========================
    if epoch > 500:
        # 🔥 langzaam opbouwen van complexiteit
        alpha = min(1.0, epoch / 1000)

        loss = (
            loss_fn(pred, y) * 1.0 +
            distance_loss(pred, y) * (0.1 * alpha) +
            backbone_loss(pred) * (0.05 * alpha) +
            smoothness_loss(pred) * (0.1 * alpha) +
            step_loss(pred) * (0.05 * alpha)            
        )

    optimizer.zero_grad()
    loss.backward()

    # 🔥 voorkomt exploding gradients
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

    optimizer.step()

    # 🔹 logging
    if epoch % 100 == 0:
        print(f"Epoch {epoch} | Loss: {loss.item():.4f}")

# =========================
# 🔹 SAVE MODEL
# =========================
torch.save(model.state_dict(), "rna_model.pt")
print("✅ Model opgeslagen!")