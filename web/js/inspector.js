//
// Living Notitia
// inspector.js
//
import Data from "./data.js";
import * as Map from "./map.js";
let panel=null;
export function initialize(){
    panel=document.getElementById("inspector");
}
export function show(node){
    if(!panel){
        initialize();
    }
    if(!panel||!node){
        return;
    }
    panel.innerHTML="";
    heading(nodeLabel(node));
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
function showLine(node){
    section("Notitia");
    const table=createTable();
    row(table,"Text",sourceLineText(node)||clean(node.textContent));
    row(table,"Line",node.getAttribute("line"));
    directRows(table,node);
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
    row(contextTable,"Chapter",directTitle(chapterNode));
    row(contextTable,"Context",contextPath(node));
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
function selectPlace(placeName,contextNode=null){
    Map.showPlace(placeName);
    showPlaceMentions(placeName,contextNode);
}
function showPlaceMentions(placeName,contextNode=null){
    if(typeof Data?.getPlaceMentions!=="function"){
        return;
    }
    const mentions=Data.getPlaceMentions(placeName)||[];
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
        list.appendChild(div);
    }
    panel.appendChild(list);
    if(contextNode){
        showContext(contextNode);
    }
}
function mentionText(mention){
    const text=[
        mention?.office,
        mention?.unit
    ].map(clean).filter(Boolean).join(" ");
    return text||clean(mention?.placeName);
}
function showContainer(node){
    const items=Array.from(node.children||[]).filter(child=>child.tagName!=="title");
    if(items.length){
        section("Contents");
        const list=document.createElement("div");
        list.className="inspectorContents";
        for(const item of items){
            const div=document.createElement("div");
            div.className="inspectorEntry";
            div.textContent=containerItemText(item);
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
            row(table,"Chapter",directTitle(chapterNode));
        }
        row(table,"Context",contextPath(node));
    }
    appendTable(table);
}
function containerItemText(node){
    return directTitle(node)||sourceLineText(node)||clean(node.textContent);
}
function isContainer(node){
    return ["document","chapter","group"].includes(node.tagName);
}
function directRows(table,node){
    const fields=[
        ["Office","office"],
        ["Unit","unit"],
        ["Function","function"],
        ["Place","place"],
        ["Province","province"],
        ["Region","region"]
    ];
    for(const [label,tag] of fields){
        const value=directTexts(node,tag).join(" / ");
        if(label==="Place"&&value){
            clickableRow(table,label,value,()=>selectPlace(value,node));
        }
        else{
            row(table,label,value);
        }
    }
}
function contextPath(node){
    const titles=[];
    let current=node.parentElement;
    while(current){
        if(current.tagName==="group"){
            const title=directTitle(current);
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
    const h=document.createElement("h2");
    h.textContent=text;
    panel.appendChild(h);
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