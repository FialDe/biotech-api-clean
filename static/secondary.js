let secondaryHover = null;
let currentSecondaryRenderer = "topology";

const RNA_COLORS = {

    A: "#4ade80",
    U: "#f87171",
    G: "#fb923c",
    C: "#60a5fa"
};

export function drawSecondaryStructure(seq, pairs){

    currentSecondaryRenderer = "linear";

    let canvas = document.getElementById("secondaryCanvas");

    let ctx = canvas.getContext("2d");

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    ctx.clearRect(0,0,canvas.width,canvas.height);

    let w = canvas.width;
    let h = canvas.height;

    let padding = 40;

    let y = h - 45;

    let spacing =
        (w - padding*2) / Math.max(seq.length-1,1);

    // =========================
    // PAIRING ARCS
    // =========================
    pairs.forEach(p => {

        let i = p[0];
        let j = p[1];

        let x1 = padding + i*spacing;
        let x2 = padding + j*spacing;

        let mid = (x1+x2)/2;

        let arcHeight =
            Math.abs(j-i) * 10;

        ctx.beginPath();

        let b1 = seq[i];
        let b2 = seq[j];

        if(
            (b1==="G" && b2==="C") ||
            (b1==="C" && b2==="G")
        ){

            // sterke G-C pair
            ctx.strokeStyle = "#60a5fa";
        }

        else if(
            (b1==="A" && b2==="U") ||
            (b1==="U" && b2==="A")
        ){

            // standaard A-U pair
            ctx.strokeStyle = "#22c55e";
        }

        else{

            // wobble pair
            ctx.strokeStyle = "#fb923c";
        }

        ctx.lineWidth = 4;

        ctx.moveTo(x1,y);

        ctx.quadraticCurveTo(
            mid,
            y - arcHeight,
            x2,
            y
        );

        ctx.stroke();
    });

    // =========================
    // NUCLEOTIDES
    // =========================
    window.secondaryNodes = [];

    for(let i=0;i<seq.length;i++){

        let x = padding + i*spacing;

        window.secondaryNodes.push({
            x,
            y,
            index:i,
            base:seq[i]
        });

        ctx.beginPath();

        ctx.fillStyle =
            RNA_COLORS[seq[i]] || "#94a3b8";

        ctx.arc(x,y,14,0,Math.PI*2);

        ctx.fill();

        if(
            secondaryHover &&
            secondaryHover.index === i
        ){

            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 3;
            ctx.shadowColor = "#ffffff";
            ctx.shadowBlur = 12;
            ctx.stroke();
            ctx.shadowBlur = 0;
        }

        ctx.fillStyle = "#020617";
        ctx.strokeStyle = "#020617";
        ctx.lineWidth = 2;

        ctx.stroke();

        ctx.font = "bold 13px Inter";
        ctx.textAlign = "center";
        ctx.fillText(seq[i],x,y+4);
    }
}

document
.getElementById("secondaryCanvas")
.addEventListener("mousemove", e => {

    let canvas =
        document.getElementById("secondaryCanvas");

    let rect =
        canvas.getBoundingClientRect();

    let x =
        e.clientX - rect.left;

    let y =
        e.clientY - rect.top;

    if(!window.secondaryNodes) return;

    let previousHover = secondaryHover;

    secondaryHover = null;

    window.secondaryNodes.forEach(node => {

        let dx = x - node.x;
        let dy = y - node.y;

        let dist =
            Math.sqrt(dx*dx + dy*dy);

        if(dist < 16){

            secondaryHover = node;
        }
    });

    canvas.style.cursor =
        secondaryHover ? "pointer" : "default";

    let info =
        document.getElementById("secondaryInfo");

    if(secondaryHover){

        info.innerHTML = `
            <b>Hovering nucleotide:</b><br>
            ${secondaryHover.base}
            (position ${secondaryHover.index + 1})
        `;
    }

    else{

        info.innerHTML =
            "Hover over a nucleotide";
    }

    let changed = false;

    if(!previousHover && secondaryHover){
        changed = true;
    }

    else if(previousHover && !secondaryHover){
        changed = true;
    }

    else if(
        previousHover &&
        secondaryHover &&
        previousHover.index !== secondaryHover.index
    ){
        changed = true;
    }

    if(
        changed &&
        window.lastSeq &&
        window.lastPairs
    ){

        if(currentSecondaryRenderer === "topology"){

            drawTopologyStructure(
                window.lastSeq,
                window.lastPairs,
                window.lastStems
            );

        } else {

            drawSecondaryStructure(
                window.lastSeq,
                window.lastPairs
            );
        }
    }
});

