//
// Living Notitia
// nav.js
//

import * as XML from "./xml.js";
import * as Inspector from "./inspector.js";
import * as Map from "./map.js";
import * as ProvinceGazetteer from "./province_gazetteer.js";
import { regionKeyForNavigation } from "./regions.js";

const SECTIONS = [
    { title: "INDEX", chapters: [1] },
    { title: "REGIONAL ADMINISTRATION", chapters: [2, 3, 4] },
    { title: "MILITARY ORGANIZATION", chapters: [5, 6, 7] },
    { title: "CENTRAL ADMINISTRATION", chapters: [9, 10, 11, 12, 13, 14, 15, 16, 17] }
];

let container = null;
let selected = null;
let rowByNode = new WeakMap();
let mapSelectionListenerInstalled = false;

function element(tagName, className = "", text = "") {
    const node = document.createElement(tagName);
    if (className) node.className = className;
    if (text !== "") node.textContent = text;
    return node;
}

function setExpanded(toggle, list, open) {
    list.style.display = open ? "block" : "none";
    if (toggle.textContent) toggle.textContent = open ? "▼" : "▶";
}

function toggleExpanded(toggle, list) {
    setExpanded(toggle, list, list.style.display === "none");
}

export function initialize() {
    container = document.getElementById("tree");
    if (mapSelectionListenerInstalled) return;
    document.addEventListener("notitia:map-place", handleMapPlaceSelection);
    mapSelectionListenerInstalled = true;
}

function handleMapPlaceSelection(event) {
    const node = event.detail?.sourceNode;
    if (node) selectNodeFromMap(node);
}

export function build() {
    container.innerHTML = "";
    rowByNode = new WeakMap();

    const documents = XML.documents();
    if (!documents.length) return;

    for (const documentNode of documents) {
        container.appendChild(createDocument(documentNode));
    }

    requestAnimationFrame(selectDeepLinkFromUrl);
}

function selectDeepLinkFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const line = params.get("line");
    if (!line) return false;

    const wantedDocument = params.get("document");
    const documentNode = XML.documents().find(node =>
        !wantedDocument || XML.attr(node, "id") === wantedDocument
    );
    if (!documentNode) return false;

    const target = Array.from(documentNode.querySelectorAll("[line]")).find(
        node => XML.attr(node, "line") === line
    );

    return target ? selectNode(target) : false;
}

function createDocument(documentNode) {
    const wrapper = element("div", "treeNode");
    const row = element("div", "treeRow tree-document");
    const toggle = element("span", "toggle", "▶");
    const label = element("span", "label", XML.attr(documentNode, "id") || "Document");
    const list = element("div", "treeChildren");

    list.style.display = "none";
    row.append(toggle, label);
    wrapper.append(row, list);
    rowByNode.set(documentNode, row);

    row.onclick = event => {
        event.stopPropagation();
        select(row, documentNode);
    };

    const chapters = XML.children(documentNode).filter(node => node.tagName === "chapter");
    const used = new Set();

    for (const section of SECTIONS) {
        const sectionChapters = chapters.filter(chapter =>
            section.chapters.includes(chapterNumber(chapter))
        );
        if (!sectionChapters.length) continue;

        list.appendChild(createSection(section.title, sectionChapters));
        sectionChapters.forEach(chapter => used.add(chapter));
    }

    const chapterVIII = chapters.find(chapter => chapterNumber(chapter) === 8);
    if (chapterVIII) {
        list.appendChild(createNode(chapterVIII, 1));
        used.add(chapterVIII);
    }

    for (const chapter of chapters) {
        if (!used.has(chapter)) list.appendChild(createNode(chapter, 1));
    }

    toggle.onclick = event => {
        event.stopPropagation();
        toggleExpanded(toggle, list);
    };

    return wrapper;
}

function createSection(title, chapters) {
    const wrapper = element("div", "treeNode treeSection");
    const row = element("div", "treeRow tree-section");
    const toggle = element("span", "toggle", "▶");
    const label = element("span", "label", title);
    const list = element("div", "treeChildren");

    row.style.paddingLeft = "16px";
    list.style.display = "none";
    row.append(toggle, label);
    wrapper.append(row, list);

    for (const chapter of chapters) {
        list.appendChild(createNode(chapter, 2));
    }

    row.onclick = event => {
        event.stopPropagation();
        toggleExpanded(toggle, list);
    };

    return wrapper;
}

function navigationChildren(node) {
    // A source line is a leaf in the navigation tree. Its semantic children
    // belong in the Inspector. Groups are the one exception.
    if (XML.attr(node, "line") && node.tagName !== "group") return [];
    return XML.children(node).filter(child => child.tagName !== "title");
}

function createNode(node, depth) {
    const wrapper = element("div", "treeNode");
    const row = element("div", `treeRow tree-${node.tagName}`);
    const children = navigationChildren(node);
    const toggle = element("span", "toggle", children.length ? "▶" : "");
    const geo = element("span", "geoFlag");
    const label = element("span", "label", getLabel(node));

    row.style.paddingLeft = `${depth * 16}px`;
    rowByNode.set(node, row);

    if (node.tagName === "entry") {
        const name = entryPlaceName(node);
        if (name && Map.hasPlace(name)) geo.textContent = "⚑";
    }

    row.append(toggle, geo, label);
    wrapper.appendChild(row);

    row.onclick = event => {
        event.stopPropagation();
        select(row, node);
    };

    if (!children.length) return wrapper;

    const list = element("div", "treeChildren");
    list.style.display = "none";

    for (const child of children) {
        list.appendChild(createNode(child, depth + 1));
    }

    wrapper.appendChild(list);
    toggle.onclick = event => {
        event.stopPropagation();
        toggleExpanded(toggle, list);
    };

    return wrapper;
}

