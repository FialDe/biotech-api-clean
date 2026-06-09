export function drawPredictView(
    seq,
    coords,
    pairs,
    hairpins,
    currentMode
){

// document.getElementById("downloadBtn").style.display = "block";

    // let viewerDiv = document.getElementById("viewer");
    // viewerDiv.innerHTML = "";

    // let viewer = $3Dmol.createViewer(viewerDiv, {
    //     backgroundColor: "#020617"
    // });
    
    // viewerDiv.classList.remove("show");

    // setTimeout(() => {
    //     viewerDiv.classList.add("show");
    // }, 50);

    // viewer.addCurve({
    //     points: coords.map(c => ({x:c[0], y:c[1], z:c[2]})),
    //     radius: 0.25,
    //     color: "#94a3b8"
    // });

    // let colors = {
    //     "A": "#4ade80",
    //     "U": "#f87171",
    //     "G": "#fb923c",
    //     "C": "#60a5fa"
    // };

    // coords.forEach((c,i)=>{

    //     // sphere
    //     viewer.addSphere({
    //         center: {x:c[0], y:c[1], z:c[2]},
    //         radius: 0.6,
    //         color: colors[seq[i]]
    //     });

    //     // permanent nucleotide label
    //     viewer.addLabel(
    //         `${seq[i]}${i+1}`,
    //         {
    //             position: {
    //                 x:c[0],
    //                 y:c[1],
    //                 z:c[2]
    //             },

    //             backgroundColor: "rgba(2,6,23,0.65)",
    //             backgroundOpacity: 0.8,
    //             fontColor: "#38bdf8",
    //             fontSize: 12,
    //             inFront: true
    //         }
    //     );

    //     // hover sphere
    //     viewer.addSphere({

    //         center: {
    //             x:c[0],
    //             y:c[1],
    //             z:c[2]
    //         },

    //         radius: 0.9,
    //         color: colors[seq[i]],
    //         opacity: 0.0,
    //         hoverable: true,
            
    //         hover_callback: function(){    
                
    //             viewerDiv.style.cursor = "pointer";

    //             this.opacity = 0.45;
    //             viewer.render();        

    //             if(this.label) return;
    //             this.label = viewer.addLabel(

    //                 `${seq[i]}${i+1}

    // X: ${c[0].toFixed(2)}
    // Y: ${c[1].toFixed(2)}
    // Z: ${c[2].toFixed(2)}`,

    //                 {
    //                     position: {
    //                         x:c[0],
    //                         y:c[1],
    //                         z:c[2]
    //                     },

    //                     backgroundColor: "rgba(2,6,23,0.92)",
    //                     fontColor: "#e2e8f0",
    //                     fontSize: 12,
    //                     padding: 6,
    //                     borderThickness: 1,
    //                     borderColor: "#334155",
    //                     inFront: true
    //                 }
    //             );

    //             viewer.render();
    //         },

    //         unhover_callback: function(){

    //             viewerDiv.style.cursor = "default";                
    //             this.opacity = 0.0;
    //             viewer.render();

    //             if(this.label){

    //                 viewer.removeLabel(this.label);
    //                 this.label = null;
    //                 viewer.render();
    //             }
    //         }
    //     });
    // });
    
    // pairs.forEach(p => {

    //     let i = p[0];
    //     let j = p[1];

    //     let cylinderConfig = {

    //         start: {
    //             x:coords[i][0],
    //             y:coords[i][1],
    //             z:coords[i][2]
    //         },

    //         end: {
    //             x:coords[j][0],
    //             y:coords[j][1],
    //             z:coords[j][2]
    //         },

    //         radius: 0.15,
    //         color: "#22c55e",
    //         dashed: true
    //     };

    //     // =========================
    //     // EDUCATIONAL MODE
    //     // =========================
    //     if(currentMode === "educational"){

    //         let base1 = seq[i];
    //         let base2 = seq[j];

    //         let pairType = "";
    //         let pairInfo = "";

    //         if(
    //             (base1 === "G" && base2 === "C") ||
    //             (base1 === "C" && base2 === "G")
    //         ){

    //             pairType = "G-C Pair";
    //             pairInfo = `
    // Strong canonical interaction

    // 3 hydrogen bonds

    // High structural stability
    // `;

    //         } else if(
    //             (base1 === "A" && base2 === "U") ||
    //             (base1 === "U" && base2 === "A")
    //         ){

    //             pairType = "A-U Pair";
    //             pairInfo = `
    // Canonical interaction

    // 2 hydrogen bonds
    // `;

    //         } else {

    //             pairType = "G-U Wobble Pair";
    //             pairInfo = `
    // Non-canonical interaction

    // Common in RNA folding
    // `;
    //         }

    //         cylinderConfig.hoverable = true;

    //         cylinderConfig.hover_callback = function(){

    //             if(this.label) return;
    //             this.label = viewer.addLabel(

    // `${pairType}
    // ${pairInfo}`,

    //                 {

    //                     position: {

    //                         x:(coords[i][0] + coords[j][0]) / 2,
    //                         y:(coords[i][1] + coords[j][1]) / 2,
    //                         z:(coords[i][2] + coords[j][2]) / 2
    //                     },

    //                     backgroundColor: "rgba(2,6,23,0.95)",
    //                     fontColor: "#e2e8f0",
    //                     fontSize: 12,
    //                     padding: 6,
    //                     borderThickness: 1,
    //                     borderColor: "#334155",
    //                     inFront: true
    //                 }
    //             );

    //             viewer.render();
    //         };

    //         cylinderConfig.unhover_callback = function(){

    //             if(this.label){

    //                 viewer.removeLabel(this.label);
    //                 this.label = null;
    //                 viewer.render();
    //             }
    //         };
    //     }

    //     viewer.addCylinder(cylinderConfig);
    // });

    // hairpins.forEach(h => {
    //     viewer.addCylinder({
    //         start: {x:coords[h.start][0], y:coords[h.start][1], z:coords[h.start][2]},
    //         end: {x:coords[h.end][0], y:coords[h.end][1], z:coords[h.end][2]},
    //         radius: 0.25,
    //         color: "#facc15" // geel = hairpin
    //     });
    // });

    // viewer.zoomTo();
    // viewer.render();