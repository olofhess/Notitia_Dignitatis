//
// Living Notitia
// search.js
// Ranked Latin search with AND / OR plus contextual IN / NOT IN and parentheses
//

import * as XML from "./xml.js";

let searchIndex=[];

export function initialize(){
    buildIndex();
    console.log("SEARCH INDEX LATIN",searchIndex.length,"records");
    runConsoleTests();
    return Promise.resolve(searchIndex);
}

export function ready(){
    return Promise.resolve(searchIndex);
}

export function records(){
    return searchIndex;
}

export function search(queryOrOptions=""){
    const query=normalize(
        typeof queryOrOptions==="string"
            ? queryOrOptions
            : queryOrOptions?.text||""
    );

    if(!query){
        return [];
    }

    //
    // Advanced syntax is intentionally small. IN and NOT IN are uppercase
    // so the Latin preposition "in" remains searchable as ordinary text.
    // Parentheses may be used to group AND / OR expressions.
    //
    if(hasAdvancedSyntax(queryOrOptions)){
        const ast=parseAdvancedQuery(String(
            typeof queryOrOptions==="string"
                ? queryOrOptions
                : queryOrOptions?.text||""
        ));

        if(ast){
            return searchAst(ast);
        }
    }

    const booleanQuery=parseBooleanQuery(query);

    if(booleanQuery){
        const { left, operator, right }=booleanQuery;

        if(operator==="or"){
            return searchOr(left,right);
        }

        return searchAnd([left,right]);
    }

    //
    // Existing behaviour is preserved:
    // a plain multi-word query is still an implicit AND search.
    //
    const terms=query.split(" ").filter(Boolean);

    if(terms.length===1){
        return searchSingleTerm(terms[0]);
    }

    return searchAnd(terms);
}
function hasAdvancedSyntax(queryOrOptions){
    const raw=String(
        typeof queryOrOptions==="string"
            ? queryOrOptions
            : queryOrOptions?.text||""
    );

    return /[()]/.test(raw) || /\bIN\b/.test(raw) || /\bNOT\s+IN\b/.test(raw);
}

function tokenizeAdvancedQuery(raw){
    const source=String(raw||"");
    const tokens=[];
    let buffer="";
    let i=0;

    const flush=()=>{
        const value=clean(buffer);
        if(value){
            tokens.push({type:"term",value});
        }
        buffer="";
    };

    while(i<source.length){
        const ch=source[i];

        if(ch==="(" || ch===")"){
            flush();
            tokens.push({type:ch});
            i+=1;
            continue;
        }

        const rest=source.slice(i);
        const notIn=rest.match(/^NOT\s+IN\b/);
        if(notIn){
            flush();
            tokens.push({type:"not_in"});
            i+=notIn[0].length;
            continue;
        }

        const inOp=rest.match(/^IN\b/);
        if(inOp){
            flush();
            tokens.push({type:"in"});
            i+=inOp[0].length;
            continue;
        }

        const andOp=rest.match(/^(AND)\b/i);
        if(andOp && (andOp[0]===andOp[0].toUpperCase() || /\s/.test(source[i-1]||" "))){
            flush();
            tokens.push({type:"and"});
            i+=andOp[0].length;
            continue;
        }

        const orOp=rest.match(/^(OR)\b/i);
        if(orOp && (orOp[0]===orOp[0].toUpperCase() || /\s/.test(source[i-1]||" "))){
            flush();
            tokens.push({type:"or"});
            i+=orOp[0].length;
            continue;
        }

        buffer+=ch;
        i+=1;
    }

    flush();
    return tokens;
}

function parseAdvancedQuery(raw){
    const tokens=tokenizeAdvancedQuery(raw);
    let position=0;

    function peek(type){
        return tokens[position]?.type===type;
    }

    function take(type){
        if(!peek(type)){
            return null;
        }
        return tokens[position++];
    }

    function parsePrimary(){
        if(take("(")){
            const expression=parseOr();
            if(!take(")")){
                return null;
            }
            return expression;
        }

        const token=take("term");
        if(!token){
            return null;
        }

        return {type:"term",value:normalize(token.value)};
    }

    function parseIn(){
        let left=parsePrimary();
        if(!left){
            return null;
        }

        while(peek("in") || peek("not_in")){
            const operator=tokens[position++].type;
            const right=parsePrimary();
            if(!right){
                return null;
            }
            left={type:operator,left,right};
        }

        return left;
    }

    function parseAnd(){
        let left=parseIn();
        if(!left){
            return null;
        }

        while(take("and")){
            const right=parseIn();
            if(!right){
                return null;
            }
            left={type:"and",left,right};
        }

        return left;
    }

    function parseOr(){
        let left=parseAnd();
        if(!left){
            return null;
        }

        while(take("or")){
            const right=parseAnd();
            if(!right){
                return null;
            }
            left={type:"or",left,right};
        }

        return left;
    }

    const ast=parseOr();
    return ast && position===tokens.length ? ast : null;
}

