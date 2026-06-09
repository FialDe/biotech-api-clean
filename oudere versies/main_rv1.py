from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import torch
from model import RNAModel

# 🔹 Model laden
model = RNAModel()
model.load_state_dict(torch.load("rna_model_cpu.pt", map_location=torch.device("cpu")))
model.eval()

MAX_LEN = 1000

# Maak app
app = FastAPI()

# Input structuur
class SequenceInput(BaseModel):
    sequence: str

# Encoding
def encode(seq):
    mapping = {"A":0, "U":1, "G":2, "C":3}
    return [mapping.get(s, 0) for s in seq]

# 🔹 coords → PDB
def coords_to_pdb(seq, coords):
    pdb_lines = []
    for i, (base, (x, y, z)) in enumerate(zip(seq, coords), start=1):
        line = f"ATOM  {i:5d}  P   RNA A{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}"
        pdb_lines.append(line)
    return "\n".join(pdb_lines)

# 🔹 Predict functie
def predict_structure(seq):
    x = encode(seq)
    x = torch.tensor(x).unsqueeze(0)

    with torch.no_grad():
        coords = model(x)

    return coords.squeeze(0).tolist()

# 🔵 API root
@app.get("/")
def home():
    return {
        "name": "Biotech AI API",
        "status": "running",
        "docs": "/docs",
        "predict": "/predict"
    }

# 🔹 Glossary
GLOSSARY = {
    "Sequence length": "Number of nucleotides in the RNA sequence.",
    "Coordinates": "Predicted 3D positions of nucleotides."
}

@app.get("/glossary/{term}")
def get_glossary(term: str):
    return {
        "term": term,
        "definition": GLOSSARY.get(term, "No definition found.")
    }

# 🔹 Predict endpoint
@app.post("/predict")
def predict(data: SequenceInput):
    seq = data.sequence.upper()

    if not seq:
        return {"error": "Sequence cannot be empty"}

    if not all(c in "AUGC" for c in seq):
        return {"error": "Sequence must contain only A, U, G, C"}
    
    if len(seq) > MAX_LEN:
        return {"error": f"Sequence is too long (max {MAX_LEN})"}

    coords = predict_structure(seq)
    pdb = coords_to_pdb(seq, coords)

    return {
        "length": len(seq),
        "coords": coords,
        "pdb": pdb
    }