function buildHairpinLayout(
    seq,
    stems,
    width,
    height
){

    let points =
        Array(seq.length).fill(null);

    let stem = stems[0];

    let centerX =
        width / 2;

    let topY = 120;

    let spacing = 36;

    // =========================
    // STEM
    // =========================

    stem.forEach((pair,index)=>{

        let y =
            topY +
            index * spacing;

        points[pair[0]] = {

            x:centerX - 70,
            y
        };

        points[pair[1]] = {

            x:centerX + 70,
            y
        };
    });

    // =========================
    // LOOP
    // =========================

    let unpaired = [];

    for(let i=0;i<seq.length;i++){

        if(!points[i]){

            unpaired.push(i);
        }
    }

    let radius = 70;

    unpaired.forEach((idx,k)=>{

        let t =
            unpaired.length === 1
            ? 0.5
            : k/(unpaired.length-1);

        let angle =
            Math.PI -
            t * Math.PI;

        points[idx] = {

            x:
                centerX +
                Math.cos(angle) * radius,

            y:
                topY +
                stem.length * spacing + 40 +
                Math.sin(angle) * radius
        };
    });

    return points;
}

function buildMultiHairpinLayout(
    seq,
    stems,
    width,
    height
){

    let points =
        Array(seq.length).fill(null);

    let centerY =
        height * 0.5;

    stems.forEach((stem, stemIndex) => {

        let centerX =
            width * (
                (stemIndex + 1)
                /
                (stems.length + 1)
            );

        let leftSide =
            stem.map(p => p[0]);

        let rightSide =
            stem.map(p => p[1]);

        leftSide.forEach((idx, i) => {

            points[idx] = {

                x: centerX - 40,

                y:
                    centerY
                    -
                    (leftSide.length * 12)
                    +
                    i * 24
            };

        });

        rightSide.forEach((idx, i) => {

            points[idx] = {

                x: centerX + 40,

                y:
                    centerY
                    -
                    (rightSide.length * 12)
                    +
                    i * 24
            };

        });

    });

    //     for(let i=0;i<points.length;i++){

    //     if(!points[i]){

    //         points[i] = {

    //             x: width / 2,
    //             y: height / 2
    //         };
    //     }
    // }

    let unpaired = [];

    for(let i=0;i<points.length;i++){

        if(!points[i]){

            unpaired.push(i);
        }
    }

    let radius = 60;

    unpaired.forEach((idx,k)=>{

        let angle =
            (k / Math.max(unpaired.length,1))
            *
            Math.PI * 2;

        points[idx] = {

            x:
                width/2 +
                Math.cos(angle) * radius,

            y:
                height/2 +
                Math.sin(angle) * radius
        };
    });

    return points;
}

export function drawTopologyStructure(seq, pairs, stems){

    currentSecondaryRenderer = "topology";

    let canvas =
        document.getElementById("secondaryCanvas");

    let ctx = canvas.getContext("2d");

    // scherpe rendering
    const dpr = window.devicePixelRatio || 1;

    canvas.width =
        canvas.clientWidth * dpr;

    canvas.height =
        canvas.clientHeight * dpr;

    ctx.setTransform(1,0,0,1,0,0);
    ctx.scale(dpr,dpr);

    ctx.clearRect(
        0,
        0,
        canvas.clientWidth,
        canvas.clientHeight
    );

    let width = canvas.clientWidth;
    let height = canvas.clientHeight;

    let centerX = width / 2;
    let centerY = height / 2;

    // =========================
    // LAYOUT SETTINGS
    // =========================

    let radius =
        Math.min(width,height) * 0.32;

    let nodeRadius = 13;

    let points = null;

    if(
            stems.length === 1 &&
            stems[0].length >= 2
        ){

            points =
                buildHairpinLayout(
                    seq,
                    stems,
                    width,
                    height
                );
        }
        else if(
            stems.length > 1
        ){

            points =
                buildMultiHairpinLayout(
                    seq,
                    stems,
                    width,
                    height
                );
        }

    // =========================
    // PLACE NODES ON CURVE
    // =========================
    if (!points){

        for(let i=0;i<seq.length;i++){

            let angle =
                Math.PI * 0.2 +
                (i / Math.max(seq.length-1,1))
                * Math.PI * 1.6;

            let x =
                centerX +
                Math.cos(angle) * radius * 1.15;

            let y =
                centerY +
                Math.sin(angle) * radius * 0.68;

            // =========================
            // STEM CLUSTERING
            // =========================

            pairs.forEach(pair => {

                let a = pair[0];
                let b = pair[1];

                if(i === a || i === b){

                    let partner =
                        (i === a) ? b : a;

                    let partnerAngle =
                        Math.PI * 0.2 +
                        (partner / Math.max(seq.length-1,1))
                        * Math.PI * 1.6;

                    // trek paired nodes
                    // iets naar elkaar toe

                    x +=
                        Math.cos(partnerAngle) * 18;

                    y +=
                        Math.sin(partnerAngle) * 12;
                }
            });

            points.push({x,y});

        }
    }

    // =========================
    // BACKBONE
    // =========================

    ctx.strokeStyle = "#64748b";
    ctx.lineWidth = 5;

    ctx.beginPath();

    for(let i=0; i<points.length-1; i++){

        let p1 = points[i];
        let p2 = points[i+1];

        // midpoint
        let mx = (p1.x + p2.x) / 2;
        let my = (p1.y + p2.y) / 2;

        if(i === 0){

            ctx.moveTo(p1.x, p1.y);
        }

        // smooth quadratic backbone
        ctx.quadraticCurveTo(
            p1.x,
            p1.y,
            mx,
            my
        );
    }

    // laatste segment
    let last =
        points[points.length-1];

    ctx.lineTo(last.x, last.y);

    ctx.stroke();
    
    // =========================
    // STEM RENDERING
    // =========================

    stems.forEach((stem, stemIndex) => {

        // dynamische kleurintensiteit
        let alpha =
            Math.min(0.35 + stem.length * 0.08, 0.9);

        // dikkere stems bij langere helices
        let stemWidth =
            Math.min(2 + stem.length * 0.6, 6);

        stem.forEach((pair, pairIndex) => {

            let p1 = points[pair[0]];
            let p2 = points[pair[1]];

            if(!p1 || !p2){

                console.log(
                    "MISSING POINTS:",
                    pair
                );

                return;
            }

            // midpoint
            let midX =
                (p1.x + p2.x) / 2;

            let midY =
                (p1.y + p2.y) / 2;

            // stem curvature
            let curveStrength =
                25 + stem.length * 6;

            // parallel stem effect
            let offset =
                (pairIndex - (stem.length-1)/2) * 4;

            ctx.strokeStyle =
                `rgba(34,197,94,${alpha})`;

            ctx.lineWidth = stemWidth;

            ctx.beginPath();

            ctx.moveTo(p1.x, p1.y);

            ctx.quadraticCurveTo(
                midX,
                midY - curveStrength + offset,
                p2.x,
                p2.y
            );

            ctx.stroke();
        });
    });

    // =========================
    // DRAW NODES
    // =========================

    points.forEach((p,index)=>{

        ctx.fillStyle =
            RNA_COLORS[seq[index]]
            || "#94a3b8";

        ctx.beginPath();

        ctx.arc(
            p.x,
            p.y,
            nodeRadius,
            0,
            Math.PI*2
        );

        ctx.closePath();

        ctx.fill();

        // hover highlight
        if(
            secondaryHover &&
            secondaryHover.index === index
        ){

            ctx.beginPath();

            ctx.arc(
                p.x,
                p.y,
                nodeRadius,
                0,
                Math.PI*2
            );

            ctx.closePath();

            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 3;

            ctx.shadowColor = "#ffffff";
            ctx.shadowBlur = 12;

            ctx.stroke();

            ctx.shadowBlur = 0;
        }

        ctx.fillStyle = "white";

        ctx.font = "12px Inter";

        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        ctx.fillText(
            seq[index],
            p.x,
            p.y
        );
    });

    // bewaren voor hover
    window.secondaryNodes = points.map((p,i)=>({

        x:p.x,
        y:p.y,
        index:i,
        base:seq[i]
    }));
}