function searchAst(ast){
    return searchIndex
        .map(record=>{
            const result=evaluateAst(record,ast,"all");
            if(!result?.matched){
                return null;
            }

            const matches=result.matches||[];
            const primaryMatch=matches
                .slice()
                .sort((a,b)=>(b.score||0)-(a.score||0))[0]||null;

            return {
                ...record,
                score:result.score||0,
                matchType:primaryMatch?.type||"",
                primaryMatch,
                matches,
                matchLanguages:["la"],
                matchFields:[...new Set(matches.map(match=>match.field).filter(Boolean))]
            };
        })
        .filter(Boolean)
        .sort((a,b)=>{
            if(b.score!==a.score){
                return b.score-a.score;
            }
            return lineNumber(a.line)-lineNumber(b.line);
        });
}

function evaluateAst(record,node,scope="all"){
    if(!node){
        return {matched:false,score:0,matches:[]};
    }

    if(node.type==="term"){
        const terms=node.value.split(" ").filter(Boolean);
        const ranked=rankRecordTermsScoped(record,terms,scope);
        return ranked
            ? {matched:true,score:ranked.score,matches:ranked.matches||[]}
            : {matched:false,score:0,matches:[]};
    }

    if(node.type==="and"){
        const left=evaluateAst(record,node.left,scope);
        if(!left.matched){
            return left;
        }
        const right=evaluateAst(record,node.right,scope);
        if(!right.matched){
            return right;
        }
        return {
            matched:true,
            score:left.score+right.score,
            matches:[...left.matches,...right.matches]
        };
    }

    if(node.type==="or"){
        const left=evaluateAst(record,node.left,scope);
        const right=evaluateAst(record,node.right,scope);
        if(!left.matched && !right.matched){
            return {matched:false,score:0,matches:[]};
        }
        if(left.matched && right.matched){
            return {
                matched:true,
                score:Math.max(left.score,right.score)+1000,
                matches:[...left.matches,...right.matches]
            };
        }
        return left.matched ? left : right;
    }

    if(node.type==="in"){
        const left=evaluateAst(record,node.left,"direct");
        if(!left.matched){
            return left;
        }
        const right=evaluateAst(record,node.right,"context");
        if(!right.matched){
            return right;
        }
        return {
            matched:true,
            score:left.score+right.score+5000,
            matches:[...left.matches,...right.matches]
        };
    }

    if(node.type==="not_in"){
        const left=evaluateAst(record,node.left,"direct");
        if(!left.matched){
            return left;
        }
        const right=evaluateAst(record,node.right,"context");
        if(right.matched){
            return {matched:false,score:0,matches:[]};
        }
        return left;
    }

    return {matched:false,score:0,matches:[]};
}

function parseBooleanQuery(query){
    const match=query.match(/^(.+?)\s+(and|or)\s+(.+)$/i);

    if(!match){
        return null;
    }

    const left=normalize(match[1]);
    const operator=normalize(match[2]);
    const right=normalize(match[3]);

    if(!left||!right){
        return null;
    }

    //
    // Deliberately support one Boolean operator only.
    // No parentheses, NOT, or chained Boolean expressions.
    //
    if(/\s+(and|or)\s+/i.test(left)||/\s+(and|or)\s+/i.test(right)){
        return null;
    }

    return { left, operator, right };
}

function searchAnd(terms){
    return searchIndex
        .map(record=>rankRecordTerms(record,terms))
        .filter(Boolean)
        .sort((a,b)=>{
            if(b.score!==a.score){
                return b.score-a.score;
            }
            return lineNumber(a.line)-lineNumber(b.line);
        });
}

