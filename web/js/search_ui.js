// Step 9: elegant search UI with visible context evidence
//
// Living Notitia
// search_ui.js
// Step 3: simple bilingual ranked search interface
//

import * as Search from "./search.js";
import * as Nav from "./nav.js";
import MapView from "./map.js";

let searchBox=null;
let status=null;
let resultsPanel=null;
let searchTimer=null;

export function initialize(){

    searchBox=document.getElementById("searchBox");
    status=document.getElementById("status");

    if(!searchBox){
        return;
    }

    prepareSearchBox();
    simplifyToolbar();
    createResultsPanel();

    searchBox.addEventListener("input",scheduleSearch);

    searchBox.addEventListener("keydown",event=>{

        if(event.key==="Escape"){

            searchBox.value="";
            clearResults();
            MapView.clearSearchResults();

            if(status){
                status.textContent="Ready";
            }

            searchBox.blur();

        }

    });

    document.addEventListener("keydown",event=>{

        if(
            event.key==="/" &&
            document.activeElement!==searchBox
        ){

            event.preventDefault();
            searchBox.focus();

        }

    });

}

function prepareSearchBox(){

    searchBox.setAttribute(
        "placeholder",
        "Search Latin or English"
    );

    searchBox.setAttribute(
        "autocomplete",
        "off"
    );

    searchBox.setAttribute(
        "spellcheck",
        "false"
    );

    searchBox.setAttribute(
        "aria-label",
        "Search Living Notitia in Latin or English"
    );

    Object.assign(searchBox.style,{
        width:"390px",
        height:"42px",
        boxSizing:"border-box",
        padding:"0 42px 0 38px",
        fontSize:"18px",
        lineHeight:"42px",
        borderRadius:"21px",
        border:"1px solid rgba(0,0,0,0.18)",
        background:"#fff",
        boxShadow:"0 1px 4px rgba(0,0,0,0.08)"
    });

}

function simplifyToolbar(){

    const toolbar=document.getElementById("toolbar");

    if(!toolbar){
        return;
    }

    Array.from(toolbar.querySelectorAll("select"))
        .forEach(select=>select.remove());

}

function createResultsPanel(){

    const header=document.getElementById("header");

    if(!header){
        return;
    }

    const old=document.getElementById("searchResults");

    if(old){
        old.remove();
    }

    resultsPanel=document.createElement("div");
    resultsPanel.id="searchResults";

    Object.assign(resultsPanel.style,{
        display:"none",
        position:"fixed",
        left:"0",
        right:"auto",
        zIndex:"2000",
        boxSizing:"border-box",
        overflowY:"auto",
        padding:"8px",
        background:"rgba(255,255,255,0.98)",
        borderTop:"1px solid rgba(0,0,0,0.08)",
        boxShadow:"0 8px 24px rgba(0,0,0,0.12)",
        backdropFilter:"blur(14px)",
        WebkitBackdropFilter:"blur(14px)"
    });

    header.insertAdjacentElement(
        "afterend",
        resultsPanel
    );

    positionResultsPanel();

    window.addEventListener(
        "resize",
        positionResultsPanel
    );

}

function positionResultsPanel(){

    if(!resultsPanel){
        return;
    }

    const header=document.getElementById("header");
    const mapElement=document.getElementById("map");

    if(!header){
        return;
    }

    const headerRect=header.getBoundingClientRect();
    const top=Math.max(0,headerRect.bottom);

    let width=360;

    if(mapElement){

        const mapRect=mapElement.getBoundingClientRect();

        if(mapRect.left>0){
            width=mapRect.left;
        }

    }

    let bottom=window.innerHeight;

    if(status){

        const statusRect=status.getBoundingClientRect();

        if(
            statusRect.top>top &&
            statusRect.top<bottom
        ){
            bottom=statusRect.top;
        }

    }

    resultsPanel.style.top=top+"px";
    resultsPanel.style.width=Math.max(220,width)+"px";
    resultsPanel.style.maxHeight=Math.max(120,bottom-top)+"px";

}

function scheduleSearch(){

    window.clearTimeout(searchTimer);

    searchTimer=window.setTimeout(
        runSearch,
        70
    );

}

async function runSearch(){

    const text=searchBox.value.trim();

    if(!text){

        clearResults();
        MapView.clearSearchResults();

        if(status){
            status.textContent="Ready";
        }

        return;
    }

    await Search.ready();

    if(text!==searchBox.value.trim()){
        return;
    }

    MapView.clearSelection(false);

    const results=Search.search(text);

    showResults(results,text);
    showResultsOnMap(results);

    if(status){

        status.textContent=
            results.length+
            (
                results.length===1
                    ? " search result"
                    : " search results"
            );

    }

}

