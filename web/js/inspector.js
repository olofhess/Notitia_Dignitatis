//
// Living Notitia
// inspector.js
//
import Data from "./data.js";
import * as Map from "./map.js";

let panel=null;
let currentNode=null;
let currentPlaceName=null;
let currentPlaceContext=null;
let currentPlaceMention=null;
let language="la";
let englishDocument=null;
let englishRender=null;
let englishLoadStarted=false;

export function initialize(){

    panel=document.getElementById("inspector");

    loadEnglish();

}

export function show(node){

    if(!panel){

        initialize();

    }

    if(!panel||!node){

        return;

    }

    currentNode=node;
    currentPlaceName=null;
    currentPlaceContext=null;
    currentPlaceMention=null;

    if(node.getAttribute("line")){

        const multiMentionPlace=multiMentionPlaceForNode(node);

        if(multiMentionPlace){

            showPlaceMentions(multiMentionPlace,node);

            return;

        }

    }

    panel.innerHTML="";

    heading(displayNodeLabel(node));

    if(isContainer(node)){

        showContainer(node);

        return;

    }

    if(node.getAttribute("line")){

        showLine(node);

        return;

    }

    showContainer(node);

}

async function loadEnglish(){

    if(englishLoadStarted){

        return;

    }

    englishLoadStarted=true;

    try{

        const [xmlResponse,renderResponse]=await Promise.all([
            fetch("../data/notitia.en.xml"),
            fetch("../data/english_render.json")
        ]);

        if(!xmlResponse.ok){

            throw new Error(`notitia.en.xml HTTP ${xmlResponse.status}`);

        }

        const xmlText=await xmlResponse.text();

        englishDocument=new DOMParser().parseFromString(xmlText,"application/xml");

        const parserError=englishDocument.querySelector("parsererror");

        if(parserError){

            throw new Error("notitia.en.xml could not be parsed");

        }

        if(renderResponse.ok){

            englishRender=await renderResponse.json();

        }
        else{

            console.warn(
                `english_render.json HTTP ${renderResponse.status}; using notitia.en.xml only`
            );

            englishRender=null;

        }

    }
    catch(error){

        console.warn("English translation data could not be loaded:",error);

        englishDocument=null;
        englishRender=null;

    }

}

function parallelNode(node){

    if(language!=="en"||!englishDocument||!node){

        return node;

    }

    const documentNode=ancestor(node,"document");

    if(!documentNode){

        return node;

    }

    const documentId=documentNode.getAttribute("id");

    const englishDocuments=Array.from(
        englishDocument.getElementsByTagName("document")
    );

    const englishDocumentNode=englishDocuments.find(
        item=>item.getAttribute("id")===documentId
    );

    if(!englishDocumentNode){

        return node;

    }

    if(node===documentNode){

        return englishDocumentNode;

    }

    const path=[];

    let current=node;

    while(current&&current!==documentNode){

        const parent=current.parentElement;

        if(!parent){

            break;

        }

        const index=Array.from(parent.children).indexOf(current);

        path.unshift(index);

        current=parent;

    }

    let candidate=englishDocumentNode;

    for(const index of path){

        candidate=candidate?.children?.[index];

        if(!candidate){

            break;

        }

    }

    if(candidate&&candidate.tagName===node.tagName){

        return candidate;

    }

    const line=node.getAttribute("line");

    if(line){

        const lineMatches=Array.from(
            englishDocumentNode.querySelectorAll("[line]")
        );

        const lineMatch=lineMatches.find(
            item=>item.getAttribute("line")===line
        );

        if(lineMatch){

            return lineMatch;

        }

    }

    return node;

}

function englishEntry(node){

    if(language!=="en"||!englishRender||!node){

        return null;

    }

    const line=node.getAttribute("line");

    if(!line){

        return null;

    }

    const documentNode=ancestor(node,"document");

    const documentId=documentNode?.getAttribute("id");

    if(!documentId){

        return null;

    }

    return englishRender.entries?.[`${documentId}:${line}`]||null;

}

function toggleLanguage(){

    language=language==="la"?"en":"la";

    if(currentPlaceName){

        showPlaceMentions(
            currentPlaceName,
            currentPlaceContext,
            currentPlaceMention
        );

        return;

    }

    if(currentNode){

        show(currentNode);

    }

}

function displayNode(node){

    return parallelNode(node);

}

function showLine(node){

    const shown=displayNode(node);

    section("Notitia");

    const table=createTable();

    const rendered=englishEntry(node);

    row(
        table,
        "Text",
        rendered?.english||sourceLineText(shown)||clean(shown.textContent)
    );

    row(table,"Line",node.getAttribute("line"));

    directRows(table,node,shown);

    appendTable(table);

    showContext(node);

    showProvincePlaces(node);

}

function showContext(node){

    section("Context");

    const contextTable=createTable();

    const documentNode=ancestor(node,"document");

    const chapterNode=ancestor(node,"chapter");

    row(contextTable,"Document",documentNode?.getAttribute("id"));

    row(contextTable,"Chapter",displayDirectTitle(chapterNode));

    row(contextTable,"Context",displayContextPath(node));

    appendTable(contextTable);

}