export function clearTopologyViewer(){

    let canvas =
        document.getElementById(
            "secondaryCanvas"
        );

    if(!canvas) return;

    let ctx =
        canvas.getContext("2d");

    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );
}

export function drawLinearView(seq, pairs){

    let canvas =
        document.getElementById(
            "linearCanvas"
        );

    if(!canvas) return;

    let ctx =
        canvas.getContext("2d");

    let rect =
        canvas.getBoundingClientRect();

    let dpr =
        window.devicePixelRatio || 1;

    canvas.width =
        rect.width * dpr;

    canvas.height =
        rect.height * dpr;

    ctx.setTransform(1,0,0,1,0,0);
    ctx.scale(dpr,dpr);

    ctx.clearRect(
        0,
        0,
        rect.width,
        rect.height
    );

    let width = rect.width;
    let height = rect.height;

    let padding = 40;

    let spacing =
        (width - padding*2) /
        Math.max(seq.length-1,1);

    let y =
        height * 0.72;

    let colors = {

        A:"#4ade80",
        U:"#f87171",
        G:"#fb923c",
        C:"#60a5fa"
    };

    // =========================
    // PAIRING ARCS
    // =========================

    pairs.forEach(pair => {

        let i = pair[0];
        let j = pair[1];

        let x1 =
            padding + i * spacing;

        let x2 =
            padding + j * spacing;

        let arcHeight =
            Math.abs(x2 - x1) * 0.22;

        ctx.beginPath();

        ctx.strokeStyle =
            "rgba(34,197,94,0.9)";

        ctx.lineWidth = 2;

        ctx.moveTo(x1,y);

        ctx.quadraticCurveTo(
            (x1+x2)/2,
            y - arcHeight,
            x2,
            y
        );

        ctx.stroke();
    });

    // =========================
    // NUCLEOTIDES
    // =========================

    for(let i=0;i<seq.length;i++){

        let x =
            padding + i * spacing;

        ctx.beginPath();

        ctx.arc(
            x,
            y,
            10,
            0,
            Math.PI*2
        );

        ctx.fillStyle =
            colors[seq[i]] || "#94a3b8";

        ctx.fill();

        ctx.fillStyle = "#ffffff";

        ctx.font = "11px Inter";

        ctx.textAlign = "center";

        ctx.textBaseline = "middle";

        ctx.fillText(
            seq[i],
            x,
            y
        );
    }
}