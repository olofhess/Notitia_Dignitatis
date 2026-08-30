import * as XML from "./xml.js";
import * as Nav from "./nav.js";
import Content from "./content.js";
import * as Inspector from "./inspector.js";
import Data from "./data.js";
import * as Map from "./map.js";
import * as Search from "./search.js";
import * as SearchUI from "./search_ui.js";
import * as ProvinceGazetteer from "./province_gazetteer.js";

async function start(){

    await XML.load("../data/notitia.xml");

    Search.initialize();

    await Data.loadAll();

    await ProvinceGazetteer.initialize();

    await Content.initialize();

    Inspector.initialize();

    await Map.init();

    Nav.initialize();

    Nav.build();

    SearchUI.initialize();

}

start();