function showResultsOnMap(results){

    const places=[];

    results.forEach(record=>{

        (record.places||[]).forEach(place=>{

            if(
                place &&
                Number.isFinite(Number(place.latitude)) &&
                Number.isFinite(Number(place.longitude))
            ){

                places.push(place);
                return;

            }

            const name=
                place?.placeName ||
                place?.sourcePlaceName ||
                place?.name;

            if(name){
                places.push(name);
            }

        });

    });

    MapView.beginSearchMode();
    MapView.showSearchResults(places);

}

function showResults(results,query){

    if(!resultsPanel){
        return;
    }

    resultsPanel.innerHTML="";

    const summary=document.createElement("div");

    Object.assign(summary.style,{
        display:"flex",
        justifyContent:"space-between",
        alignItems:"baseline",
        gap:"8px",
        padding:"4px 7px 8px 7px",
        color:"#666",
        font:"500 12px -apple-system, BlinkMacSystemFont, \"SF Pro Text\", sans-serif"
    });

    summary.textContent=
        results.length+
        (
            results.length===1
                ? " result"
                : " results"
        );

    resultsPanel.appendChild(summary);

    if(!results.length){

        const empty=document.createElement("div");

        Object.assign(empty.style,{
            padding:"18px 10px",
            color:"#777",
            font:"14px -apple-system, BlinkMacSystemFont, \"SF Pro Text\", sans-serif"
        });

        empty.textContent="No results";
        resultsPanel.appendChild(empty);

        positionResultsPanel();
        resultsPanel.style.display="block";

        return;

    }

    const maxResults=50;

    results
        .slice(0,maxResults)
        .forEach(record=>{
            resultsPanel.appendChild(
                createResultRow(record,query)
            );
        });

    if(results.length>maxResults){

        const more=document.createElement("div");

        Object.assign(more.style,{
            padding:"10px 8px",
            color:"#777",
            font:"12px -apple-system, BlinkMacSystemFont, \"SF Pro Text\", sans-serif"
        });

        more.textContent=
            "Showing first "+
            maxResults+
            " of "+
            results.length;

        resultsPanel.appendChild(more);

    }

    positionResultsPanel();
    resultsPanel.style.display="block";

}

function createResultRow(record,query){

    const row=document.createElement("div");
    row.className="searchResult";
    row.title="Open in Living Notitia";

    Object.assign(row.style,{
        padding:"9px 10px",
        margin:"0 0 3px 0",
        borderRadius:"9px",
        cursor:"pointer",
        fontFamily:"-apple-system, BlinkMacSystemFont, \"SF Pro Text\", sans-serif"
    });

    row.addEventListener("mouseenter",()=>{
        row.style.background="rgba(0,0,0,0.055)";
    });

    row.addEventListener("mouseleave",()=>{
        row.style.background="";
    });

    row.addEventListener("click",()=>{

        if(Nav.selectNode(record.node)){

            clearResults();
            searchBox.blur();

        }

    });

    const preferredLanguage=
        record.primaryMatch?.language==="en"
            ? "en"
            : "la";

    const primaryText=
        preferredLanguage==="en"
            ? bestEnglishText(record)
            : bestLatinText(record);

    const secondaryText=
        preferredLanguage==="en"
            ? bestLatinText(record)
            : bestEnglishText(record);

    const main=document.createElement("div");

    Object.assign(main.style,{
        fontSize:"14px",
        fontWeight:"600",
        lineHeight:"1.25",
        color:"#1d1d1f"
    });

    appendHighlightedText(
        main,
        primaryText||fallbackTitle(record),
        query
    );

    row.appendChild(main);

    if(
        secondaryText &&
        normalizeDisplay(secondaryText)!==normalizeDisplay(primaryText)
    ){

        const translation=document.createElement("div");

        Object.assign(translation.style,{
            marginTop:"2px",
            fontSize:"12px",
            lineHeight:"1.25",
            color:"#6e6e73"
        });

        appendHighlightedText(
            translation,
            secondaryText,
            query
        );
        row.appendChild(translation);

    }

    const detail=document.createElement("div");

    Object.assign(detail.style,{
        marginTop:"5px",
        fontSize:"11px",
        lineHeight:"1.3",
        color:"#8a8a8f"
    });

    const detailText=resultDetail(record);

    if(detailText){
        appendHighlightedText(
            detail,
            detailText,
            query
        );
        row.appendChild(detail);
    }

    const contextText=contextEvidence(
        record,
        query,
        primaryText,
        secondaryText,
        detailText
    );

    if(contextText){

        const context=document.createElement("div");

        Object.assign(context.style,{
            marginTop:"4px",
            fontSize:"11px",
            lineHeight:"1.3",
            color:"#6e6e73",
            fontStyle:"italic"
        });

        appendHighlightedText(
            context,
            "Context: "+contextText,
            query
        );

        row.appendChild(context);

    }

    return row;

}

