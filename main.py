from fastapi import FastAPI
from pydantic import BaseModel
import torch
import RNA

from model import RNAModel

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# 🔹 Model laden
model = RNAModel()
model.load_state_dict(torch.load("rna_model_cpu.pt", map_location=torch.device("cpu")))
model.eval()

MAX_LEN = 1000

class SequenceInput(BaseModel):
    sequence: str

def encode(seq):
    mapping = {"A":0, "U":1, "G":2, "C":3}
    return [mapping.get(s, 0) for s in seq]

def coords_to_pdb(seq, coords):
    pdb_lines = []
    for i, (base, (x, y, z)) in enumerate(zip(seq, coords), start=1):
        line = f"ATOM  {i:5d}  P   RNA A{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}"
        pdb_lines.append(line)
    return "\n".join(pdb_lines)

def predict_structure(seq):
    x = encode(seq)
    x = torch.tensor(x).unsqueeze(0)

    with torch.no_grad():
        coords = model(x) * 100.0

    return coords.squeeze(0).tolist()

@app.get("/")
def home():
    return {
        "name": "Biotech AI API",
        "status": "running"
    }

@app.post("/predict")
def predict(data: SequenceInput):
    seq = data.sequence.upper().strip()

    # 🔴 BACKEND VALIDATIE (blijft altijd nodig)
    if not seq:
        return {"error": "Sequence cannot be empty"}

    if not all(c in "AUGC" for c in seq):
        return {"error": "Sequence must contain only A, U, G, C"}

    if len(seq) > MAX_LEN:
        return {"error": f"Sequence is too long (max {MAX_LEN})"}

    fc = RNA.fold_compound(seq)

    structure, mfe = fc.mfe()

    coords = predict_structure(seq)

    return {
        "length": len(seq),
        "coords": coords,
        "dot_bracket": structure,
        "mfe": mfe
    }

@app.get("/pdb_example")
def pdb_example():

    # 🔥 simpele hairpin (realistisch gevormd)
    coords = [
        [0,0,0],
        [1.5,0,0],
        [3,0.5,0],
        [4,1.5,0],
        [5,2.5,0],
        [6,3.5,0],
        [7,2.5,0],
        [8,1.5,0],
        [9,0.5,0],
        [10,0,0]
    ]

    seq = "GGGAAAUCCC"

    return {
        "coords": coords,
        "sequence": seq,
        "type": "real"
    }

@app.get("/demo")
def demo(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )