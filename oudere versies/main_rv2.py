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
        coords = model(x)

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

@app.get("/demo", response_class=HTMLResponse)
def demo():
    return """
    <html>
    <head>
        <title>Biotech AI</title>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>

        <style>
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
                width: 500px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.6);
            }

            input {
                width: 100%;
                padding: 14px;
                border-radius: 10px;
                border: 1px solid #334155;
                margin-bottom: 10px;
                background: #020617;
                color: white;
            }

            button {
                width: 100%;
                padding: 12px;
                border-radius: 10px;
                border: none;
                background: linear-gradient(90deg, #3b82f6, #06b6d4);
                color: white;
                cursor: pointer;
                margin-top: 5px;
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
                height: 300px;
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

            #downloadBtn {
                margin-top: 15px;
            }

            td:hover {
                opacity: 0.8;
                transform: scale(1.05);
                transition: 0.15s;
            }

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

        </style>
    </head>

    <body>
        <div class="container">
            <h2>🧬 RNA Designer</h2>

            <input id="seq" placeholder="AUGCUAGCUA">

            <div style="margin-bottom:10px; display:flex; gap:6px; flex-wrap:wrap;">
                <button onclick="loadExample('hairpin')">Hairpin (loop)</button>
                <button onclick="loadExample('gc')">Stable RNA (high GC)</button>
                <button onclick="loadExample('none')">No structure</button>
            </div>

            <div id="error" style="color:#f87171; font-size:13px; margin-bottom:10px;"></div>
            <button id="runBtn" onclick="run()" disabled>Run</button>

            <button onclick="startGuide()" style="
                margin-top:8px;
                background: transparent;
                border: 1px solid #334155;
                font-size: 12px;
                opacity: 0.8;
            ">
                ❓ Guide
            </button>

            <button onclick="showInfo('about')" style="
                margin-top:8px;
                background: transparent;
                border: 1px solid #334155;
                font-size: 12px;
                opacity: 0.8;
            ">
                ℹ️ What is this?
            </button>

            <button onclick="showInfo('why')" style="
                margin-top:5px;
                background: transparent;
                border: 1px solid #334155;
                font-size: 12px;
                opacity: 0.8;
            ">
                🧬 Why it matters
            </button>

            <div id="loading" style="margin-top:10px; font-size:13px; opacity:0.8;"></div>

            <div id="output"></div>
            <button id="downloadBtn" onclick="download()" style="display:none;">Download coords</button>

            <div id="viewer"></div>

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

            function showInfo(type){
                let box = document.getElementById("infoBox");

                let text = "";

                if(type === "length"){
                    text = "Sequence length = aantal nucleotiden in de RNA keten.";
                }

                if(type === "gc"){
                    text = "GC Content = percentage G en C basen. Hogere waarde → vaak stabielere structuur.";
                }

                if(type === "score"){
                    text = "Structure Score = hoe consistent de afstanden tussen nucleotiden zijn. Hoger = realistischer.";
                }

                if(type === "pairs"){
                    text = "Base pairs = bindingen tussen nucleotiden (A-U, G-C, G-U). Belangrijk voor RNA structuur.";
                }

                if(type === "dot"){
                    text = "Dot-bracket structuur: ( ) = paired bases, . = vrije bases. Dit is standaard notatie in bio-informatica.";
                }

                if(type === "about"){
                    text = "RNA folding is the process by which a sequence of bases (A, U, G, C) forms a 3D structure. This structure determines its biological function. This tool gives a fast approximation of that structure, helping you understand concepts like base pairing, stability, and hairpins.";
                }

                if(type === "why"){
                    text = "Understanding RNA structure is important in biology, medicine, and biotechnology. For example, mRNA vaccines and gene regulation depend on how RNA folds.";
                }

                box.innerText = text;
                box.style.display = "block";                
            }         

            window.onload = () => {
                if(localStorage.getItem("seenOnboarding")){
                    document.getElementById("onboarding").style.display = "none";                    
                }
            };

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
            <button onclick="nextStep()" style="margin-top:10px;">Next</button>
        </div>

    </body>
    </html>
    """