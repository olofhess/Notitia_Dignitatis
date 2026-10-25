//
// Living Notitia
// map_places.js
//
// Point-place data helpers extracted from map.js.
// Behaviour is intentionally unchanged.
//

import Data from "./data.js";
import * as XML from "./xml.js";
import {
    PLACE_MARKER_STYLE,
    PLACE_TYPE_STYLES
} from "./map_styles.js";

function normalize(value) {
    return String(value || "")
        .replace(/\s+/g, " ")
        .replace(/\.$/, "")
        .trim()
        .toLowerCase();
}

function placeName(place) {
    return place?.placeName || place?.sourcePlaceName || place?.name || "Place";
}

function mappedPlace(place) {
    const latitude = Number(place?.latitude);
    const longitude = Number(place?.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;
    return { place, latitude, longitude, name: placeName(place) };
}

function placeKey(item) {
    return `${normalize(item.name)}|${item.latitude}|${item.longitude}`;
}

function uniqueMappedPlaces(places) {
    const result = [];
    const seen = new Set();

    for (const place of places) {
        const item = mappedPlace(place);
        if (!item) continue;
        const key = placeKey(item);
        if (seen.has(key)) continue;
        seen.add(key);
        result.push(item);
    }
    return result;
}

function resolvePlace(value) {
    if (!value) return null;
    if (typeof value !== "string") return value;

    const wanted = normalize(value);
    return Data.getAllPlaces().find(place =>
        [place.placeName, place.sourcePlaceName, place.pleiadesName, place.name, place.candidate]
            .some(name => normalize(name) === wanted)
    ) || null;
}

function hasPlace(value) {
    const place = resolvePlace(value);
    return Boolean(
        place &&
        Number.isFinite(Number(place.latitude)) &&
        Number.isFinite(Number(place.longitude))
    );
}

function directChildText(node, tagName) {
    return Array.from(node?.children || [])
        .find(child => child.tagName === tagName)
        ?.textContent || "";
}

function ancestor(node, tagName) {
    let current = node;
    while (current) {
        if (current.tagName === tagName) return current;
        current = current.parentElement;
    }
    return null;
}

function findPlaceSourceNode(place) {
    const wantedPlaces = [place?.sourcePlaceName, place?.placeName, place?.name]
        .map(normalize)
        .filter(Boolean);
    if (!wantedPlaces.length) return null;

    const candidates = [];
    for (const documentNode of XML.documents()) {
        for (const placeNode of documentNode.querySelectorAll("place")) {
            if (wantedPlaces.includes(normalize(placeNode.textContent))) {
                candidates.push(placeNode.parentElement);
            }
        }
    }
    if (candidates.length <= 1) return candidates[0] || null;

    const wanted = {
        document: normalize(place.document),
        chapter: normalize(place.chapter),
        unit: normalize(place.unit),
        office: normalize(place.office)
    };

    let best = candidates[0];
    let bestScore = -1;

    for (const candidate of candidates) {
        const documentNode = ancestor(candidate, "document");
        const chapterNode = ancestor(candidate, "chapter");
        const actual = {
            document: normalize(documentNode?.getAttribute("id")),
            chapter: normalize(directChildText(chapterNode, "title")),
            unit: normalize(directChildText(candidate, "unit")),
            office: normalize(directChildText(candidate, "office"))
        };

        let score = 0;
        if (wanted.document && actual.document === wanted.document) score += 4;
        if (wanted.chapter && actual.chapter === wanted.chapter) score += 4;
        if (wanted.unit && actual.unit === wanted.unit) score += 3;
        if (wanted.office && actual.office === wanted.office) score += 2;

        if (score > bestScore) {
            best = candidate;
            bestScore = score;
        }
    }
    return best;
}

function mentionType(row) {
    const source = normalize(row?.placeSource);
    const chapter = normalize(row?.chapter);
    const context = normalize(row?.contextText);
    const office = normalize(row?.office);
    const unit = normalize(row?.unit);
    const text = `${chapter} ${context} ${office} ${unit}`;

    if (source === "factory" || /\bfabrica\w*\b/.test(text)) {
        return "fabrica";
    }

    // Specific military roles take precedence over the Dux/Comes chapter context.
    if (/\btribun\w*\b/.test(office)) {
        return "tribunus";
    }

    if (/\bequit\w*\b/.test(unit)) {
        return "equites";
    }

    if (/\bdux\b/.test(text)) {
        return "dux";
    }

    if (/\b(comes|comitis)\b/.test(text)) {
        return "comes";
    }

    if (office) {
        return "office";
    }

    return "other";
}

// Build a name-to-category index from the actual Notitia XML occurrences.
// Gazetteer display names and Data.getPlaceMentions() lookup keys are not
// guaranteed to coincide; failed lookups must not turn every marker grey.
let xmlTypeIndex = null;

function xmlTypesByName() {
    if (xmlTypeIndex) return xmlTypeIndex;
    const index = new Map();
    for (const documentNode of XML.documents()) {
        for (const placeNode of documentNode.querySelectorAll("place")) {
            const name = normalize(placeNode.textContent);
            if (!name) continue;
            const chapter = ancestor(placeNode, "chapter");
            const container = placeNode.parentElement;
            const row = {
                chapter: directChildText(chapter, "title") || chapter?.getAttribute("title") || "",
                contextText: container?.textContent || "",
                office: directChildText(container, "office"),
                unit: directChildText(container, "unit"),
                placeSource: container?.getAttribute("source") || ""
            };
            const type = mentionType(row);
            if (type === "other") continue;
            if (!index.has(name)) index.set(name, new Set());
            index.get(name).add(type);
        }
    }
    xmlTypeIndex = index;
    return index;
}

function placeType(place) {
    const names = [place?.sourcePlaceName, place?.placeName, place?.name]
        .map(normalize).filter(Boolean);
    const types = new Set();

    // Explicit mention metadata remains the first source.
    for (const name of names) {
        const mentions = Data.getPlaceMentions(name) || [];
        for (const mention of mentions) {
            const type = mentionType(mention);
            if (type !== "other") types.add(type);
        }
    }

    // When a Gazetteer name fails to resolve in the mention table, look up
    // the original XML occurrences rather than silently using grey.
    if (!types.size) {
        const index = xmlTypesByName();
        for (const name of names) {
            for (const type of index.get(name) || []) types.add(type);
        }
    }

    if (types.size > 1) return "mixed";
    return types.size ? [...types][0] : "other";
}

function placeMarkerStyle(place) {
    return PLACE_TYPE_STYLES[placeType(place)] || PLACE_MARKER_STYLE;
}

export {
    placeName,
    mappedPlace,
    placeKey,
    uniqueMappedPlaces,
    resolvePlace,
    hasPlace,
    findPlaceSourceNode,
    placeType,
    placeMarkerStyle
};
