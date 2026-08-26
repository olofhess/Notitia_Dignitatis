//
// Living Notitia
// search.js
//

import * as XML from "./xml.js";

let searchIndex=[];

export function initialize(){

    searchIndex=[];

    const documents=XML.documents();

    documents.forEach(document=>{
        walk(document);
    });

    console.log(
        "SEARCH INDEX",
        searchIndex.length,
        "records"
    );

}

export function records(){

    return searchIndex;

}

export function search(options={}){

    const text=normalize(
        options.text||""
    );

    const placeSource=normalize(
        options.placeSource||""
    );

    const office=normalize(
        options.office||""
    );

    const dimension=normalize(
        options.dimension||""
    );

    return searchIndex.filter(record=>{

        if(
            text &&
            !record.searchText.includes(text)
        ){
            return false;
        }

        if(
            placeSource &&
            !record.places.some(
                place=>
                    normalize(place.source)===
                    placeSource
            )
        ){
            return false;
        }

        if(
            office &&
            normalize(record.officeType)!==
            office
        ){
            return false;
        }

        if(
            dimension &&
            normalize(record.dimension)!==
            dimension
        ){
            return false;
        }

        return true;

    });

}

export function placeSources(){

    return uniqueSorted(
        searchIndex
            .flatMap(
                record=>
                    record.places.map(
                        place=>place.source
                    )
            )
            .filter(Boolean)
    );

}

export function officeTypes(){

    return uniqueSorted(
        searchIndex
            .map(
                record=>record.officeType
            )
            .filter(Boolean)
    );

}

export function dimensions(){

    return uniqueSorted(
        searchIndex
            .filter(
                record=>record.unit
            )
            .map(
                record=>record.dimension
            )
            .filter(Boolean)
    );

}

function walk(node){

    searchIndex.push(
        createRecord(node)
    );

    const children=navigationChildren(node);

    children.forEach(child=>{
        walk(child);
    });

}

function navigationChildren(node){

    if(
        XML.attr(node,"line") &&
        node.tagName!=="group"
    ){
        return [];
    }

    return XML.children(node);

}

function createRecord(node){

    const officeNode=
        directChild(node,"office");

    const unitNode=
        directChild(node,"unit");

    const places=
        directChildren(node,"place")
            .map(place=>({
                name:clean(place.textContent),
                source:clean(
                    place.getAttribute("source")
                )
            }));

    const documentNode=
        ancestorOrSelf(
            node,
            "document"
        );

    const chapterNode=
        ancestorOrSelf(
            node,
            "chapter"
        );

    const title=
        directTitle(node);

    const context=
        contextTitles(node);

    const office=
        clean(
            officeNode?.textContent
        );

    const officeType=
        clean(
            officeNode?.getAttribute("type")
        );

    const unit=
        clean(
            unitNode?.textContent
        );

    const document=
        clean(
            documentNode?.getAttribute("id")
        );

    const chapter=
        directTitle(chapterNode);

    const dimension=
        node.tagName;

    const searchText=
        normalize(
            [
                title,
                office,
                officeType,
                unit,
                ...places.map(
                    place=>place.name
                ),
                ...places.map(
                    place=>place.source
                ),
                chapter,
                ...context,
                document
            ]
            .filter(Boolean)
            .join(" ")
        );

    return {
        node,
        line:
            clean(
                node.getAttribute("line")
            ),
        dimension,
        title,
        office,
        officeType,
        unit,
        places,
        document,
        chapter,
        context,
        searchText
    };

}

function directChild(node,name){

    return Array.from(
        node.children
    ).find(
        child=>child.tagName===name
    )||null;

}

function directChildren(node,name){

    return Array.from(
        node.children
    ).filter(
        child=>child.tagName===name
    );

}

function directTitle(node){

    if(!node){
        return "";
    }

    const title=
        directChild(
            node,
            "title"
        );

    return clean(
        title?.textContent
    );

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

function contextTitles(node){

    const result=[];

    let current=
        node.parentElement;

    while(current){

        if(current.tagName==="group"){

            const title=
                directTitle(current);

            if(title){
                result.unshift(title);
            }

        }

        if(current.tagName==="document"){
            break;
        }

        current=
            current.parentElement;

    }

    return result;

}

function uniqueSorted(values){

    return [
        ...new Set(values)
    ].sort(
        (a,b)=>
            a.localeCompare(
                b,
                undefined,
                {
                    sensitivity:"base"
                }
            )
    );

}

function clean(value){

    return String(
        value||""
    )
    .replace(
        /\s+/g,
        " "
    )
    .trim();

}

function normalize(value){

    return clean(value)
        .toLowerCase();

}