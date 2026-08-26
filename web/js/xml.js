//
// Living Notitia
// xml.js
//

let xmlDocument=null;

export async function load(url){

    const response=await fetch(url);

    const text=await response.text();

    const parser=new DOMParser();

    xmlDocument=parser.parseFromString(
        text,
        "application/xml"
    );

}

export function document(){

    return xmlDocument.documentElement.querySelector("document");

}

export function documents(){

    return Array.from(
        xmlDocument.documentElement.querySelectorAll(
            ":scope>document"
        )
    );

}

export function root(){

    return xmlDocument.documentElement;

}

export function children(node){

    return Array.from(node.children).filter(child=>{

        return child.tagName!=="title";

    });

}

export function child(node,name){

    return node.querySelector(`:scope>${name}`);

}

export function title(node){

    const t=child(node,"title");

    return t ? t.textContent.trim() : "";

}

export function text(node){

    return node.textContent.trim();

}

export function attr(node,name){

    return node.getAttribute(name);

}
