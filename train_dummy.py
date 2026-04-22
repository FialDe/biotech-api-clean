import torch
import torch.nn as nn
import math
import random
from model import RNAModel

def is_pair(a, b):
    return (a == 0 and b == 1) or (a == 1 and b == 0) or (a == 2 and b == 3) or (a == 3 and b == 2)

def generate_data(seq_len=40):
    x = torch.randint(0, 4, (seq_len,))
    
    coords = []

    for i in range(seq_len):
        influence = 0

        for j in range(seq_len):
            if is_pair(x[i].item(), x[j].item()):
                influence += 2.0 / (abs(i-j) + 1)
            else:
                influence -= 0.5 / (abs(i-j) + 1)
        
        # base = x[i].item()

        coords.append([
            math.sin(i/5),
            math.cos(i/5),
            influence * 2.0 + (x[i].float() / 3.0) + random.uniform(-0.1, 0.1)
        ])
    
    y = torch.tensor(coords, dtype=torch.float32)
    return x, y

model = RNAModel()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

for epoch in range(1500):
    x, y = generate_data(seq_len=random.randint(30, 100))
    
    x = x.unsqueeze(0)
    y = y.unsqueeze(0)
    
    pred = model(x)
    loss = loss_fn(pred, y)
    
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch % 100 == 0:
        print(f"Epoch {epoch} Loss {loss.item()}")

torch.save(model.state_dict(), "rna_model.pt")
print("Model opgeslagen!")