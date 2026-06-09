export function generateAIInsights(
    seq, 
    pairs, 
    hairpins, 
    gc,
    currentMode
){
    let insights = [];

    // =========================
    // EDUCATIONAL MODE
    // =========================
    if(currentMode === "educational"){

        if(gc > 60){

            insights.push(
                "✓ High GC regions often create more stable RNA folds"
            );

            insights.push(
                "✓ G-C interactions contain 3 hydrogen bonds"
            );

            insights.push(
                "✓ Blue arcs indicate strong G-C pair interactions"
            );
        }

        if(gc < 40){

            insights.push(
                "⚠ Low GC content may reduce structural stability"
            );
        }

        if(pairs.length >= 3){

            insights.push(
                "✓ Multiple long-range interactions detected"
            );

            insights.push(
                "✓ RNA may form stem-loop structures"
            );
        }

        if(hairpins.length > 0){

            insights.push(
                "✓ Hairpin motifs are visible in the secondary structure"
            );
        }

        if(pairs.length > 0){

            insights.push(
                "✓ Colored arcs in the secondary viewer represent RNA interactions"
            );
        }

        if(seq.length > 50){

            insights.push(
                "✓ Larger RNAs can fold into more complex topologies"
            );
        }

        if(pairs.length === 0){

            insights.push(
                "⚠ Few stabilizing interactions detected"
            );
        }
    }

    // =========================
    // PROFESSIONAL MODE
    // =========================
    else{

        insights.push(
            `GC-richness profile: ${gc.toFixed(1)}%`
        );

        insights.push(
            `Predicted interaction count: ${pairs.length}`
        );

        if(hairpins.length > 0){

            insights.push(
                `Stem-loop motifs detected: ${hairpins.length}`
            );
        }

        if(pairs.length > 5){

            insights.push(
                "High interaction density observed"
            );

            insights.push(
                "Predicted interaction topology visualized in secondary structure panel"
            );
        }

        if(seq.length > 75){

            insights.push(
                "Increased folding complexity predicted"
            );
        }

        if(gc > 65){

            insights.push(
                "Potentially stable GC-enriched topology"
            );
        }

        if(pairs.length === 0){

            insights.push(
                "Low structural interaction profile"
            );
        }
    }

    return insights;
}