function showProvincePlaces(node){

    if(typeof Data?.getPlaceMentionsByProvince!=="function"){

        return;

    }

    const provinceName=directTexts(node,"province")[0]||nodeLabel(node);

    const mentions=Data.getPlaceMentionsByProvince(provinceName)||[];

    if(!mentions.length){

        return;

    }

    const names=[...new Set(
        mentions
            .map(item=>clean(item.placeName))
            .filter(Boolean)
    )];

    if(!names.length){

        return;

    }

    section("Places");

    const list=document.createElement("div");

    list.className="inspectorContents";

    for(const name of names){

        const div=document.createElement("div");

        div.className="inspectorEntry";

        div.textContent=name;

        div.style.cursor="pointer";

        div.style.textDecoration="underline";

        div.addEventListener("click",()=>selectPlace(name,node));

        list.appendChild(div);

    }

    panel.appendChild(list);

}

function multiMentionPlaceForNode(node){

    if(
        !node||
        typeof Data?.getPlaceMentions!=="function"
    ){

        return "";

    }

    const names=directTexts(node,"place");

    for(const name of names){

        const mentions=Data.getPlaceMentions(name)||[];

        if(mentions.length>1){

            return name;

        }

    }

    return "";

}

function selectPlace(placeName,contextNode=null){

    Map.showPlace(placeName);

    showPlaceMentions(placeName,contextNode);

}

function showPlaceMentions(
    placeName,
    contextNode=null,
    selectedMention=null
){

    if(typeof Data?.getPlaceMentions!=="function"){

        return;

    }

    const mentions=Data.getPlaceMentions(placeName)||[];

    const selectedNode=selectedMention
        ? mentionNode(selectedMention,contextNode)
        : null;

    currentNode=selectedNode||contextNode;
    currentPlaceName=placeName;
    currentPlaceContext=contextNode;
    currentPlaceMention=selectedMention;

    panel.innerHTML="";

    heading(placeName);

    section(
        mentions.length===1
            ? "Notitia — 1 mention"
            : `Notitia — ${mentions.length} mentions`
    );

    const list=document.createElement("div");

    list.className="inspectorContents";

    for(const mention of mentions){

        const div=document.createElement("div");

        div.className="inspectorEntry";

        div.textContent=mentionText(mention);

        const node=mentionNode(mention,contextNode||selectedNode);

        if(node){

            div.style.cursor="pointer";
            div.style.textDecoration="underline";

            div.addEventListener("click",()=>{
                showPlaceMentions(placeName,node,mention);
            });

        }

        if(
            selectedMention&&
            mention?.occurrenceId===selectedMention?.occurrenceId
        ){

            div.style.fontWeight="700";

        }

        list.appendChild(div);

    }

    panel.appendChild(list);

    if(selectedNode){

        showLine(selectedNode);

        return;

    }

    if(contextNode){

        showContext(contextNode);

    }

}

function mentionNode(mention,contextNode=null){

    const document=contextNode?.ownerDocument;

    const line=clean(mention?.sourceLine);

    const documentId=clean(mention?.document);

    if(!document||!line){

        return null;

    }

    const candidates=Array.from(
        document.querySelectorAll("[line]")
    ).filter(node=>node.getAttribute("line")===line);

    if(!candidates.length){

        return null;

    }

    if(!documentId){

        return candidates[0];

    }

    return candidates.find(node=>{

        const documentNode=ancestor(node,"document");

        return clean(documentNode?.getAttribute("id")).toLowerCase()===
            documentId.toLowerCase();

    })||candidates[0];

}

function mentionText(mention){

    const text=[
        mention?.office,
        mention?.unit
    ].map(clean).filter(Boolean).join(" ");

    return text||clean(mention?.placeName);

}

function showContainer(node){

    const shown=displayNode(node);

    const items=Array.from(node.children||[])
        .filter(child=>child.tagName!=="title");

    const shownItems=Array.from(shown.children||[])
        .filter(child=>child.tagName!=="title");

    if(items.length){

        section("Contents");

        const list=document.createElement("div");

        list.className="inspectorContents";

        for(let i=0;i<items.length;i++){

            const div=document.createElement("div");

            div.className="inspectorEntry";

            div.textContent=containerItemText(shownItems[i]||items[i]);

            list.appendChild(div);

        }

        panel.appendChild(list);

    }

    section("Context");

    const table=createTable();

    if(node.tagName==="document"){

        row(table,"Document",node.getAttribute("id"));

    }
    else{

        const documentNode=ancestor(node,"document");

        const chapterNode=ancestor(node,"chapter");

        row(table,"Document",documentNode?.getAttribute("id"));

        if(node.tagName!=="chapter"){

            row(table,"Chapter",displayDirectTitle(chapterNode));

        }

        row(table,"Context",displayContextPath(node));

    }

    appendTable(table);

}

function containerItemText(node){

    return directTitle(node)||sourceLineText(node)||clean(node.textContent);

}

function isContainer(node){

    return ["document","chapter","group"].includes(node.tagName);

}

