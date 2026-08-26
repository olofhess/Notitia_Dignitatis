//
// Living Notitia
// map.js
//

import Data from "./data.js";
import * as XML from "./xml.js";

const PROVINCE_FILE = "../data/provinces.geojson";
const DEFAULT_VIEW = [41, 15];
const DEFAULT_ZOOM = 4;
const PLACE_ZOOM = 8;

let map = null;
let provinceLayer = null;
let placesLayer = null;
let provinceGeoJSON = null;
let selectedPlaceMarker = null;
let selectedProvinceLayer = null;

function setStatus(text) {
    const element = document.getElementById("status");
    if (element) {
        element.textContent = text;
    }
}

function provinceName(feature) {
    const properties = feature?.properties || {};

    return (
        properties.PROV_NAME ||
        properties.prov_name ||
        properties.NAME ||
        properties.name ||
        properties.PROVINCE ||
        properties.province ||
        "Unknown province"
    );
}

function provinceStyle() {
    return {
        weight: 1,
        opacity: 0.8,
        fillOpacity: 0.12
    };
}

function selectedProvinceStyle() {
    return {
        weight: 3,
        opacity: 1,
        fillOpacity: 0.28
    };
}

async function loadProvinces() {
    const response = await fetch(PROVINCE_FILE, { cache: "no-store" });

    if (!response.ok) {
        throw new Error(
            `Could not load ${PROVINCE_FILE}: HTTP ${response.status}`
        );
    }

    provinceGeoJSON = await response.json();
}

function clearPlace(resetView = false) {
    if (!map) {
        return;
    }

    map.stop();
    map.closePopup();

    if (selectedPlaceMarker) {
        map.removeLayer(selectedPlaceMarker);
        selectedPlaceMarker = null;
    }

    if (resetView) {
        map.setView(DEFAULT_VIEW, DEFAULT_ZOOM, { animate: false });
    }
}

function clearProvince() {
    if (selectedProvinceLayer && provinceLayer) {
        provinceLayer.resetStyle(selectedProvinceLayer);
    }

    selectedProvinceLayer = null;
}

function clearSelection(resetView = false) {
    clearPlace(resetView);
    clearProvince();
}

function highlightProvince(feature) {
    clearProvince();

    if (!feature || !provinceLayer) {
        return;
    }

    provinceLayer.eachLayer(layer => {
        if (layer.feature === feature) {
            layer.setStyle(selectedProvinceStyle());
            selectedProvinceLayer = layer;
        }
    });
}

function findProvince(latitude, longitude) {
    if (!provinceGeoJSON) {
        return null;
    }

    const point = turf.point([
        Number(longitude),
        Number(latitude)
    ]);

    for (const feature of provinceGeoJSON.features || []) {
        const type = feature?.geometry?.type;

        if (type !== "Polygon" && type !== "MultiPolygon") {
            continue;
        }

        if (turf.booleanPointInPolygon(point, feature)) {
            return feature;
        }
    }

    return null;
}

function normalize(value) {
    return String(value || "")
        .replace(/\s+/g, " ")
        .replace(/\.$/, "")
        .trim()
        .toLowerCase();
}

function resolvePlace(value) {
    if (!value) {
        return null;
    }

    if (typeof value !== "string") {
        return value;
    }

    const wanted = normalize(value);

    return Data.getAllPlaces().find(place =>
        [
            place.placeName,
            place.sourcePlaceName,
            place.pleiadesName,
            place.name,
            place.candidate
        ].some(name => normalize(name) === wanted)
    ) || null;
}

function hasPlace(value) {
    const place = resolvePlace(value);

    if (!place) {
        return false;
    }

    return (
        Number.isFinite(Number(place.latitude)) &&
        Number.isFinite(Number(place.longitude))
    );
}

function directChildText(node, tagName) {
    const child = Array.from(node?.children || []).find(
        element => element.tagName === tagName
    );

    return child?.textContent || "";
}

function ancestor(node, tagName) {
    let current = node;

    while (current) {
        if (current.tagName === tagName) {
            return current;
        }
        current = current.parentElement;
    }

    return null;
}

function findPlaceSourceNode(place) {
    const wantedPlaces = [
        place?.sourcePlaceName,
        place?.placeName,
        place?.name
    ]
        .map(normalize)
        .filter(Boolean);

    if (!wantedPlaces.length) {
        return null;
    }

    const candidates = [];

    for (const documentNode of XML.documents()) {
        for (const placeNode of documentNode.querySelectorAll("place")) {
            if (wantedPlaces.includes(normalize(placeNode.textContent))) {
                candidates.push(placeNode.parentElement);
            }
        }
    }

    if (candidates.length <= 1) {
        return candidates[0] || null;
    }

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

        if (wanted.document && actual.document === wanted.document) {
            score += 4;
        }
        if (wanted.chapter && actual.chapter === wanted.chapter) {
            score += 4;
        }
        if (wanted.unit && actual.unit === wanted.unit) {
            score += 3;
        }
        if (wanted.office && actual.office === wanted.office) {
            score += 2;
        }

        if (score > bestScore) {
            best = candidate;
            bestScore = score;
        }
    }

    return best;
}

