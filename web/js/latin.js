//
// Living Notitia
// latin.js
// Small Latin normalizer for resolving administrative expressions.
// This is deliberately Notitia-specific, not a general Latin parser.
//
export function cleanLatinText(value){
    return String(value||"")
        .replace(/\s+/g," ")
        .trim();
}
export function latinKey(value){
    let text=cleanLatinText(value)
        .toLowerCase()
        .replace(/\bin\s+praesenti\b/g,"praesentalis")
        .replace(/[^a-z]+/g," ")
        .trim();
    if(!text){
        return [];
    }
    const stopWords=new Set([
        "insignia",
        "viri",
        "vir",
        "illustris",
        "spectabilis",
        "clarissimi",
        "perfectissimi",
        "sub",
        "dispositione",
        "iurisdictione",
        "per",
        "in",
        "de",
        "ex",
        "et",
        "sunt",
        "autem",
        "officium",
        "suprascripti",
        "suprascriptae",
        "habet",
        "habent",
        "ad",
        "item",
        "dioceses",
        "dioceseos",
        "provinciae",
        "provincia",
        "infrascriptae",
        "infrascriptas",
        "rerum"
    ]);
    return text
        .split(/\s+/)
        .filter(Boolean)
        .filter(token=>!stopWords.has(token))
        .map(latinStem);
}
export function latinStem(token){
    const exact={
        praefectus:"praefect",
        praefecti:"praefect",
        praefecto:"praefect",
        praefectum:"praefect",
        magistri:"magistr",
        magister:"magistr",
        magistrum:"magistr",
        magisteriae:"magistr",
        comes:"com",
        comitis:"com",
        comite:"com",
        comitem:"com",
        quaestor:"quaest",
        quaestoris:"quaest",
        proconsul:"procons",
        proconsulis:"procons",
        vicarius:"vicar",
        vicarii:"vicar",
        vicario:"vicar",
        dux:"duc",
        ducis:"duc",
        primicerius:"primicer",
        primicerii:"primicer",
        praepositus:"praeposit",
        praepositi:"praeposit",
        consularis:"consular",
        consulares:"consular",
        corrector:"correct",
        correctores:"correct",
        praeses:"praesid",
        praesidis:"praesid",
        praesides:"praesid",
        praesenti:"praesent",
        praesentalis:"praesent",
        praesentalem:"praesent",
        praesentales:"praesent",
        praesentali:"praesent",
        praesentis:"praesent",
        mauretaniae:"mauritan",
        mauretania:"mauritan",
        mauritaniae:"mauritan",
        mauritania:"mauritan"
    };
    if(exact[token]){
        return exact[token];
    }
    const endings=[
        "arum","orum","ibus","ium",
        "iae","iam","ias",
        "ae","am","as",
        "is","um","us","i","o","a","e"
    ];
    for(const ending of endings){
        if(
            token.length-ending.length>=4 &&
            token.endsWith(ending)
        ){
            return token.slice(
                0,
                token.length-ending.length
            );
        }
    }
    return token;
}
export function keyContains(targetKey,sourceKey){
    return sourceKey.every(token=>targetKey.includes(token));
}
