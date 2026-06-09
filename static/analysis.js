export function gcContent(seq){
    let gc = 0;
    for(let s of seq){
        if(s === "G" || s === "C") gc++;
    }
    return ((gc / seq.length) * 100).toFixed(1);
}

export function structureScore(coords){
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

export function getPairs(seq, coords){
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

export function predictSecondaryStructure(seq){

    console.log("LOCAL PREDICTOR USED");

    let structure =
        Array(seq.length).fill(".");

    let pairs = [];

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

    let used = new Set();

    // =========================
    // STEM SEARCH
    // =========================

    for(let i=0;i<seq.length;i++){

        if(used.has(i)) continue;

        for(let j=seq.length-1;j>i+3;j--){

            if(used.has(j)) continue;

            // probeer stem te bouwen
            let stem = [];

            let left = i;
            let right = j;

            while(

                left < right &&
                canPair(seq[left], seq[right])

            ){

                stem.push([left,right]);

                left++;
                right--;
            }

            // minimale stemlengte
            if(stem.length >= 2){

                stem.forEach(p => {

                    let a = p[0];
                    let b = p[1];

                    structure[a] = "(";
                    structure[b] = ")";

                    pairs.push([a,b]);

                    used.add(a);
                    used.add(b);
                });

                break;
            }
        }
    }

    return {

        dotBracket:
            structure.join(""),

        pairs
    };
}

export function detectHairpins(stems){

    console.log("STEMS:", stems);

    let hairpins = [];

    stems.forEach(stem => {

        if(stem.length < 2)
            return;

        let innerPair =
            stem[stem.length - 1];

        let loopSize =
            innerPair[1] -
            innerPair[0] - 1;

        
        console.log(
            "LOOP SIZE:",
            loopSize
        );

        if(loopSize >= 3){

            hairpins.push({
                start: innerPair[0],
                end: innerPair[1],
                loopSize,
                stemLength: stem.length
            });
        }
    });

    console.log("HAIRPINS:", hairpins);

    return hairpins;
}

export function toDotBracket(seq, pairs){
    let structure = Array(seq.length).fill(".");

    pairs.forEach(p => {
        structure[p[0]] = "(";
        structure[p[1]] = ")";
    });

    return structure.join("");
}

export function dotBracketToPairs(dot){

    let stack = [];

    let pairs = [];

    for(let i=0;i<dot.length;i++){

        if(dot[i] === "("){

            stack.push(i);

        } else if(dot[i] === ")"){

            let start = stack.pop();

            if(start !== undefined){

                pairs.push([start,i]);
            }
        }
    }

    return pairs;
}

export function detectStems(pairs){

    if(!pairs.length) return [];

    // sorteer
    pairs.sort((a,b)=>a[0]-b[0]);

    let stems = [];

    let current = [pairs[0]];

    for(let i=1;i<pairs.length;i++){

        let prev = pairs[i-1];
        let curr = pairs[i];

        // consecutive stem?
        if(
            curr[0] === prev[0] + 1 &&
            curr[1] === prev[1] - 1
        ){

            current.push(curr);

        } else {

            stems.push(current);

            current = [curr];
        }
    }

    stems.push(current);

    return stems;
}

export function classifyStructure(
    pairs,
    stems,
    hairpins
){

    if(pairs.length === 0)
        return "Unstructured RNA";

    let longestStem =
        stems.length
        ? Math.max(...stems.map(s => s.length))
        : 0;

    if(
        stems.length === 1 &&
        hairpins.length === 1
    ){
        return "Hairpin Structure";
    }

    if(
        longestStem >= 5 &&
        hairpins.length >= 2
    ){
        return "Complex Folded RNA";
    }

    if(
        hairpins.length >= 1
    ){
        return "Multi-Hairpin Structure";
    }

    return "Folded RNA";
}

export function buildHairpinLayout(seq, pairs){

    let stems = detectStems([...pairs]);

    if(stems.length !== 1){
        return null;
    }

    let stem = stems[0];

    let points =
        Array(seq.length)
        .fill(null);

    let stemSpacing = 40;
    let stemWidth = 120;

    // =========================
    // STEM
    // =========================

    stem.forEach((pair,index)=>{

        let left = pair[0];
        let right = pair[1];

        let y = index * stemSpacing;

        points[left] = {
            x:-stemWidth/2,
            y:y
        };

        points[right] = {
            x: stemWidth/2,
            y:y
        };
    });

    // =========================
    // LOOP
    // =========================

    let loopStart =
        stem[stem.length-1][0] + 1;

    let loopEnd =
        stem[stem.length-1][1] - 1;

    let loopBases =
        loopEnd - loopStart + 1;

    if(loopBases > 0){

        let radius = 60;

        for(let i=0;i<loopBases;i++){

            let t =
                loopBases === 1
                ? 0.5
                : i/(loopBases-1);

            let angle =
                Math.PI -
                (Math.PI * t);

            points[loopStart+i] = {

                x:
                    Math.cos(angle)
                    * radius,

                y:
                    stem.length
                    * stemSpacing +

                    Math.sin(angle)
                    * radius
            };
        }
    }

    return points;
}