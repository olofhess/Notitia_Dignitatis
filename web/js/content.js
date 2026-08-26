//
// Living Notitia
// content.js
//
console.log("CONTENT FILE LOADED");
const Content={

gazetteer:[],
context:[],

gazetteerByName:new Map(),
contextByName:new Map(),
contextById:new Map(),

async initialize(){

    await this.loadGazetteer();

    await this.loadContext();

},

async loadGazetteer(){

    const response=
        await fetch("../csv/PlaceGazetteer.csv");

    const text=
        await response.text();

    const rows=this.parseCSV(text);

    this.gazetteer=rows;

    this.gazetteerByName.clear();

    for(const row of rows){

        this.gazetteerByName.set(
            row.placeName,
            row
        );

    }

},

async loadContext(){

    const response=
        await fetch("../csv/PlaceContext.csv");

    const text=
        await response.text();

    const rows=this.parseCSV(text);

    this.context=rows;

    this.contextByName.clear();
    this.contextById.clear();

    for(const row of rows){

        if(!this.contextByName.has(row.placeName)){

            this.contextByName.set(
                row.placeName,
                []
            );

        }

        this.contextByName
            .get(row.placeName)
            .push(row);

        this.contextById.set(
            row.contextId,
            row
);  

    }

},

parseCSV(text){

    const rows=[];

    const lines=text.trim().split("\n");

    const header=
        lines.shift().split(",");

    for(const line of lines){

        const cols=line.split(",");

        const row={};

        for(let i=0;i<header.length;i++){

            row[
                header[i].trim()
            ]=

            (cols[i]||"").trim();

        }

        rows.push(row);

    }

    return rows;

},

getPlace(placeName){

    return this.gazetteerByName.get(
        placeName
    );

},

getContext(placeName){

    return this.contextByName.get(
        placeName
    )||[];

},

getContextById(contextId){

    return this.contextById.get(
        contextId
    );
}
};

export default Content;
console.log(Content);