function searchSingleTerm(term){
    const ranked=searchIndex
        .map(record=>rankRecordTerms(record,[term]))
        .filter(Boolean)
        .sort((a,b)=>{
            if(b.score!==a.score){
                return b.score-a.score;
            }
            return lineNumber(a.line)-lineNumber(b.line);
        });

    const strong=ranked.filter(record=>
        record.matchType==="exact" ||
        record.matchType==="whole"
    );

    return strong.length
        ? strong
        : ranked;
}

function searchOr(left,right){
    const combined=new Map();

    for(const term of [left,right]){
        for(const record of searchSingleTerm(term)){
            const key=record.node;

            if(!combined.has(key)){
                combined.set(key,{
                    ...record,
                    booleanOperator:"or",
                    booleanTerms:[term],
                    matchedBooleanTerms:1
                });
                continue;
            }

            const existing=combined.get(key);
            const terms=[...new Set([...existing.booleanTerms,term])];

            if(record.score>existing.score){
                combined.set(key,{
                    ...record,
                    booleanOperator:"or",
                    booleanTerms:terms,
                    matchedBooleanTerms:terms.length
                });
            }
            else{
                existing.booleanTerms=terms;
                existing.matchedBooleanTerms=terms.length;
            }
        }
    }

    return [...combined.values()]
        .sort((a,b)=>{
            if(b.matchedBooleanTerms!==a.matchedBooleanTerms){
                return b.matchedBooleanTerms-a.matchedBooleanTerms;
            }
            if(b.score!==a.score){
                return b.score-a.score;
            }
            return lineNumber(a.line)-lineNumber(b.line);
        });
}

// Temporary compatibility with the old search_ui.js.
// These can disappear when the new search UI is built.
export function placeSources(){
    return uniqueSorted(
        searchIndex
            .flatMap(record=>record.places.map(place=>place.source))
            .filter(Boolean)
    );
}

export function officeTypes(){
    return uniqueSorted(
        searchIndex
            .map(record=>record.officeType)
            .filter(Boolean)
    );
}

export function ownerOffices(){
    return uniqueSorted(
        searchIndex
            .map(record=>record.ownerOffice)
            .filter(Boolean)
    );
}

export function dimensions(){
    return uniqueSorted(
        searchIndex
            .filter(record=>record.unit)
            .map(record=>record.dimension)
            .filter(Boolean)
    );
}

function buildIndex(){
    searchIndex=[];
    XML.documents().forEach(document=>walk(document));
    console.log("SEARCH INDEX LATIN",searchIndex.length,"records");
}

function walk(node){
    searchIndex.push(createRecord(node));
    navigationChildren(node).forEach(child=>walk(child));
}

function navigationChildren(node){
    if(XML.attr(node,"line") && node.tagName!=="group"){
        return [];
    }
    return XML.children(node);
}

function createRecord(node){
    const documentNode=ancestorOrSelf(node,"document");
    const chapterNode=ancestorOrSelf(node,"chapter");
    const officiumNode=ancestorOfficium(node);
    const officeNode=directChild(node,"office");
    const unitNode=directChild(node,"unit");
    const places=directChildren(node,"place").map(place=>({
        name:clean(place.textContent),
        source:clean(place.getAttribute("source"))
    }));
    const latinTitle=directTitle(node);
    const latinOffice=clean(officeNode?.textContent);
    const latinUnit=clean(unitNode?.textContent);
    const latinText=primaryText(node);
    const latinContext=contextTitles(node);
    const structuralContext=contextStructure(node);
    const document=clean(documentNode?.getAttribute("id"));
    const chapter=directTitle(chapterNode);
    const ownerOffice=clean(officiumNode?.getAttribute("ownerOffice"));
    const officeType=clean(officeNode?.getAttribute("type"));
    const dimension=node.tagName;
    const latinSearchText=normalize([
        latinText,
        latinTitle,
        latinOffice,
        officeType,
        latinUnit,
        ownerOffice,
        ...places.map(place=>place.name),
        ...places.map(place=>place.source),
        chapter,
        ...latinContext,
        ...structuralContext,
        document
    ].filter(Boolean).join(" "));

    return {
        node,
        line:clean(node.getAttribute("line")),
        dimension,
        document,
        chapter,
        officeType,
        ownerOffice,
        places,
        latinText,
        latinTitle,
        latinOffice,
        office:latinOffice,
        latinUnit,
        unit:latinUnit,
        latinContext,
        structuralContext,
        context:latinContext,
        latinSearchText,
        searchText:latinSearchText
    };
}

