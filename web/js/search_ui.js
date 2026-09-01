//
// Living Notitia
// search_ui.js
//

import * as Search from "./search.js";
import * as Nav from "./nav.js";
import MapView from "./map.js";

let searchBox=null;
let placeSourceSelect=null;
let officeSelect=null;
let ownerOfficeSelect=null;
let dimensionSelect=null;
let status=null;
let resultsPanel=null;

export function initialize(){

    searchBox=
        document.getElementById("searchBox");

    const toolbar=
        document.getElementById("toolbar");

    status=
        document.getElementById("status");

    if(
        !searchBox ||
        !toolbar
    ){
        return;
    }

    placeSourceSelect=
        createSelect(
            "searchPlaceSource",
            "Place source",
            Search.placeSources()
        );

    officeSelect=
        createSelect(
            "searchOffice",
            "Office",
            Search.officeTypes()
        );

    ownerOfficeSelect=
        createSelect(
            "searchOwnerOffice",
            "Owner office",
            Search.ownerOffices()
        );

    dimensionSelect=
        createSelect(
            "searchDimension",
            "Dimension",
            Search.dimensions()
        );

    toolbar.appendChild(
        placeSourceSelect
    );

    toolbar.appendChild(
        officeSelect
    );

    toolbar.appendChild(
        ownerOfficeSelect
    );

    toolbar.appendChild(
        dimensionSelect
    );

    createResultsPanel();

    searchBox.addEventListener(
        "input",
        runSearch
    );

    placeSourceSelect.addEventListener(
        "change",
        runSearch
    );

    officeSelect.addEventListener(
        "change",
        runSearch
    );

    ownerOfficeSelect.addEventListener(
        "change",
        runSearch
    );

    dimensionSelect.addEventListener(
        "change",
        runSearch
    );

}

function createSelect(
    id,
    label,
    values
){

    const select=
        document.createElement("select");

    select.id=id;

    const all=
        document.createElement("option");

    all.value="";
    all.textContent=
        label+": All";

    select.appendChild(all);

    values.forEach(value=>{

        const option=
            document.createElement("option");

        option.value=value;
        option.textContent=value;

        select.appendChild(option);

    });

    return select;

}

function createResultsPanel(){

    const header=
        document.getElementById("header");

    if(!header){
        return;
    }

    resultsPanel=
        document.createElement("div");

    resultsPanel.id=
        "searchResults";

    resultsPanel.style.display=
        "none";

    resultsPanel.style.padding=
        "8px 12px";

    resultsPanel.style.borderTop=
        "1px solid #ccc";

    resultsPanel.style.background=
        "#fff";

    // Search results are an overlay over the left navigation column only.
    // They must never cover the map or push the workspace down.
    resultsPanel.style.position=
        "fixed";

    resultsPanel.style.left=
        "0";

    resultsPanel.style.right=
        "auto";

    resultsPanel.style.zIndex=
        "2000";

    resultsPanel.style.boxSizing=
        "border-box";

    resultsPanel.style.overflowY=
        "auto";

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

    const header=
        document.getElementById("header");

    const mapElement=
        document.getElementById("map");

    if(!header){
        return;
    }

    const headerRect=
        header.getBoundingClientRect();

    const top=
        Math.max(0,headerRect.bottom);

    let width=360;

    if(mapElement){
        const mapRect=
            mapElement.getBoundingClientRect();

        if(mapRect.left>0){
            width=mapRect.left;
        }
    }

    let bottom=
        window.innerHeight;

    if(status){
        const statusRect=
            status.getBoundingClientRect();

        if(
            statusRect.top>top &&
            statusRect.top<bottom
        ){
            bottom=statusRect.top;
        }
    }

    resultsPanel.style.top=
        top+"px";

    resultsPanel.style.width=
        Math.max(220,width)+"px";

    resultsPanel.style.maxHeight=
        Math.max(120,bottom-top)+"px";

}

function runSearch(){

    const text=
        searchBox.value.trim();

    const placeSource=
        placeSourceSelect.value;

    const office=
        officeSelect.value;

    const ownerOffice=
        ownerOfficeSelect.value;

    const dimension=
        dimensionSelect.value;

    if(
        !text &&
        !placeSource &&
        !office &&
        !ownerOffice &&
        !dimension
    ){

        if(status){
            status.textContent="Ready";
        }

        clearResults();
        MapView.clearSearchResults();

        return;
    }

    // A new search must start from a clean map selection.
    // Keep the Inspector as it is, but remove any previously selected
    // place marker, popup and province highlight before drawing search results.
    MapView.clearSelection(false);

    const results=
        Search.search({
            text,
            placeSource,
            office,
            ownerOffice,
            dimension
        });

    showResults(results);
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

    console.log(
        "SEARCH RESULTS",
        results
    );

}


function showResultsOnMap(results){

    const places=[];

    results.forEach(record=>{

        (record.places || [])
            .forEach(place=>{

                if(
                    place &&
                    Number.isFinite(
                        Number(place.latitude)
                    ) &&
                    Number.isFinite(
                        Number(place.longitude)
                    )
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

    MapView.showSearchResults(
        places
    );

}

function showResults(results){

    if(!resultsPanel){
        return;
    }

    resultsPanel.innerHTML="";

    if(!results.length){

        const empty=
            document.createElement("div");

        empty.textContent=
            "No results";

        resultsPanel.appendChild(
            empty
        );

        positionResultsPanel();

        resultsPanel.style.display=
            "block";

        return;
    }

    const maxResults=50;

    results
        .slice(0,maxResults)
        .forEach(record=>{

            resultsPanel.appendChild(
                createResultRow(record)
            );

        });

    if(results.length>maxResults){

        const more=
            document.createElement("div");

        more.style.padding=
            "6px 0";

        more.textContent=
            "Showing first "+
            maxResults+
            " of "+
            results.length+
            " results";

        resultsPanel.appendChild(
            more
        );

    }

    positionResultsPanel();

    resultsPanel.style.display=
        "block";

}

function createResultRow(record){

    const row=
        document.createElement("div");

    row.className=
        "searchResult";

    row.style.padding=
        "5px 0";

    row.style.borderBottom=
        "1px solid #eee";

    row.style.cursor=
        "pointer";

    row.title=
        "Open in Living Notitia";

    row.onclick=function(){

        if(
            Nav.selectNode(
                record.node
            )
        ){
            clearResults();
            searchBox.blur();
        }

    };

    const main=
        document.createElement("div");

    main.style.fontWeight=
        "600";

    main.textContent=
        resultTitle(record);

    row.appendChild(main);

    const detail=
        document.createElement("div");

    detail.style.fontSize=
        "12px";

    detail.textContent=
        resultDetail(record);

    row.appendChild(detail);

    return row;

}

function resultTitle(record){

    if(record.unit){
        return record.unit;
    }

    if(record.title){
        return record.title;
    }

    if(record.office){
        return record.office;
    }

    return record.dimension;
}

function resultDetail(record){

    const parts=[];

    if(record.places.length){

        parts.push(
            record.places
                .map(place=>{
                    if(place.source){
                        return (
                            place.name+
                            " ["+
                            place.source+
                            "]"
                        );
                    }

                    return place.name;
                })
                .join(", ")
        );

    }

    if(record.chapter){
        parts.push(
            record.chapter
        );
    }

    if(record.line){
        parts.push(
            "line "+record.line
        );
    }

    return parts.join(" · ");

}

function clearResults(){

    if(!resultsPanel){
        return;
    }

    resultsPanel.innerHTML="";
    resultsPanel.style.display=
        "none";

}