function bestLatinText(record){

    return (
        record.latinUnit ||
        record.latinText ||
        record.latinTitle ||
        record.latinOffice ||
        ""
    );

}

function bestEnglishText(record){

    return (
        record.englishUnit ||
        record.englishText ||
        record.englishTitle ||
        record.englishOffice ||
        ""
    );

}

function fallbackTitle(record){

    return (
        record.dimension ||
        record.document ||
        "Notitia entry"
    );

}

function resultDetail(record){

    const parts=[];

    const places=(record.places||[])
        .map(place=>place.name)
        .filter(Boolean);

    if(places.length){
        parts.push([...new Set(places)].join(", "));
    }

    const chapter=
        record.primaryMatch?.language==="en"
            ? record.englishChapter||record.chapter
            : record.chapter||record.englishChapter;

    if(chapter){
        parts.push(chapter);
    }

    if(record.line){
        parts.push("line "+record.line);
    }

    return parts.join(" · ");

}

function contextEvidence(
    record,
    query,
    primaryText,
    secondaryText,
    detailText
){

    const terms=String(query||"")
        .trim()
        .split(/\s+/)
        .map(term=>normalizeDisplay(term))
        .filter(Boolean);

    if(!terms.length){
        return "";
    }

    const alreadyVisible=normalizeDisplay([
        primaryText,
        secondaryText,
        detailText
    ].filter(Boolean).join(" "));

    const hiddenTerms=terms.filter(term=>
        !matchesSearchTerm(alreadyVisible,term)
    );

    if(!hiddenTerms.length){
        return "";
    }

    //
    // Search from the nearest semantic context outward.
    // Individual context items are used rather than the complete
    // joined context path, so the explanation stays short.
    //
    const candidates=[
        ...(record.latinContext||[]),
        ...(record.englishContext||[]),
        record.chapter,
        record.englishChapter,
        record.ownerOffice,
        record.officeType,
        record.document
    ]
        .map(value=>String(value||"").trim())
        .filter(Boolean);

    const evidence=[];

    hiddenTerms.forEach(term=>{

        const matches=candidates
            .filter(value=>
                matchesSearchTerm(
                    normalizeDisplay(value),
                    term
                )
            )
            .sort((a,b)=>a.length-b.length);

        if(matches.length){
            evidence.push(matches[0]);
        }

    });

    return [...new Set(evidence)].join(" · ");

}

function matchesSearchTerm(text,term){

    if(!text || !term){
        return false;
    }

    if(text.includes(term)){
        return true;
    }

    const words=text.split(/[^a-z0-9]+/).filter(Boolean);

    return words.some(word=>word.startsWith(term));

}

function appendHighlightedText(element,text,query){

    const source=String(text||"");
    const terms=String(query||"")
        .trim()
        .split(/\s+/)
        .map(term=>term.trim())
        .filter(Boolean);

    if(!terms.length){
        element.textContent=source;
        return;
    }

    //
    // Step 8:
    // Highlight every search term independently.
    //
    // This matters for AND searches such as
    // "procurator dalmatia", where the two terms may appear
    // in different parts of the same result.
    //
    const escaped=terms
        .sort((a,b)=>b.length-a.length)
        .map(term=>term.replace(/[.*+?^${}()|[\]\\]/g,"\\$&"));

    const pattern=new RegExp(
        "(" + escaped.join("|") + ")",
        "gi"
    );

    const pieces=source.split(pattern);

    pieces.forEach(piece=>{

        if(!piece){
            return;
        }

        const isMatch=terms.some(term=>
            normalizeDisplay(piece).startsWith(
                normalizeDisplay(term)
            )
        );

        if(isMatch){

            const mark=document.createElement("mark");

            mark.textContent=piece;

            Object.assign(mark.style,{
                background:"#fff3b0",
                color:"inherit",
                padding:"0 1px",
                borderRadius:"2px"
            });

            element.appendChild(mark);

        }else{

            element.appendChild(
                document.createTextNode(piece)
            );

        }

    });

}
function normalizeDisplay(value){

    return String(value||"")
        .replace(/\s+/g," ")
        .trim()
        .toLocaleLowerCase();

}

function clearResults(){

    if(!resultsPanel){
        return;
    }

    resultsPanel.innerHTML="";
    resultsPanel.style.display="none";

}