function showPlace(value) {
    if (!map) {
        return null;
    }

    clearSelection();

    const place = resolvePlace(value);

    if (!place) {
        clearPlace(true);
        setStatus("Place not mapped");
        return null;
    }

    const latitude = Number(place.latitude);
    const longitude = Number(place.longitude);
    const name = place.placeName || place.sourcePlaceName || place.name || "Place";

    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        clearPlace(true);
        setStatus(`${name} — no coordinates`);
        return null;
    }

    map.invalidateSize();
    map.setView([latitude, longitude], PLACE_ZOOM, { animate: false });

    selectedPlaceMarker = L.circleMarker(
        [latitude, longitude],
        {
            pane: "selectedPlacePane",
            radius: 9,
            weight: 3,
            color: "#c00000",
            fillColor: "#c00000",
            opacity: 1,
            fillOpacity: 1,
            interactive: false
        }
    ).addTo(map);

    const province = findProvince(latitude, longitude);
    const provinceText = province
        ? provinceName(province)
        : "No province found";

    if (province) {
        highlightProvince(province);
    }

    selectedPlaceMarker
        .bindPopup(
            `<strong>${name}</strong><br>${provinceText}`,
            { autoPan: false }
        )
        .openPopup();

    setStatus(`${name} — ${provinceText}`);

    return { place, province };
}

const showPlaceName = showPlace;

function getProvinceForPlace(place) {
    return place
        ? findProvince(place.latitude, place.longitude)
        : null;
}

function getProvinceForPlaceName(placeName) {
    return getProvinceForPlace(resolvePlace(placeName));
}

function notifyPlaceSelection(place, sourceNode) {
    document.dispatchEvent(
        new CustomEvent("notitia:map-place", {
            detail: {
                placeName: place.placeName || place.sourcePlaceName || place.name,
                sourceNode
            }
        })
    );
}

function buildProvinceLayer() {
    provinceLayer = L.geoJSON(provinceGeoJSON, {
        style: provinceStyle,
        onEachFeature(feature, layer) {
            const name = provinceName(feature);

            layer.bindTooltip(name);
            layer.on("click", () => {
                clearPlace();
                highlightProvince(feature);
                setStatus(name);
            });
        }
    }).addTo(map);
}

function buildPlacesLayer() {
    placesLayer = L.layerGroup();
    let count = 0;

    for (const place of Data.getAllPlaces()) {
        const latitude = Number(place.latitude);
        const longitude = Number(place.longitude);

        if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
            continue;
        }

        const name = place.placeName || place.sourcePlaceName || place.name || "Place";

        const marker = L.circleMarker(
            [latitude, longitude],
            {
                radius: 4,
                weight: 1,
                fillOpacity: 0.8,
                bubblingMouseEvents: false
            }
        );

        marker.bindTooltip(name);
        marker.on("click", () => {
            if (!showPlace(place)) {
                return;
            }

            const sourceNode = findPlaceSourceNode(place);
            notifyPlaceSelection(place, sourceNode);
        });

        marker.addTo(placesLayer);
        count += 1;
    }

    placesLayer.addTo(map);
    return count;
}

async function init() {
    const mapElement = document.getElementById("map");

    if (!mapElement) {
        throw new Error("Map element #map was not found");
    }

    map = L.map("map").setView(DEFAULT_VIEW, DEFAULT_ZOOM);

    map.createPane("selectedPlacePane");
    map.getPane("selectedPlacePane").style.zIndex = "650";

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 18,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);

    await loadProvinces();
    buildProvinceLayer();
    const placeCount = buildPlacesLayer();

    L.control.layers(
        null,
        {
            Provinces: provinceLayer,
            Places: placesLayer
        },
        { collapsed: false }
    ).addTo(map);

    if (provinceLayer.getBounds().isValid()) {
        map.fitBounds(provinceLayer.getBounds(), { padding: [10, 10] });
    }

    requestAnimationFrame(() => map.invalidateSize());

    setStatus(`Map ready — ${placeCount} places`);

    console.log(
        `Provinces loaded: ${provinceGeoJSON.features?.length || 0}`
    );
    console.log(`Places loaded on map: ${placeCount}`);
}

const MapView = {
    init,
    clearSelection,
    hasPlace,
    showPlace,
    showPlaceName,
    getProvinceForPlace,
    getProvinceForPlaceName,
    findProvince
};

window.MapView = MapView;

export default MapView;
export {
    init,
    clearSelection,
    hasPlace,
    showPlace,
    showPlaceName,
    getProvinceForPlace,
    getProvinceForPlaceName,
    findProvince
};