function directRows(table,node,shownNode=node){

    const fields=[
        ["Office","office"],
        ["Unit","unit"],
        ["Function","function"],
        ["Place","place"],
        ["Province","province"],
        ["Region","region"]
    ];

    for(const [label,tag] of fields){

        const originalValue=directTexts(node,tag).join(" / ");

        const displayValue=directTexts(shownNode,tag).join(" / ")||originalValue;

        if(label==="Place"&&originalValue){

            clickableRow(
                table,
                label,
                displayValue,
                ()=>selectPlace(originalValue,node)
            );

        }
        else{

            row(table,label,displayValue);

        }

    }

}

function displayContextPath(node){

    const titles=[];

    let current=node.parentElement;

    while(current){

        if(current.tagName==="group"){

            const title=displayDirectTitle(current);

            if(title){

                titles.push(title);

            }

        }

        current=current.parentElement;

    }

    return titles.reverse().join(" / ");

}

function sourceLineText(node){

    const parts=[];

    for(const child of node.childNodes||[]){

        if(child.nodeType===Node.TEXT_NODE){

            const value=clean(child.textContent);

            if(value){

                parts.push(value);

            }

            continue;

        }

        if(child.nodeType!==Node.ELEMENT_NODE){

            continue;

        }

        if(child.tagName==="place"&&child.getAttribute("source")){

            continue;

        }

        const value=clean(child.textContent);

        if(value){

            parts.push(value);

        }

    }

    return clean(parts.join(" "));

}

function displayNodeLabel(node){

    const rendered=englishEntry(node);

    return rendered?.english||nodeLabel(displayNode(node));

}

function nodeLabel(node){

    if(node.tagName==="document"){

        return node.getAttribute("id")||"Document";

    }

    const title=directTitle(node);

    if(title){

        return title;

    }

    if(node.getAttribute("line")){

        return sourceLineText(node)||clean(node.textContent);

    }

    return node.tagName;

}

function displayDirectTitle(node){

    if(!node){

        return "";

    }

    return directTitle(displayNode(node));

}

function directTitle(node){

    return directTexts(node,"title")[0]||"";

}

function directTexts(node,tagName){

    return Array.from(node?.children||[])
        .filter(child=>child.tagName===tagName)
        .map(child=>clean(child.textContent))
        .filter(Boolean);

}

function ancestor(node,tagName){

    let current=node;

    while(current){

        if(current.tagName===tagName){

            return current;

        }

        current=current.parentElement;

    }

    return null;

}

function clean(value){

    return String(value||"").replace(/\s+/g," ").trim();

}

function heading(text){

    const wrapper=document.createElement("div");

    wrapper.style.display="flex";

    wrapper.style.alignItems="flex-start";

    wrapper.style.justifyContent="space-between";

    wrapper.style.gap="12px";

    const h=document.createElement("h2");

    h.textContent=text;

    h.style.marginRight="auto";

    const button=document.createElement("button");

    button.type="button";

    button.textContent=language==="la"?"English":"Latin";

    button.title=language==="la"
        ?"Show English translation"
        :"Show Latin original";

    button.style.flex="0 0 auto";
    button.style.border="0";
    button.style.borderRadius="999px";
    button.style.padding="6px 12px";
    button.style.font="600 13px -apple-system, BlinkMacSystemFont, \"SF Pro Text\", sans-serif";
    button.style.letterSpacing="-0.01em";
    button.style.color="#ffffff";
    button.style.background=language==="la"?"#ff3b30":"#34c759";
    button.style.boxShadow="0 1px 2px rgba(0,0,0,0.16), inset 0 0 0 0.5px rgba(255,255,255,0.28)";
    button.style.cursor="pointer";
    button.style.webkitAppearance="none";
    button.style.appearance="none";

    button.addEventListener("mouseenter",()=>{
        button.style.filter="brightness(0.96)";
    });

    button.addEventListener("mouseleave",()=>{
        button.style.filter="";
    });

    button.addEventListener("click",toggleLanguage);

    wrapper.appendChild(h);

    wrapper.appendChild(button);

    panel.appendChild(wrapper);

}

function section(text){

    const h=document.createElement("h3");

    h.textContent=text;

    panel.appendChild(h);

}

function createTable(){

    const table=document.createElement("table");

    table.className="inspectorTable";

    return table;

}

function clickableRow(table,label,value,onClick){

    const text=clean(value);

    if(!text){

        return;

    }

    const tr=document.createElement("tr");

    const th=document.createElement("th");

    const td=document.createElement("td");

    th.textContent=label;

    td.textContent=text;

    td.style.cursor="pointer";

    td.style.textDecoration="underline";

    td.addEventListener("click",onClick);

    tr.appendChild(th);

    tr.appendChild(td);

    table.appendChild(tr);

}

function row(table,label,value){

    const text=clean(value);

    if(!text){

        return;

    }

    const tr=document.createElement("tr");

    const th=document.createElement("th");

    const td=document.createElement("td");

    th.textContent=label;

    td.textContent=text;

    tr.appendChild(th);

    tr.appendChild(td);

    table.appendChild(tr);

}

function appendTable(table){

    if(table.children.length){

        panel.appendChild(table);

    }

}