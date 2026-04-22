import torch
import pandas as pd

class RNADataset(torch.utils.data.Dataset):
    def __init__(self, seq_path, label_path):

        self.seq_df = pd.read_csv(seq_path)
        self.lab_df = pd.read_csv(label_path, low_memory=False)

        # 🔹 target_id
        self.lab_df["target_id"] = self.lab_df["ID"].str.split("_").str[0]

        # 🔥 GROEPEREN (KEY FIX)
        self.grouped = {
            k: v for k, v in self.lab_df.groupby("target_id")
        }

        mapping = {"A":0, "U":1, "G":2, "C":3}

        self.data = []

        # nt("🔄 Building dataset...")

        for i, (_, row) in enumerate(self.seq_df.iterrows()):
            target = row["target_id"]
            seq = row["sequence"]

            if target not in self.grouped:
                continue

            sub = self.grouped[target]

            coords = sub[["x_1","y_1","z_1"]].values

            x = [mapping.get(s, 0) for s in seq]

            L = min(len(x), len(coords))

            x = torch.tensor(x[:L], dtype=torch.long)
            y = torch.tensor(coords[:L], dtype=torch.float32)

            if torch.isnan(y).any():
                continue

            self.data.append((x, y))

            # 🔥 progress print
        #     if i % 100 == 0:
        #         print(f"Loaded {i} sequences")

        # print(f"✅ Dataset ready: {len(self.data)} samples")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]
    
def collate_fn(batch):
    xs, ys = zip(*batch)

    max_len = max(x.shape[0] for x in xs)

    x_padded = []
    y_padded = []
    mask = []

    for x, y in zip(xs, ys):
        L = x.shape[0]
        pad = max_len - L

        x_padded.append(torch.cat([x, torch.zeros(pad, dtype=torch.long)]))
        y_padded.append(torch.cat([y, torch.zeros(pad, 3)]))

        mask.append(torch.cat([torch.ones(L), torch.zeros(pad)]))

    return (
        torch.stack(x_padded),
        torch.stack(y_padded),
        torch.stack(mask)
    )