# 🔹 Demo UI
@app.get("/demo", response_class=HTMLResponse)
def demo():
    return """
    <html>
    <head>
        <title>Biotech AI</title>

        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>

        <style>
            body {
                font-family: 'Inter', Arial, sans-serif;
                background: radial-gradient(circle at top, #1e293b, #020617);
                color: #e2e8f0;
                display: flex;
                justify-content: center;
                align-items: flex-start;   /* 🔥 belangrijk */
                min-height: 100vh;         /* 🔥 ipv fixed height */
                margin: 0;
                padding: 40px 0;           /* 🔥 ruimte boven/onder */
            }

            .container {
                background: rgba(15, 23, 42, 0.9);
                backdrop-filter: blur(20px);
                padding: 30px;
                border-radius: 16px;
                width: 500px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.6);
                # text-align: center;
                # border: 1px solid rgba(255,255,255,0.05);

                # max-height: 90vh;      /* 🔥 voorkomt overflow */
                # overflow-y: auto;      /* 🔥 scroll binnen card */
                # position: relative;   /* 🔥 BELANGRIJK */
                # overflow: hidden;     /* 🔥 voorkomt dat viewer eruit breekt */
            }

            h1 {
                margin-bottom: 5px;
                font-size: 22px;
            }

            .subtitle {
                font-size: 12px;
                color: #64748b;
                margin-bottom: 15px;
            }

            input {
                width: 100%;
                padding: 14px;
                border-radius: 10px;
                border: 1px solid #334155;
                margin-bottom: 10px;
                background: #020617;
                color: white;
                # outline: none;
                # font-size: 15px;
            }

            input:focus {
                border-color: #38bdf8;
                box-shadow: 0 0 0 2px rgba(56,189,248,0.2);
            }

            .info {
                font-size: 12px;
                color: #94a3b8;
                margin-bottom: 10px;
                text-align: left;
            }

            .error {
                color: #f87171;
                font-size: 13px;
                margin-bottom: 10px;
                text-align: left;
            }

            button {
                width: 100%;
                padding: 12px;
                border: none;
                border-radius: 10px;
                background: linear-gradient(90deg, #3b82f6, #06b6d4);
                color: white;
                # font-size: 15px;
                cursor: pointer;
                # transition: all 0.2s ease;
            }

            button:hover {
                transform: translateY(-1px);
                box-shadow: 0 10px 20px rgba(59,130,246,0.4);
            }

            button:disabled {
                background: #475569;
                cursor: not-allowed;
            }

            .spinner {
                border: 3px solid rgba(255,255,255,0.1);
                border-top: 3px solid #38bdf8;
                border-radius: 50%;
                width: 22px;
                height: 22px;
                animation: spin 1s linear infinite;
                margin: 15px auto;
                display: none;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .result-box {
                background: #020617;
                padding: 12px;
                border-radius: 10px;
                margin-top: 12px;
                text-align: left;
                font-size: 13px;

                max-height: 180px;
                overflow-y: auto;
            }

            table {
                width: 100%;
                margin-top: 10px;
                font-size: 12px;
            }

            th, td {
                padding: 4px;
                text-align: center;
            }

            #viewer {
                width: 100%;
                height: 320px;
                margin-top: 15px;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.05);
                
                position: relative;   /* 🔥 voorkomt overlay issues */
                z-index: 0;           /* 🔥 zorgt dat hij onder UI blijft */
                overflow: hidden;     /* 🔥 belangrijk voor 3Dmol */
            }
            #infoBox {
                margin-top: 15px;
                padding: 12px;
                border-radius: 10px;
                background: #020617;
                font-size: 13px;
                text-align: left;
                display: none;

                input, button, .info, .error, .result-box {
                position: relative;
                z-index: 1;
            }
            
        </style>
    </head>

    <body>
        <div class="container">
            <h2>🧬 RNA Predictor</h2>
            <div class="subtitle">AI-powered RNA structure preview</div>

            <input id="seq" placeholder="e.g. AUGCUAGCUAGC">

            <div class="info" id="info">Length: 0</div>
            <div class="error" id="error"></div>

            <button id="btn" onclick="send()" disabled>Run Prediction</button>

            <div class="spinner" id="spinner"></div>

            <div id="output" class="result-box"></div>

            <div id="viewer"></div>

            <div id="infoBox"></div>
        </div>

        <script>
        let input = document.getElementById("seq");
        let error = document.getElementById("error");
        let info = document.getElementById("info");
        let btn = document.getElementById("btn");

        input.addEventListener("input", () => {
            let seq = input.value.toUpperCase().trim();
            info.innerText = "Length: " + seq.length;

            if (!seq) {
                error.innerText = "Please enter a sequence";
                btn.disabled = true;
                return;
            }

            if (!/^[AUGC]+$/.test(seq)) {
                error.innerText = "Only A, U, G, C allowed";
                btn.disabled = true;
                return;
            }

            if (seq.length > 1000) {
                error.innerText = "Max length is 1000";
                btn.disabled = true;
                return;
            }

            error.innerText = "";
            btn.disabled = false;
        });

        input.addEventListener("keypress", function(e) {
            if (e.key === "Enter" && !btn.disabled) send();
        });

        async function send() {
            let seq = input.value.toUpperCase().trim();

            let output = document.getElementById("output");
            let spinner = document.getElementById("spinner");
            let viewerDiv = document.getElementById("viewer");

            output.innerHTML = "";
            viewerDiv.innerHTML = "";
            document.getElementById("infoBox").style.display = "none";

            spinner.style.display = "block";
            btn.disabled = true;

            try {
                let res = await fetch("/predict", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({sequence: seq})
                });

                let data = await res.json();
                spinner.style.display = "none";

                if (data.error) {
                    output.innerText = "Error: " + data.error;
                    return;
                }

                output.innerHTML = `
                    <b>Sequence length:</b> ${data.length}<br><br>
                    <b>First 5 coordinates:</b>
                    <pre>${JSON.stringify(data.coords.slice(0,5), null, 2)}</pre>
                `;

                let viewer = $3Dmol.createViewer(viewerDiv, {backgroundColor: "#0f172a"});

                let coords = data.coords;
                let scale = 10 / Math.max(...coords.flat().map(v => Math.abs(v)));
                coords = coords.map(c => c.map(v => v * scale));

                viewer.addCurve({
                    points: coords.map(c => ({x:c[0], y:c[1], z:c[2]})),
                    radius: 0.2,
                    color: "#94a3b8"
                });

                let colors = {
                    "A": "#4ade80",  // groen
                    "U": "#f87171",  // rood
                    "G": "#fb923c",  // oranje
                    "C": "#60a5fa"   // blauw
                };

                coords.forEach((c, i) => {
                    viewer.addSphere({
                        center: {x:c[0], y:c[1], z:c[2]},
                        radius: 0.5,
                        color: colors[seq[i]],
                        opacity: 0.95
                    });
                });

                viewer.zoomTo();
                viewer.render();

            } catch {
                spinner.style.display = "none";
                output.innerText = "Server error.";
            } finally {
                btn.disabled = false;
            }
        }
        </script>
    </body>
    </html>
    """