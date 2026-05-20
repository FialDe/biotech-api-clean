from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import torch
from model import RNAModel
import requests

# 🔹 Model laden
model = RNAModel()
model.load_state_dict(torch.load("rna_model_cpu.pt", map_location=torch.device("cpu")))
model.eval()

MAX_LEN = 1000

app = FastAPI()

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

    coords = predict_structure(seq)

    return {
        "length": len(seq),
        "coords": coords
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

@app.get("/pdb/{pdb_id}")
def get_pdb(pdb_id: str):

    url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"

    res = requests.get(url)

    if res.status_code != 200:
        return {"error": "PDB not found"}

    pdb_text = res.text

    coords = []
    seq = []

    for line in pdb_text.splitlines():

        if line.startswith("ATOM"):

            atom_name = line[12:16].strip()
            resname = line[17:20].strip()

            # 🔥 alleen backbone (simpel houden)
            if atom_name == "P":

                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])

                coords.append([x, y, z])

                # simpele mapping
                base = resname[0]  # A, U, G, C
                seq.append(base)

    return {
        "sequence": "".join(seq),
        "coords": coords,
        "type": "pdb"
    }

@app.get("/demo", response_class=HTMLResponse)
def demo():
    return """
    <html>
    <head>
        <title>Biotech AI</title>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>

        <style>
            /* =========================
            GLOBAL LAYOUT
            ========================= */
            body {
                font-family: 'Inter', Arial;
                background: radial-gradient(circle at top, #1e293b, #020617);
                color: #e2e8f0;
                display: flex;
                justify-content: center;
                align-items: flex-start;
                min-height: 100vh;
                margin: 0;
                padding: 40px 0;
            }

            .container {
                background: rgba(15, 23, 42, 0.9);
                padding: 30px;
                border-radius: 16px;
                width: 600px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.6);
            }

            /* =========================
            INPUT
            ========================= */
            input {
                width: 100%;
                padding: 14px;
                border-radius: 10px;
                border: 1px solid #334155;
                margin-bottom: 10px;
                background: #020617;
                color: white;
            }

            /* =========================
            BUTTONS (BASE)
            ========================= */
            button {
                padding: 12px;
                border-radius: 10px;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            }

            button:active {
                transform: scale(0.97);
            }

            button:disabled {
                background: #475569;
                cursor: not-allowed;
            }

            /* =========================
            TOOLBAR
            ========================= */
            .toolbar {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin-bottom: 10px;
            }

            /* kleine knoppen */
            .mini-btn {
                padding: 6px 10px;
                font-size: 11px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: transparent;
                color: #cbd5f5;
                width: auto;
                display: inline-flex;
                align-items: center;
                justify-content: center;
            }

            .mini-btn:hover {
                background: #1e293b;
                transform: translateY(-1px);
            }

            /* primaire knop (Run) */
            .primary-btn {
                width: 50%;
                background: linear-gradient(90deg, #3b82f6, #06b6d4);
                color: white;
                font-size: 13px;
            }

            /* =========================
            TABLE
            ========================= */
            table {
                width: 100%;
                margin-top: 10px;
                font-size: 12px;
            }

            th, td {
                padding: 4px;
                text-align: center;
            }

            td:hover {
                opacity: 0.8;
                transform: scale(1.05);
                transition: 0.15s;
            }

            /* =========================
            VIEWER + ANIMATION
            ========================= */
            #viewer {
                width: 100%;
                height: 420px;
                margin-top: 15px;
                border-radius: 10px;
                border: 1px solid #334155;
                overflow: hidden;
                position: relative;
                opacity: 0;
                transition: opacity 0.4s ease;
            }

            #viewer.show {
                opacity: 1;
            }

            #output {
                margin-top: 18px;
                opacity: 0;
                transform: translateY(10px);
                transition: all 0.4s ease;
            }

            #output.show {
                opacity: 1;
                transform: translateY(0);
            }

            /* =========================
            INFO / DOWNLOAD
            ========================= */
            #downloadBtn {
                margin-top: 15px;
            }

            /* =========================
            GUIDE + HIGHLIGHT
            ========================= */
            .highlight {
                position: relative;
                z-index: 1001;
                box-shadow: 0 0 0 3px #38bdf8, 0 0 20px rgba(56,189,248,0.6);
                border-radius: 8px;
            }

            #guideBox {
                position: fixed;
                bottom: 40px;
                left: 50%;
                transform: translateX(-50%);
                background: #020617;
                padding: 15px 20px;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.6);
                font-size: 14px;
                z-index: 1002;
                max-width: 320px;
                text-align: center;
            }

            .small-btn {
                width: auto;
                padding: 6px 12px;
                font-size: 12px;
            }

            .app {
                display: flex;
                width: 100%;
                max-width: 900px;
                gap: 20px;
            }

            .sidebar {
                width: 160px;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .sidebar button {
                padding: 8px;
                font-size: 12px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: transparent;
                color: #cbd5f5;
                cursor: pointer;
            }

            .sidebar button:hover {
                background: #1e293b;
            }

            .main-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }

            .left-panel {
                display: flex;
                flex-direction: column;
            }

            .right-panel {
                display: flex;
                flex-direction: column;
                justify-content: center;
            }

            @media (max-width: 700px) {
                .main-grid {
                    grid-template-columns: 1fr;
                }
            }

            span[onclick] {
                transition: color 0.2s;
            }

            span[onclick]:hover {
                color: #38bdf8;
            }
        </style>
    </head>

    <body>
        <div class="app">
            <div class="sidebar">
                <button class="mini-btn" onclick="loadExample('hairpin')">Hairpin</button>
                <button class="mini-btn" onclick="loadExample('gc')">High GC</button>
                <button class="mini-btn" onclick="loadExample('none')">No structure</button>
                <button class="mini-btn" onclick="randomSeq()">🎲 Random</button>

                <hr style="margin:10px 0; border-color:#334155;">

                <button class="mini-btn" onclick="loadReal()">🧬 Real RNA</button>
                <button class="mini-btn" onclick="loadPDB('1EHZ')">🧬 Real PDB</button>

                <hr style="margin:10px 0; border-color:#334155;">

                <button class="mini-btn" onclick="startGuide()">❓ Guide</button>
                <button class="mini-btn" onclick="showInfo('about')">ℹ️ About</button>
                <button class="mini-btn" onclick="showInfo('why')">🧬 Why</button>

                <hr style="margin:10px 0; border-color:#334155;">

                <button class="mini-btn" onclick="showInfo('rna')">RNA</button>
                <button class="mini-btn" onclick="showInfo('types')">Types</button>
                <button class="mini-btn" onclick="showInfo('pairing')">Pairing</button>
                <button class="mini-btn" onclick="showInfo('function')">Function</button>
            </div>

            <div class="container">
                
            <h2>🧬 RNA Designer</h2>

            <div style="
                background: rgba(2,6,23,0.6);
                padding:10px;
                border-radius:10px;
                font-size:12px;
                color:#94a3b8;
                margin-bottom:15px;
            ">
                <span onclick="showInfo('about')" style="cursor:pointer;">
                    ⚠️ Demo model — click for more info
                </span>
            </div>

            <input id="seq" placeholder="AUGCUAGCUA">

            <div class="toolbar">           
                
                
                <button id="runBtn" class="primary-btn" onclick="run()" disabled>Run</button>

            </div>

            <div id="error" style="color:#f87171; font-size:13px; margin-bottom:10px;"></div>               
                     

            <div id="loading" style="margin-top:10px; font-size:13px; opacity:0.8;"></div>
            
    <div class="main-grid">

        <div class="left-panel">
            <div id="output"></div>

            <button id="downloadBtn" class="primary-btn small-btn" onclick="download()" style="display:none;">Download coords</button>

        </div>

        <div class="right-panel">
            <div id="viewer"></div>
        </div>
    </div>

            <div id="infoBox" style="
                margin-top: 10px;
                padding: 10px;
                border-radius: 10px;
                background: #020617;
                font-size: 13px;
                display: none;
            "></div>
        </div>

        <script>
            let lastCoords = [];

            let input = document.getElementById("seq");
            let btn = document.getElementById("runBtn");
            let errorDiv = document.getElementById("error");

            input.addEventListener("input", () => {
                let seq = input.value.toUpperCase().trim();

                if (!seq) {
                    errorDiv.innerText = "Sequence cannot be empty";
                    btn.disabled = true;
                    return;
                }

                if (!/^[AUGC]+$/.test(seq)) {
                    errorDiv.innerText = "Only A, U, G, C allowed";
                    btn.disabled = true;
                    return;
                }

                if (seq.length > 1000) {
                    errorDiv.innerText = "Sequence too long (max 1000)";
                    btn.disabled = true;
                    return;
                }

                // ✅ geldig
                errorDiv.innerText = "";
                btn.disabled = false;
            });

            async function loadReal(){

                let res = await fetch("/pdb_example");
                let data = await res.json();

                let seq = data.sequence;
                let coords = data.coords;

                // zet sequence in input (zoals andere knoppen)
                document.getElementById("seq").value = seq;

                // trigger validatie (zoals andere knoppen)
                document.getElementById("seq").dispatchEvent(new Event("input"));

                // 🔥 NU: gebruik dezelfde flow als run()
                renderFromCoords(seq, coords);
            }

            async function loadPDB(id){

                let res = await fetch("/pdb/" + id);
                let data = await res.json();

                if(data.error){
                    alert(data.error);
                    return;
                }

                let seq = data.sequence;
                let coords = data.coords;

                document.getElementById("seq").value = seq;
                document.getElementById("seq").dispatchEvent(new Event("input"));

                renderFromCoords(seq, coords);
            }

            function detectHairpins(pairs){
                let hairpins = [];

                pairs.forEach(p => {
                    let i = p[0];
                    let j = p[1];

                    if(j - i > 4){ // ruimte voor loop
                        hairpins.push({start:i, end:j});
                    }
                });

                return hairpins;
            }

            function renderFromCoords(seq, coords){

                lastCoords = coords;

                // schaal (zelfde als nu)
                let maxVal = Math.max(...coords.flat().map(v => Math.abs(v)));
                let scale = maxVal === 0 ? 1 : 10 / maxVal;
                let scaled = coords.map(c => c.map(v => v * scale));

                let pairs = getPairs(seq, scaled);
                let hairpins = detectHairpins(pairs);
                let dot = toDotBracket(seq, pairs);

                let outputDiv = document.getElementById("output");

                outputDiv.innerHTML = `
                    <div style="font-size:13px; line-height:1.6;">

                        <b>
                        <span onclick="showInfo('rna')" style="cursor:pointer;color:#38bdf8">RNA</span> |
                        <span onclick="showInfo('types')" style="cursor:pointer;color:#38bdf8">Types</span> |
                        <span onclick="showInfo('pairing')" style="cursor:pointer;color:#38bdf8">Pairing</span>
                        </b>

                        <br><br>

                        <b>Sequence:</b> ${seq}<br>
                        <b>Type:</b> Real RNA structure<br>
                        <b>Pairs:</b> ${pairs.length}<br>
                        <b>Structure:</b> ${dot}<br>

                    </div>
                `;

                // viewer
                let viewerDiv = document.getElementById("viewer");
                viewerDiv.innerHTML = "";

                let viewer = $3Dmol.createViewer(viewerDiv, {
                    backgroundColor: "#020617"
                });

                // backbone
                viewer.addCurve({
                    points: scaled.map(c => ({x:c[0], y:c[1], z:c[2]})),
                    radius: 0.25,
                    color: "#64748b"
                });

                // bases
                let colors = {
                    "A": "#4ade80",
                    "U": "#f87171",
                    "G": "#fb923c",
                    "C": "#60a5fa"
                };

                scaled.forEach((c,i)=>{
                    viewer.addSphere({
                        center: {x:c[0], y:c[1], z:c[2]},
                        radius: 0.6,
                        color: colors[seq[i]]
                    });
                });

                // pairs
                pairs.forEach(p => {
                    viewer.addCylinder({
                        start: {x:scaled[p[0]][0], y:scaled[p[0]][1], z:scaled[p[0]][2]},
                        end: {x:scaled[p[1]][0], y:scaled[p[1]][1], z:scaled[p[1]][2]},
                        radius: 0.15,
                        color: "#22c55e"
                    });
                });

                // hairpins
                hairpins.forEach(h => {
                    viewer.addCylinder({
                        start: {x:scaled[h.start][0], y:scaled[h.start][1], z:scaled[h.start][2]},
                        end: {x:scaled[h.end][0], y:scaled[h.end][1], z:scaled[h.end][2]},
                        radius: 0.25,
                        color: "#facc15"
                    });
                });

                viewer.zoomTo();
                viewer.render();
            }

            function getPairs(seq, coords){
                let pairs = [];
                let used = new Set();

                function canPair(a,b){
                    return (
                        (a==="A" && b==="U") ||
                        (a==="U" && b==="A") ||
                        (a==="G" && b==="C") ||
                        (a==="C" && b==="G") ||
                        (a==="G" && b==="U") ||
                        (a==="U" && b==="G")
                    );
                }

                let candidates = [];

                // verzamel alle mogelijke pairs
                for(let i=0;i<seq.length;i++){
                    for(let j=i+4;j<seq.length;j++){
                        if(!canPair(seq[i], seq[j])) continue;

                        let dx = coords[i][0] - coords[j][0];
                        let dy = coords[i][1] - coords[j][1];
                        let dz = coords[i][2] - coords[j][2];

                        let dist = Math.sqrt(dx*dx + dy*dy + dz*dz);

                        if(dist < 4){
                            candidates.push({i, j, dist});
                        }
                    }
                }

                // sorteer op beste (kortste afstand eerst)
                candidates.sort((a,b) => a.dist - b.dist);

                // kies alleen unieke paren
                candidates.forEach(c => {
                    if(!used.has(c.i) && !used.has(c.j)){
                        pairs.push([c.i, c.j]);
                        used.add(c.i);
                        used.add(c.j);
                    }
                });

                return pairs;
            }

            function loadExample(type){
                let examples = {
                    hairpin: "GGGAAAUCC",
                    gc: "GGGCGGCGCCG",
                    none: "AAAAAAA",
                    random: generateRandom(10)
                };

                let seq = examples[type];

                document.getElementById("seq").value = seq;

                // trigger input check
                document.getElementById("seq").dispatchEvent(new Event("input"));

                run();
            }

            function generateRandom(length){
                let bases = ["A","U","G","C"];
                let seq = "";

                for(let i=0;i<length;i++){
                    seq += bases[Math.floor(Math.random()*4)];
                }

                return seq;
            }

            function randomSeq(){
                let length = 10 + Math.floor(Math.random() * 20); // 10–30 bases
                let seq = generateRandom(length);

                document.getElementById("seq").value = seq;

                // trigger validatie
                document.getElementById("seq").dispatchEvent(new Event("input"));

                // direct run
                run();
            }

            function toDotBracket(seq, pairs){
                let structure = Array(seq.length).fill(".");

                pairs.forEach(p => {
                    structure[p[0]] = "(";
                    structure[p[1]] = ")";
                });

                return structure.join("");
            }

            function classifyStructure(pairs){
                if(pairs.length === 0) return "No stable structure";

                if(pairs.length === 1) return "Simple pair";

                if(pairs.length >= 2) return "Hairpin-like structure (loop formation)";

                return "Complex structure";
            }

            function showBaseInfo(base){
                let box = document.getElementById("infoBox");

                let text = "";

                if(base === "A"){
                    text = "A (Adenine) bindt meestal met U. Vormt 2 waterstofbruggen.";
                }

                if(base === "U"){
                    text = "U (Uracil) bindt met A. Komt alleen voor in RNA (niet in DNA).";
                }

                if(base === "G"){
                    text = "G (Guanine) bindt met C (sterk, 3 bindingen) en soms met U (wobble pair).";
                }

                if(base === "C"){
                    text = "C (Cytosine) bindt met G. Dit is de sterkste binding in RNA.";
                }

                box.innerText = text;
                box.style.display = "block";
            }

            function gcContent(seq){
                let gc = 0;
                for(let s of seq){
                    if(s === "G" || s === "C") gc++;
                }
                return ((gc / seq.length) * 100).toFixed(1);
            }

            function structureScore(coords){
                let score = 0;
                for(let i=1;i<coords.length;i++){
                    let dx = coords[i][0] - coords[i-1][0];
                    let dy = coords[i][1] - coords[i-1][1];
                    let dz = coords[i][2] - coords[i-1][2];

                    let dist = Math.sqrt(dx*dx+dy*dy+dz*dz);
                    score += Math.abs(dist - 1.5);
                }
                return (100 - score).toFixed(1);
            }

            function formatCoords(coords, seq){
                let colors = {
                    "A": "#4ade80",
                    "U": "#f87171",
                    "G": "#fb923c",
                    "C": "#60a5fa"
                };

            
                let html = "<table>";
                html += "<tr><th>#</th><th>Base</th><th>X</th><th>Y</th><th>Z</th></tr>";

                coords.slice(0,10).forEach((c,i)=>{
                    html += "<tr>";
                    html += `<td>${i+1}</td>`;
                    html += `<td onclick="showBaseInfo('${seq[i]}')" 
                        style='color:${colors[seq[i]]}; cursor:pointer; font-weight:bold;'>
                        ${seq[i]}
                    </td>`;
                    html += `<td>${c[0].toFixed(2)}</td>`;
                    html += `<td>${c[1].toFixed(2)}</td>`;
                    html += `<td>${c[2].toFixed(2)}</td>`;
                    html += "</tr>";
                });

                html += "</table>";
                return html;
            }

            async function run(){                

                let loading = document.getElementById("loading");
                loading.innerText = "Calculating structure...";
                btn.disabled = true;

                let seq = input.value.toUpperCase();

                let res = await fetch("/predict", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({sequence: seq})
                });

                let data = await res.json();

                if(data.error){
                    errorDiv.innerText = data.error;
                    loading.innerText = "";
                    btn.disabled = false;
                    return;
                }

                errorDiv.innerText = "";

                lastCoords = data.coords;

                // 🔵 werk-variabele
                let coords = data.coords;

                // schaal
                let maxVal = Math.max(...coords.flat().map(v => Math.abs(v)));
                let scale = maxVal === 0 ? 1 : 10 / maxVal;
                coords = coords.map(c => c.map(v => v * scale));

                // 🟢 pairing op geschaalde coords
                let pairs = getPairs(seq, coords);

                let dot = toDotBracket(seq, pairs);

                let hairpins = detectHairpins(pairs);                

                let outputDiv = document.getElementById("output");
                outputDiv.classList.remove("show");
                outputDiv.innerHTML = `
                    <div style="font-size:13px; line-height:1.6;">

                        <b>
                        <span onclick="showInfo('rna')" style="cursor:pointer;color:#38bdf8">RNA</span> |
                        <span onclick="showInfo('types')" style="cursor:pointer;color:#38bdf8">Types</span> |
                        <span onclick="showInfo('pairing')" style="cursor:pointer;color:#38bdf8">Pairing</span>
                        </b>

                        <br><br>

                        <b><span onclick="showInfo('length')" style="cursor:pointer;color:#38bdf8">Sequence length</span>:</b> ${data.length}<br>
                        <b><span onclick="showInfo('gc')" style="cursor:pointer;color:#38bdf8">GC Content</span>:</b> ${gcContent(seq)}%<br>
                        <b><span onclick="showInfo('score')" style="cursor:pointer;color:#38bdf8">Structure Score</span>:</b> ${structureScore(data.coords)}<br>
                        <b><span onclick="showInfo('pairs')" style="cursor:pointer;color:#38bdf8">Base pairs</span>:</b> ${pairs.length}<br>
                        <b><span onclick="showInfo('dot')" style="cursor:pointer;color:#38bdf8">Structure</span>:</b> ${dot}<br>
                        <b>Type:</b> ${classifyStructure(pairs)}<br>
                    </div><br>
                    ${formatCoords(data.coords, seq)}
                `;

                setTimeout(() => {
                    outputDiv.classList.add("show");
                }, 50);

                document.getElementById("downloadBtn").style.display = "block";

                let viewerDiv = document.getElementById("viewer");
                viewerDiv.innerHTML = "";

                let viewer = $3Dmol.createViewer(viewerDiv, {
                    backgroundColor: "#020617"
                });
                
                viewerDiv.classList.remove("show");

                setTimeout(() => {
                    viewerDiv.classList.add("show");
                }, 50);

                viewer.addCurve({
                    points: coords.map(c => ({x:c[0], y:c[1], z:c[2]})),
                    radius: 0.25,
                    color: "#94a3b8"
                });

                let colors = {
                    "A": "#4ade80",
                    "U": "#f87171",
                    "G": "#fb923c",
                    "C": "#60a5fa"
                };

                coords.forEach((c,i)=>{
                    viewer.addSphere({
                        center: {x:c[0], y:c[1], z:c[2]},
                        radius: 0.6,
                        color: colors[seq[i]]
                    });
                });
                
                pairs.forEach(p => {
                    let i = p[0];
                    let j = p[1];

                    viewer.addCylinder({
                        start: {x:coords[i][0], y:coords[i][1], z:coords[i][2]},
                        end: {x:coords[j][0], y:coords[j][1], z:coords[j][2]},
                        radius: 0.15,
                        color: "#22c55e", // groen = pairing
                        dashed: true
                    });
                });

                hairpins.forEach(h => {
                    viewer.addCylinder({
                        start: {x:coords[h.start][0], y:coords[h.start][1], z:coords[h.start][2]},
                        end: {x:coords[h.end][0], y:coords[h.end][1], z:coords[h.end][2]},
                        radius: 0.25,
                        color: "#facc15" // geel = hairpin
                    });
                });

                viewer.zoomTo();
                viewer.render();

                loading.innerText = "";
                btn.disabled = false;
            }

            function download(){
                let text = lastCoords.map(c => c.join(",")).join("\\n");

                let blob = new Blob([text], {type:"text/plain"});
                let a = document.createElement("a");

                a.href = URL.createObjectURL(blob);
                a.download = "coords.txt";
                a.click();
            }

            function openModal(text){
                let modal = document.getElementById("modal");
                let content = document.getElementById("modalContent");

                content.innerHTML = text;
                modal.style.display = "flex";
            }

            function closeModal(){
                document.getElementById("modal").style.display = "none";
            }

            function showInfo(type){
                let box = document.getElementById("infoBox");
                if(!box) return;

                let text = "";

                if(type === "length"){
                    text = "Sequence length = aantal nucleotiden in de RNA keten.";
                }

                else if(type === "gc"){
                    text = "GC Content = percentage G en C basen.<br><br>Een hogere waarde betekent meestal een stabielere structuur, omdat G-C bindingen sterker zijn dan A-U bindingen.";
                }

                else if(type === "score"){
                    text = "Structure Score = hoe consistent de afstanden tussen nucleotiden zijn.<br><br>Een hogere score betekent een meer realistische en stabiele structuur.";
                }

                else if(type === "pairs"){
                    text = "Base pairs zijn bindingen tussen nucleotiden.<br><br>Deze interacties vormen de basis van RNA structuur en bepalen hoe de keten vouwt.";
                }

                else if(type === "dot"){
                    text = "Dot-bracket notatie:<br><br>( ) = gekoppelde basen<br>. = vrije basen<br><br>Dit is een standaard manier om RNA structuur te beschrijven.";
                }

                else if(type === "about"){
                    text = `
                    <b>About this tool</b><br><br>

                    This application is designed as an interactive introduction to RNA structure and behavior.<br><br>

                    RNA (Ribonucleic Acid) is a fundamental biological molecule that plays a central role in processes such as protein synthesis, gene regulation, and modern biotechnology applications like mRNA vaccines.<br><br>

                    <b>What this tool does</b><br>
                    - Visualizes RNA sequences in 3D space<br>
                    - Highlights concepts such as base pairing, GC content, and structural motifs<br>
                    - Allows users to explore how sequence influences structure<br><br>

                    <b>AI-based structure prediction</b><br>
                    This tool includes a machine learning model that attempts to predict RNA structure based on sequence input.<br>
                    These predictions are simplified approximations and are intended for educational and exploratory use only.<br><br>

                    <b>Important note</b><br>
                    The predicted structures are <b>not scientifically accurate</b> and should not be used for research, medical, or engineering purposes.<br>
                    Real RNA structure prediction requires advanced physics-based models and large-scale biological data.<br><br>

                    <b>Purpose</b><br>
                    The goal of this tool is to make RNA more intuitive and accessible by combining visualization, interaction, and basic AI-driven insights in one place.
                    `;
                }

                else if(type === "why"){
                    text = "<b>Waarom is RNA belangrijk?</b><br><br>RNA speelt een centrale rol in biologie:<br><br>- mRNA: draagt genetische informatie<br>- tRNA: transporteert aminozuren<br>- rRNA: vormt ribosomen<br><br>RNA is ook cruciaal in vaccins en geneeskunde.";
                }

                else if(type === "rna"){
                    text = "<b>Wat is RNA?</b><br><br>RNA (Ribonucleic Acid) is een molecuul dat genetische informatie gebruikt en uitvoert.<br><br>Het bestaat uit vier basen:<br>A (Adenine)<br>U (Uracil)<br>G (Guanine)<br>C (Cytosine)";
                }

                else if(type === "types"){
                    text = "<b>Belangrijke RNA types:</b><br><br>" +
                        "mRNA: draagt genetische code van DNA naar ribosomen<br>" +
                        "rRNA: vormt de structuur van ribosomen<br>" +
                        "tRNA: brengt aminozuren naar ribosomen<br><br>" +
                        "Andere RNA soorten reguleren genexpressie en cellulaire processen.";
                }

                else if(type === "pairing"){
                    text = "<b>Base pairing:</b><br><br>" +
                        "A - U (2 bindingen)<br>" +
                        "G - C (3 bindingen, sterker)<br>" +
                        "G - U (zwakkere 'wobble' binding)<br><br>" +
                        "Deze bindingen zorgen ervoor dat RNA specifieke structuren vormt zoals hairpins.";
                }

                else if(type === "function"){
                    text = "<b>Structuur bepaalt functie</b><br><br>" +
                        "RNA vormt vaak lussen en hairpins.<br><br>" +
                        "Deze structuren maken interactie mogelijk met eiwitten en andere moleculen.<br><br>" +
                        "Zonder juiste structuur werkt RNA niet goed.";
                }

                 openModal(text);

                 window.onclick = function(event) {
                     let modal = document.getElementById("modal");
                     if(event.target === modal){
                         modal.style.display = "none";
                     }
                 }
            }       

            function startApp(){
                document.getElementById("onboarding").style.display = "none";
                localStorage.setItem("seenOnboarding", "true");

                loadExample('hairpin'); // meteen demo

                setTimeout(() => {
                    startGuide();
                }, 500);
            } 

            let step = 0;

            function startGuide(){
                step = 0;
                document.getElementById("guideBox").style.display = "block";
                nextStep();
            }

            function clearHighlights(){
                document.getElementById("seq").classList.remove("highlight");
                document.getElementById("runBtn").classList.remove("highlight");
                document.getElementById("output").classList.remove("highlight");
            }

            function nextStep(){
                clearHighlights();

                let text = "";

                if(step === 0){
                    document.getElementById("seq").classList.add("highlight");
                    text = "Enter an RNA sequence here (A, U, G, C).";
                }

                if(step === 1){
                    document.getElementById("runBtn").classList.add("highlight");
                    text = "Click Run to predict the RNA structure.";
                }

                if(step === 2){
                    document.getElementById("output").classList.add("highlight");
                    text = "Here you see structure info like GC content and base pairing.";
                }

                if(step === 3){
                    text = "Click on bases or labels to learn more about RNA.";
                }

                if(step === 4){
                    document.getElementById("guideBox").style.display = "none";
                    return;
                }

                document.getElementById("guideText").innerText = text;
                step++;
            }

            // =========================
            // 🔹 INIT VIEWER
            // =========================
            window.onload = () => {

                let seen = localStorage.getItem("seenOnboarding");

                let onboarding = document.getElementById("onboarding");

                if(seen){
                    if(onboarding) onboarding.style.display = "none";
                } else {
                    // eerste keer → tonen
                    if(onboarding) onboarding.style.display = "flex";
                }

                // viewer init
                let viewerDiv = document.getElementById("viewer");
                if(viewerDiv){
                    $3Dmol.createViewer(viewerDiv, {
                        backgroundColor: "#020617"
                    });
                }
            };
            
        </script>

        <div id="onboarding" style="
            position: fixed;
            top:0;
            left:0;
            width:100%;
            height:100%;
            background: rgba(2,6,23,0.95);
            color:white;
            display:flex;
            justify-content:center;
            align-items:center;
            z-index:999;
        ">

            <div style="
                max-width:400px;
                text-align:center;
                padding:30px;
                background:#020617;
                border-radius:16px;
                box-shadow:0 20px 60px rgba(0,0,0,0.6);
            ">
                <h2>🧬 Welcome</h2>

                <p style="opacity:0.8; font-size:14px;">
                    This tool helps you understand RNA structure visually.
                </p>

                <div style="text-align:left; font-size:13px; margin-top:15px; line-height:1.6;">
                    1️⃣ Enter an RNA sequence<br>
                    2️⃣ Click <b>Run</b><br>
                    3️⃣ Click on bases and metrics to learn<br>
                </div>

                <button onclick="startApp()" style="margin-top:20px;">
                    Start exploring
                </button>
            </div>
        </div>

        <div id="guideBox" style="display:none;">
            <div id="guideText"></div>
            <button onclick="nextStep()" class="primary-btn small-btn" style="margin-top:10px;">Next</button>
        </div>

        <div id="modal" style="
            display:none;
            position:fixed;
            top:0;
            left:0;
            width:100%;
            height:100%;
            background: rgba(0,0,0,0.7);
            justify-content:center;
            align-items:center;
            z-index:2000;
        ">

            <div style="
                background:#020617;
                padding:25px;
                border-radius:16px;
                max-width:500px;
                width:90%;
                box-shadow:0 20px 60px rgba(0,0,0,0.6);
                position:relative;
            ">

                <button onclick="closeModal()" style="
                    position:absolute;
                    top:10px;
                    right:15px;
                    background:none;
                    border:none;
                    color:#94a3b8;
                    font-size:18px;
                    cursor:pointer;
                ">✕</button>

                <div id="modalContent" style="font-size:14px; line-height:1.6;"></div>

            </div>
        </div>

    </body>
    </html>
    """