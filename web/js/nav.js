//
// Living Notitia
// nav.js
//
import * as XML from "./xml.js";
import * as Inspector from "./inspector.js";
import * as Map from "./map.js";
let container=null;
let selected=null;
let rowByNode=new WeakMap();
let mapSelectionListenerInstalled=false;
const SECTIONS=[
    {
        title:"INDEX",
        chapters:[1]
    },
    {
        title:"REGIONAL ADMINISTRATION",
        chapters:[2,3,4]
    },
    {
        title:"MILITARY ORGANIZATION",
        chapters:[5,6,7]
    },
    {
        title:"CENTRAL ADMINISTRATION",
        chapters:[9,10,11,12,13,14,15,16,17]
    }
];
export function initialize(){
    container=document.getElementById("tree");
    if(!mapSelectionListenerInstalled){
        document.addEventListener(
            "notitia:map-place",
            handleMapPlaceSelection
        );
        mapSelectionListenerInstalled=true;
    }
}

function handleMapPlaceSelection(event){
    const node=event.detail?.sourceNode;
    if(!node){
        return;
    }
    selectNodeFromMap(node);
}
export function build(){
    container.innerHTML="";
    rowByNode=new WeakMap();
    const documents=XML.documents();
    if(!documents.length){
        return;
    }
    documents.forEach(document=>{
        container.appendChild(
            createDocument(document)
        );
    });
}
function createDocument(document){
    const documentWrapper=
        documentElement("div");
    documentWrapper.className="treeNode";
    const documentRow=
        documentElement("div");
    documentRow.className=
        "treeRow tree-document";
    const documentToggle=
        documentElement("span");
    documentToggle.className="toggle";
    documentToggle.textContent="▶";
    documentRow.appendChild(
        documentToggle
    );
    const documentLabel=
        documentElement("span");
    documentLabel.className="label";
    documentLabel.textContent=
        XML.attr(document,"id")||"Document";
    documentRow.appendChild(
        documentLabel
    );
    rowByNode.set(
        document,
        documentRow
    );
    documentRow.onclick=function(e){
        e.stopPropagation();
        select(
            documentRow,
            document
        );
    };
    documentWrapper.appendChild(
        documentRow
    );
    const documentChildren=
        documentElement("div");
    documentChildren.className=
        "treeChildren";
    documentChildren.style.display=
        "none";
    const chapters=
    XML.children(document).filter(
        node=>node.tagName==="chapter"
    );
const used=new Set();
    for(const section of SECTIONS){
        const sectionChapters=
            chapters.filter(chapter=>{
                const number=
                    chapterNumber(chapter);
                return section.chapters.includes(
                    number
                );
            });
        if(!sectionChapters.length){
            continue;
        }
        documentChildren.appendChild(
            createSection(
                section.title,
                sectionChapters
            )
        );
        sectionChapters.forEach(
            chapter=>used.add(chapter)
        );
    }
    const chapterVIII=
        chapters.find(
            chapter=>chapterNumber(chapter)===8
        );
    if(chapterVIII){
        documentChildren.appendChild(
            createNode(
                chapterVIII,
                1
            )
        );
        used.add(chapterVIII);
    }
    const remaining=
        chapters.filter(
            chapter=>!used.has(chapter)
        );
    remaining.forEach(chapter=>{
        documentChildren.appendChild(
            createNode(
                chapter,
                1
            )
        );
    });
    documentWrapper.appendChild(
        documentChildren
    );
    documentToggle.onclick=function(e){
        e.stopPropagation();
        const open=
            documentChildren.style.display!=="none";
        documentChildren.style.display=
            open ? "none" : "block";
        documentToggle.textContent=
            open ? "▶" : "▼";
    };
    return documentWrapper;
}
function documentElement(tagName){
    return window.document.createElement(
        tagName
    );
}
function createSection(title,chapters){
    const wrapper=
        documentElement("div");
    wrapper.className=
        "treeNode treeSection";
    const row=
        documentElement("div");
    row.className=
        "treeRow tree-section";
    row.style.paddingLeft="16px";
    const toggle=
        documentElement("span");
    toggle.className="toggle";
    toggle.textContent="▶";
    row.appendChild(toggle);
    const label=
        documentElement("span");
    label.className="label";
    label.textContent=title;
    row.appendChild(label);
    wrapper.appendChild(row);
    const list=
        documentElement("div");
    list.className="treeChildren";
    list.style.display="none";
    chapters.forEach(chapter=>{
        list.appendChild(
            createNode(
                chapter,
                2
            )
        );
    });
    wrapper.appendChild(list);
    row.onclick=function(e){
        e.stopPropagation();
        const open=
            list.style.display!=="none";
        list.style.display=
            open ? "none" : "block";
        toggle.textContent=
            open ? "▶" : "▼";
    };
    return wrapper;
}
function navigationChildren(node){
    // A node with a source line represents one original Latin line.
    // Its semantic children (office, unit, place, etc.) belong in
    // the Inspector, not as extra levels in the source tree.
    if(
        XML.attr(node,"line") &&
        node.tagName!=="group"
    ){
        return [];
    }
    return XML.children(node).filter(
        child=>child.tagName!=="title"
    );
}
function createNode(node,depth){
    const wrapper=
        documentElement("div");
    wrapper.className="treeNode";
    const row=
        documentElement("div");
    row.className=
        "treeRow tree-"+node.tagName;
    row.style.paddingLeft=
        (depth*16)+"px";
    rowByNode.set(
        node,
        row
    );
    const children=
        navigationChildren(node);
    let toggle=null;
    if(children.length){
        toggle=
            documentElement("span");
        toggle.className="toggle";
        toggle.textContent="▶";
        row.appendChild(toggle);
    }
    else{
        const spacer=
            documentElement("span");
        spacer.className="toggle";
        spacer.textContent="";
        row.appendChild(spacer);
    }
    const geo=
        documentElement("span");
    geo.className="geoFlag";
    geo.textContent="";
    if(node.tagName==="entry"){
        const placeName=entryPlaceName(node);
        if(placeName && Map.hasPlace(placeName)){
            geo.textContent="⚑";
        }
    }
    row.appendChild(geo);
    const label=
        documentElement("span");
    label.className="label";
    label.textContent=getLabel(node);
    row.appendChild(label);
    row.onclick=function(e){
        e.stopPropagation();
        select(
            row,
            node
        );
    };
    wrapper.appendChild(row);
    if(children.length){
        const list=
            documentElement("div");
        list.className="treeChildren";
        list.style.display="none";
        children.forEach(child=>{
            list.appendChild(
                createNode(
                    child,
                    depth+1
                )
            );
        });
        wrapper.appendChild(list);
        toggle.onclick=function(e){
            e.stopPropagation();
            const open=
                list.style.display!=="none";
            list.style.display=
                open ? "none" : "block";
            toggle.textContent=
                open ? "▶" : "▼";
        };
    }
    return wrapper;
}
function entryPlaceName(node){
    const text=
        XML.text(node)
            .replace(/\.$/,"")
            .trim();
    if(!text){
        return "";
    }
    if(text.includes(",")){
        return text
            .split(",")
            .pop()
            .trim();
    }
    return text;
}
function chapterNumber(node){
    const parent=
        node.parentElement;
    if(parent){
        const chapters=
            XML.children(parent).filter(
                child=>child.tagName==="chapter"
            );
        const index=
            chapters.indexOf(node);
        if(index>=0){
            return index+1;
        }
    }
    const number=
        XML.attr(node,"number");
    if(number){
        const value=
            romanToNumber(
                number.trim()
            );
        if(value){
            return value;
        }
    }
    const title=
        XML.title(node);
    const match=
        title.match(
            /^\s*([IVXLCDM]+)\./i
        );
    if(match){
        return romanToNumber(
            match[1]
        );
    }
    return null;
}
function romanToNumber(roman){
    const values={
        I:1,
        V:5,
        X:10,
        L:50,
        C:100,
        D:500,
        M:1000
    };
    let total=0;
    let previous=0;
    roman=
        roman.toUpperCase();
    for(
        let i=roman.length-1;
        i>=0;
        i--
    ){
        const value=
            values[roman[i]]||0;
        if(value<previous){
            total-=value;
        }
        else{
            total+=value;
            previous=value;
        }
    }
    return total;
}
function getLabel(node){
    if(node.tagName==="chapter"){
        const number=
            chapterNumber(node);
        const title=
            shortChapterTitle(
                XML.title(node)
            );
        if(number){
            return numberToRoman(number)+". "+title;
        }
        return title;
    }
    if(node.tagName==="block"){
        return shortBlockTitle(
            XML.text(node)
        );
    }
    if(node.tagName==="entry"){
        return XML.text(node);
    }
    return XML.title(node)||
        XML.text(node)||
        node.tagName;
}
function numberToRoman(number){
    const values=[
        [1000,"M"],
        [900,"CM"],
        [500,"D"],
        [400,"CD"],
        [100,"C"],
        [90,"XC"],
        [50,"L"],
        [40,"XL"],
        [10,"X"],
        [9,"IX"],
        [5,"V"],
        [4,"IV"],
        [1,"I"]
    ];
    let result="";
    for(const [value,roman] of values){
        while(number>=value){
            result+=roman;
            number-=value;
        }
    }
    return result;
}
function shortChapterTitle(text){
    const words=
        text
            .replace(/^\s*[IVXLCDM]+\.\s*/i,"")
            .replace(/[.?:;]+$/,"")
            .trim()
            .split(/\s+/)
            .filter(Boolean);
    if(!words.length){
        return "";
    }
    if(words.length===1){
        return words[0];
    }
    return words[0]+" "+words[words.length-1];
}
function shortBlockTitle(text){
    const lower=
        text.toLowerCase();
    if(
        lower.startsWith(
            "sub dispositione"
        )
    ){
        return "Sub dispositione";
    }
    if(
        lower.startsWith(
            "officium"
        )
    ){
        return "Officium";
    }
    if(
        lower.startsWith(
            "sub iurisdictione"
        )
    ){
        return "Sub iurisdictione";
    }
    if(
        lower.startsWith(
            "sub cura"
        )
    ){
        return "Sub cura";
    }
    return text;
}
export function selectNode(node){
    const row=
        rowByNode.get(node);
    if(!row){
        return false;
    }
    revealRow(row);
    select(
        row,
        node
    );
    row.scrollIntoView({
        block:"nearest"
    });
    return true;
}
function selectNodeFromMap(node){
    const row=
        rowByNode.get(node);
    if(!row){
        return false;
    }
    revealRow(row);
    selectRow(
        row,
        node
    );
    row.scrollIntoView({
        block:"nearest"
    });
    return true;
}
function revealRow(row){
    let current=
        row.parentElement;
    while(
        current &&
        current!==container
    ){
        if(
            current.classList &&
            current.classList.contains(
                "treeChildren"
            )
        ){
            current.style.display=
                "block";
            const wrapper=
                current.parentElement;
            if(wrapper){
                const parentRow=
                    wrapper.querySelector(
                        ":scope > .treeRow"
                    );
                if(parentRow){
                    const toggle=
                        parentRow.querySelector(
                            ":scope > .toggle"
                        );
                    if(
                        toggle &&
                        toggle.textContent
                    ){
                        toggle.textContent="▼";
                    }
                }
            }
        }
        current=
            current.parentElement;
    }
}
function selectRow(row,node){
    if(selected){
        selected.classList.remove(
            "selected"
        );
    }
    selected=row;
    row.classList.add(
        "selected"
    );
    Inspector.show(node);
}
function select(row,node){
    selectRow(
        row,
        node
    );
    const directPlaces=
        Array.from(
            node.children
        ).filter(
            child=>child.tagName==="place"
        );
    for(const placeNode of directPlaces){
        const placeName=
            placeNode.textContent.trim();
        if(
            placeName &&
            Map.showPlace(placeName)
        ){
            return;
        }
    }
    if(node.tagName==="entry"){
        const placeName=entryPlaceName(node);
        if(
            placeName &&
            Map.showPlace(placeName)
        ){
            return;
        }
    }
    Map.clearSelection(true);
}