function entryPlaceName(node) {
    const text = XML.text(node).replace(/\.$/, "").trim();
    return text.includes(",") ? text.split(",").pop().trim() : text;
}

function chapterNumber(node) {
    const parent = node.parentElement;
    if (parent) {
        const chapters = XML.children(parent).filter(child => child.tagName === "chapter");
        const index = chapters.indexOf(node);
        if (index >= 0) return index + 1;
    }

    const number = XML.attr(node, "number");
    if (number) {
        const value = romanToNumber(number.trim());
        if (value) return value;
    }

    const match = XML.title(node).match(/^\s*([IVXLCDM]+)\./i);
    return match ? romanToNumber(match[1]) : null;
}

function romanToNumber(roman) {
    const values = { I: 1, V: 5, X: 10, L: 50, C: 100, D: 500, M: 1000 };
    let total = 0;
    let previous = 0;

    for (let i = roman.toUpperCase().length - 1; i >= 0; i--) {
        const value = values[roman.toUpperCase()[i]] || 0;
        if (value < previous) total -= value;
        else {
            total += value;
            previous = value;
        }
    }
    return total;
}

function numberToRoman(number) {
    const values = [
        [1000, "M"], [900, "CM"], [500, "D"], [400, "CD"],
        [100, "C"], [90, "XC"], [50, "L"], [40, "XL"],
        [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]
    ];
    let result = "";

    for (const [value, roman] of values) {
        while (number >= value) {
            result += roman;
            number -= value;
        }
    }
    return result;
}

function shortChapterTitle(text) {
    const words = text
        .replace(/^\s*[IVXLCDM]+\.\s*/i, "")
        .replace(/[.?:;]+$/, "")
        .trim()
        .split(/\s+/)
        .filter(Boolean);

    if (words.length <= 1) return words[0] || "";
    return `${words[0]} ${words[words.length - 1]}`;
}

function shortBlockTitle(text) {
    const lower = text.toLowerCase();
    if (lower.startsWith("sub dispositione")) return "Sub dispositione";
    if (lower.startsWith("officium")) return "Officium";
    if (lower.startsWith("sub iurisdictione")) return "Sub iurisdictione";
    if (lower.startsWith("sub cura")) return "Sub cura";
    return text;
}

function getLabel(node) {
    if (node.tagName === "chapter") {
        const number = chapterNumber(node);
        const title = shortChapterTitle(XML.title(node));
        return number ? `${numberToRoman(number)}. ${title}` : title;
    }
    if (node.tagName === "block") return shortBlockTitle(XML.text(node));
    if (node.tagName === "entry") return XML.text(node);
    return XML.title(node) || XML.text(node) || node.tagName;
}

export function selectNode(node) {
    return selectNodeInternal(node, true);
}

function selectNodeFromMap(node) {
    return selectNodeInternal(node, false);
}

function selectNodeInternal(node, updateMap) {
    const row = rowByNode.get(node);
    if (!row) return false;

    revealRow(row);
    if (updateMap) select(row, node);
    else selectRow(row, node);
    row.scrollIntoView({ block: "nearest" });
    return true;
}

function revealRow(row) {
    let current = row.parentElement;

    while (current && current !== container) {
        if (current.classList?.contains("treeChildren")) {
            current.style.display = "block";
            const toggle = current.parentElement
                ?.querySelector(":scope > .treeRow")
                ?.querySelector(":scope > .toggle");
            if (toggle?.textContent) toggle.textContent = "▼";
        }
        current = current.parentElement;
    }
}

function selectRow(row, node) {
    selected?.classList.remove("selected");
    selected = row;
    row.classList.add("selected");
    Inspector.show(node);
}

function descendantPlaceNames(node) {
    if (!node) return [];
    return [...new Set(
        Array.from(node.querySelectorAll("place"))
            .map(placeNode => String(placeNode.textContent || "").trim())
            .filter(Boolean)
    )];
}

function showRegionForNode(node, label) {
    const chapter = node.closest?.("chapter");
    if (!chapter) return false;

    const regionKey = regionKeyForNavigation(chapterNumber(chapter), label);
    if (!regionKey) return false;

    Map.showRegion(regionKey);
    return true;
}

function showProvinceForNode(node, label) {
    const documentNode = node.closest?.("document");
    const line = XML.attr(node, "line");
    if (!documentNode || !line) return false;

    const objectIds = ProvinceGazetteer.geoObjectIdsForSource(
        XML.attr(documentNode, "id"),
        line
    );
    if (!objectIds.length) return false;

    Map.showProvinceObjectIds(objectIds, label);
    return true;
}

function showDirectPlace(node) {
    for (const placeNode of Array.from(node.children || [])) {
        if (placeNode.tagName !== "place") continue;
        const name = placeNode.textContent.trim();
        if (name && Map.showPlace(name)) return true;
    }

    if (node.tagName !== "entry") return false;
    const name = entryPlaceName(node);
    return Boolean(name && Map.showPlace(name));
}

function select(row, node) {
    selectRow(row, node);

    const label = getLabel(node).replace(/\.$/, "").trim();
    if (showRegionForNode(node, label)) return;
    if (showProvinceForNode(node, label)) return;

    const places = descendantPlaceNames(node);
    if (places.length > 1) {
        Map.showSearchResults(places);
        return;
    }

    if (showDirectPlace(node)) return;
    Map.clearSelection(true);
}
