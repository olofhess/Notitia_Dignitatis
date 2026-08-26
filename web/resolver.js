//
// Living Notitia
// resolver.js
// Resolves entries in chapter I to later detail or model chapters.
//
import {cleanLatinText,latinKey,keyContains} from "./latin.js";
export function resolveDetail(node){
    const documentNode=findAncestor(node,"document");
    const indexChapter=findAncestor(node,"chapter");
    if(!documentNode || !indexChapter){
        return null;
    }
    const chapters=Array.from(documentNode.children).filter(
        child=>child.tagName==="chapter"
    );
    if(chapters[0]!==indexChapter){
        return null;
    }
    const sourceText=indexMeaning(node,indexChapter);
    const sourceKey=latinKey(sourceText);
    if(!sourceKey.length){
        return null;
    }
    const direct=findBestDirect(chapters.slice(1),sourceKey);
    if(direct){
        return {
            chapter:direct,
            relation:"direct",
            sourceText
        };
    }
    const role=indexRole(node,indexChapter,sourceText);
    const model=findModelChapter(chapters.slice(1),role);
    if(model){
        return {
            chapter:model,
            relation:"model",
            sourceText
        };
    }
    return null;
}
function findBestDirect(chapters,sourceKey){
    let best=null;
    let bestMatched=0;
    let bestExtra=Infinity;
    for(const chapter of chapters){
        const targetKeys=chapterKeys(chapter);
        for(const targetKey of targetKeys){
            if(!keyContains(targetKey,sourceKey)){
                continue;
            }
            const matched=sourceKey.length;
            const extra=Math.max(
                0,
                targetKey.length-sourceKey.length
            );
            if(
                matched>bestMatched ||
                (
                    matched===bestMatched &&
                    extra<bestExtra
                )
            ){
                best=chapter;
                bestMatched=matched;
                bestExtra=extra;
            }
        }
    }
    return best;
}
function chapterKeys(chapter){
    const result=[];
    chapter.querySelectorAll("title").forEach(titleNode=>{
        const key=latinKey(titleNode.textContent);
        if(key.length){
            result.push(key);
        }
    });
    if(!result.length){
        const key=latinKey(chapter.textContent);
        if(key.length){
            result.push(key);
        }
    }
    return result;
}
function indexMeaning(node,indexChapter){
    const own=cleanLatinText(node.textContent).replace(/\.$/,"");
    if(hasOfficeWord(own)){
        return own;
    }
    const role=indexRole(node,indexChapter,own);
    if(!role){
        return own;
    }
    if(role==="magister scriniorum"){
        return role+" "+own;
    }
    return role+" "+own;
}
function indexRole(node,indexChapter,sourceText){
    if(hasOfficeWord(sourceText)){
        const ownRole=roleFromText(sourceText);
        if(ownRole){
            return ownRole;
        }
    }
    let current=node.parentElement;
    while(current && current!==indexChapter){
        const title=getDirectTitle(current);
        const role=roleFromGroupTitle(title);
        if(role){
            return role;
        }
        current=current.parentElement;
    }
    return roleFromText(sourceText);
}
function roleFromGroupTitle(value){
    const text=cleanLatinText(value).toLowerCase();
    if(/\bvicarii\b/.test(text)){
        return "vicarius";
    }
    if(/\bcomites\s+rei\s+militaris\b/.test(text)){
        return "comes";
    }
    if(/\bduces\b/.test(text)){
        return "dux";
    }
    if(/\bconsulares\b/.test(text)){
        return "consularis";
    }
    if(/\bcorrectores\b/.test(text)){
        return "corrector";
    }
    if(/\bpraesides\b/.test(text)){
        return "praeses";
    }
    if(/\bmagistri\s+scriniorum\b/.test(text)){
        return "magister scriniorum";
    }
    return "";
}
function roleFromText(value){
    const key=latinKey(value);
    const roles=[
        ["praefect","praefectus"],
        ["magistr","magister"],
        ["com","comes"],
        ["quaest","quaestor"],
        ["procons","proconsul"],
        ["vicar","vicarius"],
        ["duc","dux"],
        ["primicer","primicerius"],
        ["praeposit","praepositus"],
        ["consular","consularis"],
        ["correct","corrector"],
        ["praesid","praeses"],
        ["castrens","castrensis"]
    ];
    for(const [stem,role] of roles){
        if(key.includes(stem)){
            return role;
        }
    }
    return "";
}
function hasOfficeWord(value){
    return Boolean(roleFromText(value));
}
function findModelChapter(chapters,role){
    if(!role){
        return null;
    }
    const plural={
        consularis:"consulares",
        corrector:"correctores",
        praeses:"praesides"
    }[role];
    if(!plural){
        return null;
    }
    for(const chapter of chapters){
        const text=cleanLatinText(chapter.textContent).toLowerCase();
        if(
            text.includes("ceteri omnes "+plural) &&
            text.includes("ad similitudinem")
        ){
            return chapter;
        }
    }
    return null;
}
function getDirectTitle(node){
    const title=Array.from(node.children).find(
        child=>child.tagName==="title"
    );
    return title ? cleanLatinText(title.textContent) : "";
}
function findAncestor(node,tagName){
    let current=node;
    while(current){
        if(current.tagName===tagName){
            return current;
        }
        current=current.parentElement;
    }
    return null;
}
