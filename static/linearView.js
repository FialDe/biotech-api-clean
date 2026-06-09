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