function primaryText(node){
    if(!node){
        return "";
    }

    const title=directTitle(node);

    if(title){
        return title;
    }

    //
    // Never fall back to node.textContent here.
    // For container nodes that would pull in the complete descendant tree
    // and make a chapter/document match words that occur only far below it.
    //
    // Search only direct semantic children that represent this node itself.
    //
    const searchableTags=new Set([
        "office",
        "unit",
        "place",
        "province",
        "region",
        "function",
        "factory",
        "treasury"
    ]);

    const parts=Array.from(node.children)
        .filter(child=>searchableTags.has(child.tagName))
        .map(child=>clean(child.textContent))
        .filter(Boolean);

    if(parts.length){
        return clean(parts.join(" "));
    }

    //
    // Leaf nodes with no element children may legitimately carry their
    // own text directly.
    //
    if(node.children.length===0){
        return clean(node.textContent);
    }

    return "";
}


function rankRecordTerms(record,terms){
    return rankRecordTermsScoped(record,terms,"all");
}

function rankRecordTermsScoped(record,terms,scope="all"){
    const termMatches=[];

    for(const term of terms){
        const ranked=rankRecordScoped(record,term,scope);

        if(!ranked){
            return null;
        }

        termMatches.push({
            term,
            score:ranked.score,
            matchType:ranked.matchType,
            primaryMatch:ranked.primaryMatch,
            matches:ranked.matches
        });
    }

    //
    // Step 7 ranking for multi-word queries:
    //
    // 1. Prefer records where more search terms match a DIRECT field
    //    of the record itself (office, unit, title, place, text).
    //
    // 2. Then let the weakest individual term decide. This prevents
    //    one excellent hit from hiding the fact that another term is
    //    only a distant contextual match.
    //
    // 3. Finally use the sum of all term scores as a tie-breaker.
    //
    const directTermCount=termMatches.filter(match=>
        match.matches.some(fieldMatch=>fieldMatch.scope==="direct")
    ).length;

    const weakestScore=Math.min(...termMatches.map(match=>match.score));
    const totalScore=termMatches.reduce((sum,match)=>sum+match.score,0);

    const score=
        directTermCount*1000000000 +
        weakestScore*1000 +
        totalScore;

    const allMatches=termMatches.flatMap(match=>
        match.matches.map(fieldMatch=>({
            term:match.term,
            ...fieldMatch
        }))
    );

    const best=allMatches
        .slice()
        .sort((a,b)=>b.score-a.score)[0];

    return {
        ...record,
        score,
        matchType:best?.type||"",
        primaryMatch:best||null,
        matches:allMatches,
        termMatches,
        directTermCount,
        matchLanguages:["la"],
        matchFields:[...new Set(allMatches.map(match=>match.field))]
    };
}

function rankRecord(record,query){
    return rankRecordScoped(record,query,"all");
}

function rankRecordScoped(record,query,scope="all"){
    const candidates=[
        ["latinText",record.latinText,"la",140,"direct"],
        ["latinTitle",record.latinTitle,"la",130,"direct"],
        ["latinOffice",record.latinOffice,"la",120,"direct"],
        ["latinUnit",record.latinUnit,"la",120,"direct"],
        ["places",record.places.map(place=>place.name).join(" "),"la",110,"direct"],
        ["placeSources",record.places.map(place=>place.source).join(" "),"la",100,"direct"],
        ["chapter",record.chapter,"la",80,"context"],
        ["latinContext",record.latinContext.join(" "),"la",50,"context"],
        ["structuralContext",(record.structuralContext||[]).join(" "),"la",45,"context"],
        ["officeType",record.officeType,"la",35,"context"],
        ["ownerOffice",record.ownerOffice,"la",35,"context"],
        ["document",record.document,"la",20,"context"]
    ];

    const scopedCandidates=candidates.filter(candidate=>
        scope==="all" || candidate[4]===scope
    );

    const matches=[];
    for(const [field,value,language,fieldWeight,fieldScope] of scopedCandidates){
        const match=scoreValue(value,query,fieldWeight,fieldScope);
        if(match){
            matches.push({
                field,
                language,
                scope:fieldScope,
                ...match
            });
        }
    }

    if(!matches.length){
        return null;
    }

    matches.sort((a,b)=>b.score-a.score);
    const best=matches[0];
    return {
        ...record,
        score:best.score,
        matchType:best.type,
        primaryMatch:best,
        matches,
        matchLanguages:["la"],
        matchFields:[...new Set(matches.map(match=>match.field))]
    };
}

