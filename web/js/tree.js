//
// Living Notitia
// tree.js
//

import * as XML from "./xml.js";
import * as Content from "./content.js";
import * as Inspector from "./inspector.js";

let container = null;

const expanded = new Set();

let roots = [];

export function initialize(){

    container=document.getElementById("tree");

    roots=[];

    const root=XML.root();

    for(const document of root.querySelectorAll(":scope > document")){

        let node;

if(document.id==="Occidentis"){

    node=buildOccidentis(document);

}else{

    node=buildTreeNode(document);

}

roots.push(node);

expanded.add(node);

    }

}

export function build(){

    container.innerHTML = "";

    const ul = document.createElement("ul");

    container.appendChild(ul);

    for(const node of roots){

        renderNode(node,ul);

    }

}

function buildTreeNode(xml){

    const node={

        xml:xml,

        label:getLabel(xml),

        children:[]

    };

    addChildren(
        node,
        xml
    );

    return node;

}

function addChildren(parentNode,xml){

    for(const child of xml.children){

        if(isVisible(child)){

            parentNode.children.push(
                buildTreeNode(child)
            );

        }else{

            addChildren(
                parentNode,
                child
            );

        }

    }

}

function renderNode(node,parent){

    const li=document.createElement("li");
    parent.appendChild(li);

    const span=document.createElement("span");
    li.appendChild(span);

    span.className="treeNode";

    if(node.children.length){

        span.textContent=
            (expanded.has(node) ? "▼ " : "▶ ")
            + node.label;

    }else{

        span.textContent=node.label;

    }

    span.addEventListener("click",event=>{

        event.stopPropagation();

        if(node.children.length){

            if(expanded.has(node))
                expanded.delete(node);
            else
                expanded.add(node);

            build();

        }

        if(node.xml){

    Inspector.show(node.xml);

    }

    });

    if(expanded.has(node) && node.children.length){

        const ul=document.createElement("ul");
        li.appendChild(ul);

        for(const child of node.children){

            renderNode(child,ul);

        }

    }

}

function isVisible(node){

    switch(node.tagName){

        case "document":
        case "chapter":
        case "group":
        case "list":
        case "item":
        case "office":
        case "unit":
            return true;

        case "title":
            return false;

        default:
            return false;

    }

}

function shortenLabel(text){

    return text

        .replace(
            /^Notitia dignitatum.*/i,
            "Overview"
        )

        .replace(
            /^Insignia viri illustris /i,
            ""
        )

        .replace(
            /^Sub dispositione viri illustris /i,
            ""
        )

        .replace(
            /^Officium viri illustris /i,
            "Officium "
        )

        .trim();

}

function getLabel(node){

    switch(node.tagName){

        case "document":{

            const item=node.querySelector(":scope > item");

            return item
                ? item.textContent.trim()
                : "Document";

        }

        case "chapter":{

            const title=node.querySelector(":scope > title");

            if(!title){

                return "Chapter";

            }

            return shortenLabel(
                title.textContent.trim()
            );

        }

        case "group":{

            const title=node.querySelector(":scope > title");

            return title
                ? shortenLabel(title.textContent.trim())
                : "Group";

        }

        case "list":{

            const title=node.querySelector(":scope > title");

            return title
                ? shortenLabel(title.textContent.trim())
                : "List";

        }

        case "item":{

            const text=node.textContent.trim();

            if(text.length>80){

                return text.substring(0,77)+"...";

            }

            return text;

        }

        case "unit":{

            return node.textContent.trim();

        }

        case "office":{

            return node.textContent.trim();

        }

        default:{

            return node.tagName;

        }

    }

}

function virtualNode(label){

    return{

        virtual:true,

        label:label,

        xml:null,

        children:[]

    };

}

function buildOccidentis(document){
    const root=virtualNode("Occidentis");
    const imperial=buildImperialAdministration(document);
    root.children.push(imperial);
    expanded.add(imperial);
    return root;
}
function buildImperialAdministration(document){
    const node=virtualNode("Imperial Administration");
    const chapter=document.querySelector(":scope > chapter");
    if(!chapter){
        return node;
    }
    for(const row of chapter.children){
        if(row.tagName==="title"){
            continue;
        }
        if(row.tagName==="unknown"){
            let label="";
            const office=row.querySelector(":scope > office");
            const unit=row.querySelector(":scope > unit");
            if(office){
                label=office.textContent.trim();
            }
            if(unit){
                if(label){
                    label+=" ";
                }
                label+=unit.textContent.trim();
            }
            if(label){
                node.children.push({
                    virtual:false,
                    label:label,
                    xml:row,
                    children:[]
                });
            }
            continue;
        }
        if(row.tagName==="group"){
            const title=row.querySelector(":scope > title");
            const text=title ? title.textContent.trim() : "";
            if(/^Magistri scriniorum/i.test(text)){
                node.children.push({
                    virtual:false,
                    label:"Magistri scriniorum",
                    xml:row,
                    children:[]
                });
            }
            break;
        }
    }
    return node;
}