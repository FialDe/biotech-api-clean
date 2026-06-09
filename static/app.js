import {
    getPairs,
    predictSecondaryStructure,
    dotBracketToPairs,
    detectStems,
    buildHairpinLayout,
    detectHairpins,
    toDotBracket,
    classifyStructure,
    gcContent,
    structureScore
} from "./analysis.js";

import {
    drawSecondaryStructure,
    drawTopologyStructure,
    drawLinearView,
    clearTopologyViewer
} from "./secondary.js";

import {
    renderFromCoords
} from "./viewer3d.js";

import {
    generateAIInsights
} from "./ai.js";

let lastCoords = [];

let currentMode = "professional";

let secondaryHover = null;

const RNA_COLORS = {

    A: "#4ade80",
    U: "#f87171",
    G: "#fb923c",
    C: "#60a5fa"
};

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

input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !btn.disabled) {
        run();
    }
});

async function loadReal(){

    let res = await fetch("/pdb_example");
    let data = await res.json();

    let seq = data.sequence;
    let coords = data.coords;

    renderFromCoords(seq, coords);
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

function loadRNALibrary(type){

    let data = {};

    if(type === "mrna"){

        data = {
            seq: "AUGGCUAACGUAGCUAGCUA",
            title: "mRNA",
            info: `
Messenger RNA (mRNA)

Carries genetic instructions
from DNA to ribosomes.

mRNA is essential for
protein production.
`
        };
    }

    if(type === "trna"){

        data = {
            seq: "GGGCCCAUAGCUCAGUUGG",
            title: "tRNA",
            info: `
Transfer RNA (tRNA)

Transports amino acids
to the ribosome.

Often forms hairpin
and cloverleaf structures.
`
        };
    }

    if(type === "rrna"){

        data = {
            seq: "GGGAAAUCCGGGAAAUCC",
            title: "rRNA",
            info: `
Ribosomal RNA (rRNA)

Forms the structural core
of ribosomes.

Essential for protein synthesis.
`
        };
    }

    if(type === "mirna"){

        data = {
            seq: "UGAGGUAGUAGGUUGUAUAGUU",
            title: "miRNA",
            info: `
MicroRNA (miRNA)

Small regulatory RNA molecules.

Can silence or regulate genes.
`
        };
    }

    document.getElementById("seq").value = data.seq;

    document.getElementById("seq")
        .dispatchEvent(new Event("input"));

    run();

    setTimeout(() => {

        openModal(`
            <b>${data.title}</b><br><br>

            ${data.info}
        `);

    }, 700);
}

function showBaseInfo(base){
    let box = document.getElementById("infoBox");

    let text = "";

    if(base === "A"){
        text = "A (Adenine) usually pairs with U. Forms 2 hydrogen bonds.";
    }

    if(base === "U"){
        text = "U (Uracil) pairs with A. Uracil occurs in RNA instead of DNA.";
    }

    if(base === "G"){
        text = "G (Guanine) pairs with C (strong interaction, 3 hydrogen bonds) and sometimes with U (wobble pair).";
    }

    if(base === "C"){
        text = "C (Cytosine) pairs with G. This is the strongest interaction in RNA.";
    }

    box.innerText = text;
    box.style.display = "block";
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

    // lastCoords = data.coords;

    // 🔵 werk-variabele
    let coords = data.coords;

    // schaal
    let maxVal = Math.max(...coords.flat().map(v => Math.abs(v)));
    let scale = maxVal === 0 ? 1 : 10 / maxVal;
    coords = coords.map(c => c.map(v => v * scale));

    lastCoords = coords;

    let dot =
        data.dot_bracket;

    let pairs =
        dotBracketToPairs(dot);

    let structureSource = "vienna";

    if(pairs.length === 0){

        if(currentMode === "educational"){

            let fallback =
                predictSecondaryStructure(seq);

            if(
                fallback &&
                fallback.pairs &&
                fallback.pairs.length > 0
            ){

                dot =
                    fallback.dotBracket;

                pairs =
                    fallback.pairs;

                structureSource =
                    "educational";
            }
            else{

                structureSource =
                    "none";
            }

        } else {

            structureSource =
                "none";
        }
    }

    let secondaryInfo =
        document.getElementById(
            "secondaryInfo"
        );

    let structureStatus =
        document.getElementById(
            "structureStatus"
        );

    if(structureSource === "vienna"){

        if(currentMode === "professional"){

            structureStatus.innerHTML = `
            <div>

                <div style="
                    font-size:11px;
                    letter-spacing:1px;
                    color:#64748b;
                    margin-bottom:8px;
                ">
                    VIENNARNA ANALYSIS
                </div>

                <div style="
                    color:#cbd5e1;
                    line-height:1.7;
                    font-size:13px;
                ">

                    Status:
                    <b>Stable Structure Detected</b>

                    <br>

                    Source:
                    <b>ViennaRNA</b>

                    <br>

                    MFE:
                    <b>${data.mfe.toFixed(2)} kcal/mol</b>

                </div>

            </div>
            `;

        } else {

            structureStatus.innerHTML = `
            <div>

                <div style="
                    font-size:11px;
                    letter-spacing:1px;
                    color:#64748b;
                    margin-bottom:8px;
                ">
                    VIENNARNA ANALYSIS
                </div>

                <div style="
                    color:#cbd5e1;
                    line-height:1.7;
                    font-size:13px;
                ">

                    ✓ Stable secondary structure detected

                    <br><br>

                    Source:
                    <b>ViennaRNA</b>

                    <br>

                    MFE:
                    <b>${data.mfe.toFixed(2)} kcal/mol</b>

                    <br><br>

                    Lower (more negative) MFE values generally
                    indicate increased thermodynamic stability.

                </div>

            </div>
            `;
        }
    }

    if(
        structureSource === "none" &&
        currentMode === "professional"
    ){

        structureStatus.innerHTML = `
            <div style="color:#f59e0b">

            ⚠ No stable secondary structure predicted by ViennaRNA

            <br><br>

            No thermodynamically stable RNA fold was detected.

            <br><br>

            Switch to Educational Mode
            to view a possible educational structure prediction.

            </div>
        `;
    }

    if(
        structureSource === "educational"
    ){

        structureStatus.innerHTML = `
            <div style="color:#f59e0b">

            ⚠ No stable secondary structure predicted by ViennaRNA

            <br><br>

            Showing educational structure prediction.

            <br><br>

            Structure source:
            Educational Predictor

            </div>
        `;
    }

    if(
        structureSource === "none" &&
        currentMode === "educational"
    ){

        structureStatus.innerHTML = `
            <div style="color:#ef4444">

            ✗ No secondary structure detected

            <br><br>

            No complementary base pairs were found.

            <br><br>

            This sequence is unlikely to form a meaningful RNA secondary structure.

            </div>
        `;
    }

    let stems =
        detectStems(pairs);

    let hairpins =
        detectHairpins(stems);

    let gc = parseFloat(gcContent(seq));

    console.log("SEQ:", seq);
    console.log("DOT:", dot);
    console.log("PAIRS:", pairs);
    console.log("STEMS:", stems);

    let insights = generateAIInsights(
        seq,
        pairs,
        hairpins,
        gc,
        currentMode
    );         

    let outputDiv = document.getElementById("output");
    outputDiv.classList.remove("show");
    if(currentMode === "educational"){

        outputDiv.innerHTML = `
            <div style="font-size:13px; line-height:1.7;">

                <b>
                <span onclick="showInfo('rna')" style="cursor:pointer;color:#38bdf8">RNA</span> |
                <span onclick="showInfo('types')" style="cursor:pointer;color:#38bdf8">Types</span> |
                <span onclick="showInfo('pairing')" style="cursor:pointer;color:#38bdf8">Pairing</span>
                </b>

                <br><br>

                <b><span onclick="showInfo('length')" style="cursor:pointer;color:#38bdf8">Sequence length</span>:</b> ${data.length}<br>

                <b><span onclick="showInfo('gc')" style="cursor:pointer;color:#38bdf8">GC Content</span>:</b> ${gcContent(seq)}%<br>

                <b><span onclick="showInfo('pairs')" style="cursor:pointer;color:#38bdf8">Base pairs</span>:</b> ${pairs.length}<br>

                <b><span onclick="showInfo('dot')" style="cursor:pointer;color:#38bdf8">Structure</span>:</b> ${dot}<br>

                <b>Structure Type:</b> ${classifyStructure(pairs, stems, hairpins)}<br><br>

                <div style="
                    background:rgba(15,23,42,0.6);
                    padding:10px;
                    border-radius:10px;
                    border:1px solid #334155;
                ">
                    <b>Learning Note</b><br><br>

                    RNA molecules fold because certain bases attract each other.<br><br>

                    G-C interactions are generally stronger than A-U interactions,
                    which often increases structural stability.
                </div>

            </div><br>

            ${formatCoords(coords, seq)}
        `;

    } else {

        outputDiv.innerHTML = `
            <div style="font-size:13px; line-height:1.6;">

                <div style="
                    display:grid;
                    grid-template-columns:1fr 1fr;
                    gap:10px;
                ">

                    <div class="metric-card">
                        <div class="metric-label">SEQUENCE</div>
                        <div class="metric-value">${data.length}</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">GC CONTENT</div>
                        <div class="metric-value">${gcContent(seq)}%</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">HAIRPINS</div>
                        <div class="metric-value">${hairpins.length}</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">TOPOLOGY</div>

                        <div
                            class="metric-value"
                            style="
                                font-size:14px;
                                line-height:1.3;
                            "
                        >
                            ${classifyStructure(
                                pairs,
                                stems,
                                hairpins
                            )}
                        </div>
                    </div>

                </div>
                
            </div>
        `;
    }

        let aiPanel = document.getElementById("aiPanel");
        let aiContent = document.getElementById("aiContent");

        aiPanel.style.display = "block";

        aiContent.innerHTML = insights
            .map(i => `<div class="ai-line">${i}</div>`)
            .join("");

    setTimeout(() => {
        outputDiv.classList.add("show");
    }, 50);

    window.lastSeq = seq;
    window.lastPairs = pairs;
    window.lastStems = stems;

    let vp = document.getElementById("viewerPlaceholder");

    if(vp){
        vp.style.display = "none";
    }

    let sp = document.getElementById("secondaryPlaceholder");

    if(sp){
        sp.style.display = "none";
    }

    // drawSecondaryStructure(seq, pairs);
    if(structureSource !== "none"){

        drawTopologyStructure(
            seq,
            pairs,
            stems
        );

    } else {

        clearTopologyViewer();
    }

    drawLinearView(
        seq,
        pairs
    );

    updateStructureFeatures(
        seq,
        pairs,
        stems,
        hairpins
    );

    updateBiologicalInterpretation(
        seq,
        pairs,
        stems,
        hairpins,
        gc,
        data.mfe
    );

    updatePairingTable(
        seq,
        pairs
    );
    
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

function handleFileUpload(event){

    let file = event.target.files[0];

    if(!file) return;

    let reader = new FileReader();

    reader.onload = function(e){

        let text = e.target.result;

        // FASTA headers verwijderen
        text = text
            .split("\n")
            .filter(line => !line.startsWith(">"))
            .join("");

        // whitespace verwijderen
        text = text.replace(/\s/g, "");

        // uppercase
        text = text.toUpperCase();

        // alleen RNA bases houden
        text = text.replace(/[^AUGC]/g, "");

        if(text.length === 0){

            showNotification("No valid RNA sequence found");

            return;
        }

        document.getElementById("seq").value = text;

        document.getElementById("seq")
            .dispatchEvent(new Event("input"));

        showNotification(
            `RNA sequence loaded (${text.length} bases)`
        );

        run();
    };

    reader.readAsText(file);
    event.target.value = ""; // reset file input
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
        text = "Sequence length = the number of nucleotides in the RNA chain.";
    }

    else if(type === "gc"){
        text = "GC Content = percentage G and C bases.<br><br>A higher value generally indicates increased structural stability because G-C interactions are stronger than A-U interactions.";
    }

    else if(type === "score"){
        text = "Structure Score = how consistent the distances between nucleotides are.<br><br>A higher score generally indicates a more stable and realistic structure.";
    }

    else if(type === "pairs"){
        text = "Base pairs are interactions between nucleotides.<br><br>These interactions form the basis of RNA structure and influence how the RNA chain folds.";
    }

    else if(type === "dot"){
        text = "Dot-bracket notation:<br><br>( ) = paired bases<br>. = unpaired bases<br><br>This is a standard method for describing RNA secondary structure.";
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
        text = "<b>Why is RNA important?</b><br><br>RNA plays a central role in biology:<br><br>- mRNA: carries genetic information<br>- tRNA: transports amino acids<br>- rRNA: forms ribosomes<br><br>RNA is also crucial in vaccines and modern medicine.";
    }

    else if(type === "rna"){
        text = "<b>What is RNA?</b><br><br>RNA (Ribonucleic Acid) is a molecule involved in storing, transferring, and regulating genetic information.<br><br>It consists of four bases:<br>A (Adenine)<br>U (Uracil)<br>G (Guanine)<br>C (Cytosine)";
    }

    else if(type === "types"){
        text = "<b>Major RNA types:</b><br><br>" +
            "mRNA: carries genetic information from DNA to ribosomes<br>" +
            "rRNA: forms the structural core of ribosomes<br>" +
            "tRNA: transports amino acids to ribosomes<br><br>" +
            "Other RNA molecules regulate gene expression and cellular processes.";
    }

    else if(type === "pairing"){
        text = "<b>Base pairing:</b><br><br>" +
            "A - U (2 hydrogen bonds)<br>" +
            "G - C (3 hydrogen bonds, stronger)<br>" +
            "G - U (weaker wobble interaction)<br><br>" +
            "These interactions allow RNA to form specific structures such as hairpins.";
    }

    else if(type === "function"){
        text = "<b>Structure determines function</b><br><br>" +
            "RNA often forms loops and hairpin structures.<br><br>" +
            "These structures enable interactions with proteins and other molecules.<br><br>" +
            "Without the correct structure, RNA cannot function properly.";
    }

        openModal(text);

        // window.onclick = function(event) {
        //     let modal = document.getElementById("modal");
        //     if(event.target === modal){
        //         modal.style.display = "none";
        //     }
        // }
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

function openGuide(){

    let text = `

    <div style="max-width:700px; line-height:1.7;">

        <h2 style="margin-top:0;color:#38bdf8;">
            RNA Structure Explorer Guide
        </h2>

        <p>
            This application combines RNA visualization,
            structure analysis, and interactive learning tools.
        </p>

        <hr style="border-color:#334155; margin:20px 0;">

        <h3 style="color:#38bdf8;">Getting Started</h3>

        <ul>
            <li>Enter an RNA sequence using A, U, G, and C</li>
            <li>Click Run to predict the structure</li>
            <li>Rotate and zoom the 3D viewer</li>
            <li>Hover nucleotides for coordinates</li>
        </ul>

        <hr style="border-color:#334155; margin:20px 0;">

        <h3 style="color:#38bdf8;">Interactive Features</h3>

        <ul>
            <li>Hover nucleotides to inspect coordinates</li>
            <li>Hover pairing lines in Educational Mode</li>
            <li>Explore RNA molecule types</li>
            <li>Analyze GC content and hairpins</li>
            <li>Download coordinate data</li>
        </ul>

        <hr style="border-color:#334155; margin:20px 0;">

        <h3 style="color:#38bdf8;">Educational Mode</h3>

        <ul>
            <li>Learning-focused explanations</li>
            <li>RNA interaction descriptions</li>
            <li>RNA Library examples</li>
            <li>Biological context and insights</li>
        </ul>

        <hr style="border-color:#334155; margin:20px 0;">

        <h3 style="color:#38bdf8;">Professional Mode</h3>

        <ul>
            <li>Compact analysis interface</li>
            <li>Structure metrics dashboard</li>
            <li>Cleaner visualization workflow</li>
            <li>Reduced educational overlays</li>
        </ul>

        <div style="margin-top:30px; text-align:center;">

            <button class="mini-btn"
                onclick="
                    closeModal();
                    setTimeout(startGuide,300);
                "
            >
                Start Interactive Walkthrough
            </button>

        </div>

    </div>
    `;

    openModal(text);
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

    let toggle =
        document.getElementById(
            "pairingToggle"
        );

    if(toggle){

        toggle.addEventListener(
            "click",
            togglePairingPanel
        );
    }

    setMode("professional");
};

// let currentMode = "professional";

function setMode(mode){

    currentMode = mode;

    let aiTitle = document.querySelector(".ai-title");
    let badge = document.getElementById("modeBadge");

    document.body.classList.remove(
        "educational-mode",
        "professional-mode"
    );

    if(mode === "educational"){

        // document.getElementById("eduLibrary").style.display = "block";

        document.body.classList.add("educational-mode");

        aiTitle.innerText = "AI Learning Insights";

        badge.innerText = "EDUCATIONAL MODE";

        document.querySelector(
            "#pairingPanel"
        ).closest(".panel").style.display = "block";

        document.getElementById(
            "pairingWrapper"
        ).style.display = "none";

        document.getElementById(
            "aiPanel"
        ).parentElement.style.display =
            "block";

        showNotification("Educational mode enabled");

    } else {

        //document.getElementById("eduLibrary").style.display = "none";

        document.body.classList.add("professional-mode");

        aiTitle.innerText =
            "Biological Interpretation";

        badge.innerText = "PROFESSIONAL MODE";

        document.querySelector(
            "#pairingPanel"
        ).closest(".panel").style.display = "none";

        document.getElementById(
            "aiPanel"
        ).parentElement.style.display =
            "none";

        showNotification("Professional mode enabled");
    }
}

function showNotification(text){

    let n = document.createElement("div");

    n.innerText = text;

    n.style.position = "fixed";
    n.style.bottom = "20px";
    n.style.right = "20px";

    n.style.background = "#0f172a";
    n.style.border = "1px solid #334155";

    n.style.padding = "12px 16px";

    n.style.borderRadius = "10px";

    n.style.color = "#e2e8f0";

    n.style.zIndex = "5000";

    document.body.appendChild(n);

    setTimeout(() => {
        n.remove();
    }, 2000);
}

function togglePairingPanel(){

    let panel =
        document.getElementById(
            "pairingWrapper"
        );

    let title =
        document.getElementById(
            "pairingToggle"
        );

    if(panel.style.display === "none"){

        panel.style.display = "block";

        title.innerText =
            "TECHNICAL DETAILS ▲";

    } else {

        panel.style.display = "none";

        title.innerText =
            "TECHNICAL DETAILS ▼";
    }
}

function triggerDownload(){

    setTimeout(() => {
        download();
    }, 50);
}

function updateStructureFeatures(
    seq,
    pairs,
    stems,
    hairpins
){

    let gc =
        (
            [...seq]
            .filter(x =>
                x==="G" || x==="C"
            )
            .length
            / seq.length
            * 100
        ).toFixed(1);

    let stemLength =
        stems.length
            ? Math.max(
                ...stems.map(
                    s => s.length
                )
            )
            : 0;

    let loopSize =
        Math.max(
            seq.length - pairs.length * 2,
            0
        );

    document
    .getElementById(
        "featuresPanel"
    )
    .innerHTML = `

        <div class="feature-card">

            <div class="feature-svg stem-svg">

            <svg viewBox="0 0 24 24"
                class="feature-icon-svg">

                <path
                    d="M8 4V20"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                />

                <path
                    d="M16 4V20"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                />

                <path
                    d="M8 7H16"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                />

                <path
                    d="M8 12H16"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                />

                <path
                    d="M8 17H16"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                />

            </svg>

            </div>

            <div class="feature-text">

                <div class="feature-title">
                    Stem length
                </div>

                <div class="feature-value">
                    ${stemLength} bp
                </div>

            </div>

        </div>

        <div class="feature-card">

            <div class="feature-svg loop-svg">

            <svg viewBox="0 0 24 24"
                class="feature-icon-svg">

                <circle
                    cx="12"
                    cy="12"
                    r="7"
                    stroke="currentColor"
                    stroke-width="2"
                    fill="none"
                    stroke-dasharray="4 4"
                />

            </svg>

            </div>

            <div class="feature-text">

                <div class="feature-title">
                    Loop size
                </div>

                <div class="feature-value">
                    ${loopSize} nt
                </div>

            </div>

        </div>

        <div class="feature-card">

            <div class="feature-svg hairpin-svg">

            <svg viewBox="0 0 24 24"
                class="feature-icon-svg">

                <path
                    d="M8 18V10
                    C8 6 10 4 12 4
                    C14 4 16 6 16 10
                    V18"

                    stroke="currentColor"
                    stroke-width="2"
                    fill="none"
                    stroke-linecap="round"
                />

                <path
                    d="M9 18H15"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                />

                <path
                    d="M9 14H15"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                />

            </svg>

            </div>

            <div class="feature-text">

                <div class="feature-title">
                    Hairpin loop
                </div>

                <div class="feature-value">
                    ${hairpins.length}
                </div>

            </div>

        </div>

        <div class="feature-card">

            <div class="feature-svg stable-svg">

            <svg viewBox="0 0 24 24"
                class="feature-icon-svg">

                <path
                    d="M12 4L18 7V12
                    C18 16 15.5 18.5 12 20
                    C8.5 18.5 6 16 6 12V7L12 4Z"

                    stroke="currentColor"
                    stroke-width="2"
                    fill="none"
                />

                <path
                    d="M9.5 12.5L11.5 14.5L15 10.5"

                    stroke="currentColor"
                    stroke-width="2"
                    fill="none"
                    stroke-linecap="round"
                />

            </svg>

         </div>

            <div class="feature-text">

                <div class="feature-title">
                    GC-rich and stable
                </div>

                <div class="feature-value">
                    ${gc}% GC
                </div>

            </div>

        </div>
    `;
}

function updateBiologicalInterpretation(
    seq,
    pairs,
    stems,
    hairpins,
    gc,
    mfe
){

    let text = [];

    text.push(
        `This RNA contains ${hairpins.length} hairpin structure(s).`
    );

    if(gc >= 60){

        text.push(
            "High GC content suggests increased structural stability."
        );

    } else if(gc >= 40){

        text.push(
            "Moderate GC content suggests average structural stability."
        );

    } else {

        text.push(
            "Low GC content may reduce structural stability."
        );
    }

    if(stems.length > 1){

        text.push(
            "Multiple stems indicate a more complex folding pattern."
        );
    }

    if(mfe < -5){

        text.push(
            "ViennaRNA predicts a relatively stable fold."
        );

    } else {

        text.push(
            "Predicted fold stability is limited."
        );
    }

    if(pairs.length === 0){

        text.push(
            "No significant secondary structure was detected."
        );
    }

    document.getElementById(
        "biologicalInterpretation"
    ).innerHTML = `

        <div class="panel-title">
            BIOLOGICAL INTERPRETATION
        </div>

        ${text.map(t =>
            `<div class="ai-line">• ${t}</div>`
        ).join("")}
    `;
}

function updatePairingTable(
    seq,
    pairs
){

    let table = `

        <table class="pair-table">

            <tr>
                <th>Pos</th>
                <th>Base</th>
                <th>Pair</th>
            </tr>
    `;

    for(let i=0;i<seq.length;i++){

        let found =
            pairs.find(
                p => p[0]===i || p[1]===i
            );

        let partner = "-";

        if(found){

            partner =
                found[0]===i
                ? found[1]+1
                : found[0]+1;
        }

        table += `

            <tr>
                <td>${i+1}</td>
                <td>${seq[i]}</td>
                <td>${partner}</td>
            </tr>
        `;
    }

    table += "</table>";

    document
    .getElementById(
        "pairingPanel"
    )
    .innerHTML = table;
}

// =========================
// GLOBAL MODAL CLOSE
// =========================
window.addEventListener("click", function(event){

    let modal = document.getElementById("modal");

    if(event.target === modal){

        modal.style.display = "none";
    }
});

window.run = run;
window.loadExample = loadExample;
window.randomSeq = randomSeq;
window.loadReal = loadReal;

window.showInfo = showInfo;
window.setMode = setMode;

window.startApp = startApp;
window.startGuide = startGuide;
window.nextStep = nextStep;

window.openGuide = openGuide;
window.openModal = openModal;
window.closeModal = closeModal;

window.download = download;
window.triggerDownload = triggerDownload;

window.loadRNALibrary = loadRNALibrary;
window.handleFileUpload = handleFileUpload;
window.showBaseInfo = showBaseInfo;