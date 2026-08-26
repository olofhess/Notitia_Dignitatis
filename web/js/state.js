//
// Living Notitia
// state.js
//

let xml=null;

let selectedNode=null;

export function initialize(document){

    xml=document;

}

export function document(){

    return xml;

}

export function select(node){

    selectedNode=node;

}

export function selected(){

    return selectedNode;

}