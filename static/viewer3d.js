import {
    getPairs,
    detectHairpins,
    toDotBracket,
    gcContent
} from "./analysis.js";

import {
    drawSecondaryStructure
} from "./secondary.js";

export function renderFromCoords(
    seq,
    coords,
    currentMode = "professional"
){

    // lastCoords = coords;

    // schaal (zelfde als nu)
    let maxVal = Math.max(...coords.flat().map(v => Math.abs(v)));
    let scale = maxVal === 0 ? 1 : 10 / maxVal;
    let scaled = coords.map(c => c.map(v => v * scale));

    let pairs = getPairs(seq, scaled);
    let hairpins = detectHairpins(pairs);
    let dot = toDotBracket(seq, pairs);

    let insights = [];

    let gc = parseFloat(gcContent(seq));

    if(currentMode === "educational"){

        if(gc > 60){
            insights.push("✓ High GC content may increase structural stability");
            insights.push("✓ G-C pairs form 3 hydrogen bonds");
        }

        if(gc < 40){
            insights.push("⚠ Low GC content may reduce RNA stability");
        }

        if(pairs.length >= 3){
            insights.push("✓ Multiple base pair interactions detected");
            insights.push("✓ RNA may fold into stem-loop structures");
        }

        if(hairpins.length > 0){
            insights.push("✓ Hairpin-like motif detected");
            insights.push("✓ Hairpins are common RNA secondary structures");
        }

        if(seq.length > 50){
            insights.push("✓ Larger RNA sequences may form complex folds");
        }

        if(pairs.length === 0){
            insights.push("⚠ No major pairing interactions detected");
        }

        if(insights.length === 0){
            insights.push("✓ RNA structure appears balanced");
        }

    } else {

        // PROFESSIONAL MODE

        insights.push(`GC-richness: ${gc.toFixed(1)}%`);

        insights.push(`Predicted pair interactions: ${pairs.length}`);

        if(hairpins.length > 0){
            insights.push(`Hairpin motifs detected: ${hairpins.length}`);
        }

        if(seq.length > 50){
            insights.push("Long-sequence folding complexity increased");
        }

        if(pairs.length === 0){
            insights.push("Low interaction density detected");
        }

        insights.push("Structure prediction confidence: experimental");
    }

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