function scoreValue(value,query,fieldWeight,scope){
    const text=normalize(value);
    if(!text){
        return null;
    }

    const contextPenalty=scope==="context" ? 120 : 0;

    if(text===query){
        return {
            type:"exact",
            score:1000+fieldWeight-contextPenalty
        };
    }

    if(hasWholePhrase(text,query)){
        return {
            type:"whole",
            score:750+fieldWeight-contextPenalty
        };
    }

    if(hasWordPrefix(text,query)){
        return {
            type:"prefix",
            score:550+fieldWeight-contextPenalty
        };
    }

    if(text.includes(query)){
        return {
            type:"substring",
            score:350+fieldWeight-contextPenalty
        };
    }

    return null;
}

function hasWholePhrase(text,query){
    const pattern=new RegExp("(^|[^a-z0-9])"+escapeRegex(query)+"($|[^a-z0-9])","i");
    return pattern.test(text);
}

function hasWordPrefix(text,query){
    const pattern=new RegExp("(^|[^a-z0-9])"+escapeRegex(query),"i");
    return pattern.test(text);
}

function escapeRegex(value){
    return value.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");
}

function lineNumber(value){
    const number=Number.parseInt(value,10);
    return Number.isFinite(number) ? number : Number.MAX_SAFE_INTEGER;
}

function runConsoleTests(){
    const tests=[
        "scutaria",
        "equites",
        "bafii balearum",
        "procurator dalmatia",
        "dalmatia procurator",
        "procurator balearum",
        "Princeps IN Dux",
        "A libellis IN (Dux AND Oriens)",
        "Subadiuva NOT IN Oriens",
        "(Dux OR Comes) IN Africa"
    ];

    tests.forEach(query=>{
        const results=search(query);
        console.log(
            "RANKED SEARCH TEST",
            JSON.stringify(query),
            results.length,
            "hits",
            results.slice(0,8).map(record=>({
                score:record.score,
                matchType:record.matchType,
                field:record.primaryMatch?.field,
                line:record.line,
                latin:record.latinText
            }))
        );
    });
}

function directChild(node,name){
    if(!node){
        return null;
    }
    return Array.from(node.children).find(child=>child.tagName===name)||null;
}

function directChildren(node,name){
    if(!node){
        return [];
    }
    return Array.from(node.children).filter(child=>child.tagName===name);
}

function directTitle(node){
    return clean(directChild(node,"title")?.textContent);
}

function ancestorOrSelf(node,name){
    let current=node;
    while(current){
        if(current.tagName===name){
            return current;
        }
        current=current.parentElement;
    }
    return null;
}

function ancestorOfficium(node){
    let current=node;
    while(current){
        if(current.tagName==="group" && current.getAttribute("type")==="officium"){
            return current;
        }
        if(current.tagName==="document"){
            break;
        }
        current=current.parentElement;
    }
    return null;
}

function contextTitles(node){
    if(!node){
        return [];
    }
    const result=[];
    let current=node.parentElement;
    while(current){
        if(current.tagName==="group"){
            const title=directTitle(current);
            if(title){
                result.unshift(title);
            }
        }
        if(current.tagName==="document"){
            break;
        }
        current=current.parentElement;
    }
    return result;
}

function contextStructure(node){
    if(!node){
        return [];
    }

    const result=[];
    let current=node;

    while(current){
        const tag=clean(current.tagName);
        const type=clean(current.getAttribute?.("type"));
        const owner=clean(current.getAttribute?.("ownerOffice"));

        if(tag){
            result.push(tag);
        }
        if(type){
            result.push(type);
        }
        if(owner){
            result.push(owner);
        }

        if(current.tagName==="document"){
            break;
        }
        current=current.parentElement;
    }

    return uniqueSorted(result);
}

function uniqueSorted(values){
    return [...new Set(values)].sort((a,b)=>a.localeCompare(b,undefined,{sensitivity:"base"}));
}

function clean(value){
    return String(value||"").replace(/\s+/g," ").trim();
}

function normalize(value){
    return clean(value)
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g,"")
        .toLowerCase();
}
