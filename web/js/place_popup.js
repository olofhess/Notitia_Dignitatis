//
// Living Notitia
// placePopup.js
//

import Content from "./content.js";

const PlacePopup={

initialized:false,

initialize(){

    if(this.initialized){
        return;
    }

    this.initialized=true;

    document.addEventListener(
        "click",
        event=>{

            const link=
                event.target.closest(
                    ".placeContextLink"
                );

            if(!link){
                return;
            }

            event.preventDefault();

            const detail={
                contextId:
                    link.dataset.contextId||"",
                placeId:
                    link.dataset.placeId||"",
                placeName:
                    link.dataset.placeName||"",
                chapter:
                    link.dataset.chapter||"",
                document:
                    link.dataset.document||""
            };

            document.dispatchEvent(
                new CustomEvent(
                    "notitia:place-context",
                    {
                        detail
                    }
                )
            );

        }
    );

},

build(placeOrName){

    this.initialize();

    const place=
        typeof placeOrName==="object"
            ? placeOrName
            : Content.getPlace(placeOrName);

    const placeName=
        place?.placeName||
        String(placeOrName||"");

    const rows=
        Content.getContext(placeName);

    let html="";

    html+="<div class='placePopup'>";

    html+="<h3 class='placePopupTitle'>";
    html+=this.escape(placeName);
    html+="</h3>";

    html+=this.buildNotitia(rows);

    html+=this.buildPleiades(place);

    html+="</div>";

    return html;

},

buildNotitia(rows){

    let html="";

    html+="<section class='placePopupSection'>";
    html+="<h4 class='placePopupHeading'>";
    html+="Notitia";
    html+="</h4>";

    if(!rows.length){

        html+="<div class='placePopupEmpty'>";
        html+="Ingen kontext hittades i Notitia.";
        html+="</div>";

        html+="</section>";

        return html;

    }

    const uniqueRows=
        this.uniqueContextRows(rows);

    for(const row of uniqueRows){

        html+="<a";
        html+=" href='#'";
        html+=" class='placeContextLink'";
        html+=" data-context-id='";
        html+=this.attribute(row.contextId);
        html+="'";
        html+=" data-place-id='";
        html+=this.attribute(row.placeId);
        html+="'";
        html+=" data-place-name='";
        html+=this.attribute(row.placeName);
        html+="'";
        html+=" data-chapter='";
        html+=this.attribute(row.chapter);
        html+="'";
        html+=" data-document='";
        html+=this.attribute(row.document);
        html+="'";
        html+=">";

        if(row.office){

            html+="<div class='placePopupOffice'>";
            html+=this.escape(row.office);
            html+="</div>";

        }

        if(row.unit){

            html+="<div class='placePopupUnit'>";
            html+=this.escape(row.unit);
            html+="</div>";

        }

        const context=
            this.contextLabel(row);

        if(context){

            html+="<div class='placePopupContext'>";
            html+=this.escape(context);
            html+="</div>";

        }

        html+="</a>";

    }

    html+="</section>";

    return html;

},

buildPleiades(place){

    if(!place){
        return "";
    }

    let html="";

    html+="<section class='placePopupSection ";
    html+="placePopupPleiades'>";

    html+="<h4 class='placePopupHeading'>";
    html+="Pleiades";
    html+="</h4>";

    if(place.pleiadesName){

        html+="<div class='placePopupPleiadesName'>";
        html+=this.escape(place.pleiadesName);
        html+="</div>";

    }

    if(place.description){

        html+="<div class='placePopupDescription'>";
        html+=this.escape(
            this.cleanDescription(
                place.description
            )
        );
        html+="</div>";

    }

    if(place.uri){

        html+="<a";
        html+=" class='placePopupExternalLink'";
        html+=" href='";
        html+=this.attribute(place.uri);
        html+="'";
        html+=" target='_blank'";
        html+=" rel='noopener noreferrer'";
        html+=">";
        html+="Öppna i Pleiades";
        html+="</a>";

    }

    html+="</section>";

    return html;

},

uniqueContextRows(rows){

    const result=[];
    const seen=new Set();

    for(const row of rows){

        const key=[
            row.placeId||"",
            row.office||"",
            row.unit||"",
            row.chapter||"",
            row.document||""
        ].join("|");

        if(seen.has(key)){
            continue;
        }

        seen.add(key);
        result.push(row);

    }

    return result;

},

contextLabel(row){

    const parts=[];

    if(row.chapter){
        parts.push(row.chapter);
    }

    if(row.document){
        parts.push(row.document);
    }

    return parts.join(" · ");

},

cleanDescription(value){

    let text=String(value||"").trim();

    if(
        text.startsWith('"')&&
        text.endsWith('"')
    ){
        text=text.slice(1,-1);
    }

    return text;

},

escape(value){

    return String(value||"")
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");

},

attribute(value){

    return this.escape(value);

}

};

export default PlacePopup;