//
// Living Notitia
// map.js
//

import Data from "./data.js";
import * as XML from "./xml.js";
import { REGIONS } from "./regions.js";

const PROVINCE_FILE = "../data/provinces.geojson";
const DEFAULT_VIEW = [41, 15];
const DEFAULT_ZOOM = 4;
const PLACE_ZOOM = 8;

const PLACE_MARKER_STYLE = {
    radius: 3.5, weight: 1, color: "#496b78", fillColor: "#6f919d",
    opacity: 0.8, fillOpacity: 0.68, bubblingMouseEvents: false
};
const PROVINCE_PLACE_MARKER_STYLE = {
    radius: 4, weight: 1.2, color: "#496b78", fillColor: "#f7f3ec",
    opacity: 0.95, fillOpacity: 0.95, bubblingMouseEvents: false
};
const SEARCH_MARKER_STYLE = {
    pane: "searchResultsPane", radius: 5.5, weight: 1.5,
    color: "#8e5039", fillColor: "#d09a76",
    opacity: 0.95, fillOpacity: 0.85, bubblingMouseEvents: false
};
const SELECTED_PLACE_STYLE = {
    pane: "selectedPlacePane", radius: 7.5, weight: 2.5,
    color: "#ffffff", fillColor: "#8f3027",
    opacity: 1, fillOpacity: 1, interactive: false
};

let map = null;
let provinceLayer = null;
let placesLayer = null;
let provinceGeoJSON = null;
let selectedPlaceMarker = null;
let selectedProvinceLayers = [];
let searchResultsLayer = null;
let provincePlacesLayer = null;
let placesLayerWasVisibleBeforeSearch = null;
let placesLayerWasVisibleBeforeProvinceFocus = null;

function setStatus(text) {
    const node = document.getElementById("status");
    if (node) node.textContent = text;
}

function normalize(value) {
    return String(value || "")
        .replace(/\s+/g, " ")
        .replace(/\.$/, "")
        .trim()
        .toLowerCase();
}

function provinceName(feature) {
    const p = feature?.properties || {};
    return p.PROV_NAME || p.prov_name || p.NAME || p.name ||
        p.PROVINCE || p.province || "Unknown province";
}

function provinceObjectId(feature) {
    const value = Number(feature?.properties?.OBJECTID);
    return Number.isFinite(value) ? value : null;
}

function provinceStyle() {
    return {
        color: "#7f8c94", weight: 0.9, opacity: 0.68,
        fillColor: "#aeb8bd", fillOpacity: 0.045
    };
}

function selectedProvinceStyle() {
    return {
        color: "#9a4c35", weight: 2.2, opacity: 0.96,
        fillColor: "#c9825e", fillOpacity: 0.19
    };
}

async function loadProvinces() {
    const response = await fetch(PROVINCE_FILE, { cache: "no-store" });
    if (!response.ok) {
        throw new Error(`Could not load ${PROVINCE_FILE}: HTTP ${response.status}`);
    }
    provinceGeoJSON = await response.json();
}

function setPlacesLayerVisible(visible) {
    if (!map || !placesLayer) return;
    if (visible && !map.hasLayer(placesLayer)) placesLayer.addTo(map);
    if (!visible && map.hasLayer(placesLayer)) map.removeLayer(placesLayer);
}

function clearPlace(resetView = false) {
    if (!map) return;
    map.stop();
    map.closePopup();

    if (selectedPlaceMarker) {
        map.removeLayer(selectedPlaceMarker);
        selectedPlaceMarker = null;
    }
    if (resetView) map.setView(DEFAULT_VIEW, DEFAULT_ZOOM, { animate: false });
}

function restorePlacesLayer(previousVisibility) {
    if (previousVisibility === true) setPlacesLayerVisible(true);
    if (previousVisibility === false) setPlacesLayerVisible(false);
}

function clearSearchResults() {
    if (!map) return;
    if (searchResultsLayer) {
        map.removeLayer(searchResultsLayer);
        searchResultsLayer = null;
    }
    restorePlacesLayer(placesLayerWasVisibleBeforeSearch);
    placesLayerWasVisibleBeforeSearch = null;
}

function beginSearchMode() {
    if (!map || !placesLayer) return;
    if (placesLayerWasVisibleBeforeSearch === null) {
        placesLayerWasVisibleBeforeSearch = map.hasLayer(placesLayer);
    }
    setPlacesLayerVisible(false);
}

function clearProvincePlaces() {
    if (!map) return;
    if (provincePlacesLayer) {
        map.removeLayer(provincePlacesLayer);
        provincePlacesLayer = null;
    }
    restorePlacesLayer(placesLayerWasVisibleBeforeProvinceFocus);
    placesLayerWasVisibleBeforeProvinceFocus = null;
}

function beginProvinceFocus() {
    if (!map || !placesLayer) return;
    if (placesLayerWasVisibleBeforeProvinceFocus === null) {
        placesLayerWasVisibleBeforeProvinceFocus = map.hasLayer(placesLayer);
    }
    setPlacesLayerVisible(false);
}

function clearProvince() {
    if (provinceLayer) {
        for (const layer of selectedProvinceLayers) provinceLayer.resetStyle(layer);
    }
    selectedProvinceLayers = [];
}

function clearSelection(resetView = false, clearSearch = true) {
    clearPlace(resetView);
    clearProvince();
    if (clearSearch) clearSearchResults();
    clearProvincePlaces();
}

function highlightProvince(feature) {
    clearProvince();
    if (!feature || !provinceLayer) return;

    provinceLayer.eachLayer(layer => {
        if (layer.feature !== feature) return;
        layer.setStyle(selectedProvinceStyle());
        selectedProvinceLayers.push(layer);
    });
}

function fitLayerBounds(layers, options) {
    const bounds = L.latLngBounds([]);
    for (const layer of layers) {
        if (typeof layer.getBounds === "function") bounds.extend(layer.getBounds());
    }
    map.invalidateSize();
    if (bounds.isValid()) map.fitBounds(bounds, options);
}

function showRegion(regionKey) {
    const region = REGIONS[regionKey];
    if (!region || !map || !provinceLayer) return [];

    clearSelection(false);
    const names = new Set(region.provinces.map(normalize));

    provinceLayer.eachLayer(layer => {
        if (!names.has(normalize(provinceName(layer.feature)))) return;
        layer.setStyle(selectedProvinceStyle());
        selectedProvinceLayers.push(layer);
    });

    fitLayerBounds(selectedProvinceLayers, { padding: [40, 40], animate: false });
    setStatus(`${region.label} — ${selectedProvinceLayers.length} province areas`);
    return selectedProvinceLayers;
}

function findProvince(latitude, longitude) {
    if (!provinceGeoJSON) return null;
    const point = turf.point([Number(longitude), Number(latitude)]);

    for (const feature of provinceGeoJSON.features || []) {
        const type = feature?.geometry?.type;
        if (type !== "Polygon" && type !== "MultiPolygon") continue;
        if (turf.booleanPointInPolygon(point, feature)) return feature;
    }
    return null;
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

function createPlaceMarker(item, targetLayer, markerStyle, showOptions = {}, tooltipOptions = {}) {
    const marker = L.circleMarker([item.latitude, item.longitude], markerStyle);
    marker.bindTooltip(item.name, tooltipOptions);
    marker.on("click", () => {
        if (!showPlace(item.place, showOptions)) return;
        notifyPlaceSelection(item.place, findPlaceSourceNode(item.place));
    });
    marker.addTo(targetLayer);
    return marker;
}

function placesInProvince(feature) {
    if (!feature) return [];
    const result = [];

    for (const item of uniqueMappedPlaces(Data.getAllPlaces())) {
        const point = turf.point([item.longitude, item.latitude]);
        if (turf.booleanPointInPolygon(point, feature)) result.push(item);
    }
    return result;
}

function placesInProvinces(features) {
    const result = [];
    const seen = new Set();

    for (const feature of features) {
        for (const item of placesInProvince(feature)) {
            const key = placeKey(item);
            if (seen.has(key)) continue;
            seen.add(key);
            result.push(item);
        }
    }
    return result;
}

function layersForProvinceObjectIds(values) {
    const input = Array.isArray(values) ? values : [values];
    const wanted = new Set(input.map(Number).filter(Number.isFinite));
    if (!wanted.size || !provinceLayer) return [];

    const layers = [];
    provinceLayer.eachLayer(layer => {
        if (wanted.has(provinceObjectId(layer.feature))) layers.push(layer);
    });
    return layers;
}

function showProvinceObjectIds(values, label = "") {
    if (!map || !provinceLayer) return [];

    const layers = layersForProvinceObjectIds(values);
    if (!layers.length) {
        setStatus("Province not found");
        return [];
    }

    clearSearchResults();
    clearProvincePlaces();
    clearPlace(false);
    clearProvince();
    beginProvinceFocus();

    for (const layer of layers) {
        layer.setStyle(selectedProvinceStyle());
        selectedProvinceLayers.push(layer);
    }

    const items = placesInProvinces(layers.map(layer => layer.feature));
    provincePlacesLayer = L.layerGroup().addTo(map);

    for (const item of items) {
        createPlaceMarker(
            item,
            provincePlacesLayer,
            PROVINCE_PLACE_MARKER_STYLE,
            { preserveView: true },
            { permanent: true, direction: "top", offset: [0, -5], opacity: 0.9 }
        );
    }

    fitLayerBounds(layers, { padding: [35, 35], maxZoom: 9, animate: false });

    const names = [...new Set(layers.map(layer => provinceName(layer.feature)))].join(" / ");
    setStatus(`${label || names} — ${items.length} places`);
    return items.map(item => item.place);
}

function showProvince(feature) {
    const objectId = provinceObjectId(feature);
    return objectId === null
        ? []
        : showProvinceObjectIds([objectId], provinceName(feature));
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

function showPlace(value, options = {}) {
    if (Array.isArray(value)) return showSearchResults(value);
    if (!map) return null;

    const preserveSearchResults = Boolean(options.preserveSearchResults);
    const preserveView = Boolean(options.preserveView);
    clearSelection(false, !preserveSearchResults);

    const place = resolvePlace(value);
    if (!place) {
        clearPlace(true);
        setStatus("Place not mapped");
        return null;
    }

    const item = mappedPlace(place);
    const name = placeName(place);
    if (!item) {
        clearPlace(true);
        setStatus(`${name} — no coordinates`);
        return null;
    }

    const { latitude, longitude } = item;
    map.invalidateSize();
    if (!preserveView) map.setView([latitude, longitude], PLACE_ZOOM, { animate: false });

    selectedPlaceMarker = L.circleMarker(
        [latitude, longitude],
        SELECTED_PLACE_STYLE
    ).addTo(map);

    const province = findProvince(latitude, longitude);
    const provinceText = province ? provinceName(province) : "No province found";
    if (province) highlightProvince(province);

    selectedPlaceMarker
        .bindPopup(`<strong>${name}</strong><br>${provinceText}`, { autoPan: false })
        .openPopup();

    setStatus(`${name} — ${provinceText}`);
    return { place, province };
}

function showSearchResults(values) {
    if (!map) return [];

    clearProvincePlaces();
    beginSearchMode();

    const input = Array.isArray(values) ? values : [values];
    const resolved = input.map(resolvePlace).filter(Boolean);
    const mapped = uniqueMappedPlaces(resolved);

    clearPlace(false);
    clearProvince();

    if (searchResultsLayer) {
        map.removeLayer(searchResultsLayer);
        searchResultsLayer = null;
    }

    if (!mapped.length) {
        map.setView(DEFAULT_VIEW, DEFAULT_ZOOM, { animate: false });
        setStatus("No mapped places in search results");
        return [];
    }

    if (mapped.length === 1) {
        showPlace(mapped[0].place, { preserveSearchResults: true });
        return [mapped[0].place];
    }

    searchResultsLayer = L.layerGroup().addTo(map);
    const bounds = L.latLngBounds([]);

    for (const item of mapped) {
        createPlaceMarker(
            item,
            searchResultsLayer,
            SEARCH_MARKER_STYLE,
            { preserveSearchResults: true, preserveView: true }
        );
        bounds.extend([item.latitude, item.longitude]);
    }

    map.invalidateSize();
    if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: PLACE_ZOOM, animate: false });
    }

    // Search mode is exclusive: never leave the ordinary Places layer on.
    setPlacesLayerVisible(false);

    const missingCoordinates = resolved.length - mapped.length;
    const suffix = missingCoordinates ? ` — ${missingCoordinates} without coordinates` : "";
    setStatus(`${mapped.length} places shown${suffix}`);
    return mapped.map(item => item.place);
}

const showPlaceName = showPlace;

function getProvinceForPlace(place) {
    return place ? findProvince(place.latitude, place.longitude) : null;
}

function getProvinceForPlaceName(name) {
    return getProvinceForPlace(resolvePlace(name));
}

function notifyPlaceSelection(place, sourceNode) {
    document.dispatchEvent(new CustomEvent("notitia:map-place", {
        detail: { placeName: placeName(place), sourceNode }
    }));
}

function buildProvinceLayer() {
    provinceLayer = L.geoJSON(provinceGeoJSON, {
        style: provinceStyle,
        onEachFeature(feature, layer) {
            layer.bindTooltip(provinceName(feature));
            layer.on("click", () => showProvince(feature));
        }
    }).addTo(map);
}

function buildPlacesLayer() {
    placesLayer = L.layerGroup();
    let count = 0;

    for (const place of Data.getAllPlaces()) {
        const item = mappedPlace(place);
        if (!item) continue;
        createPlaceMarker(item, placesLayer, PLACE_MARKER_STYLE);
        count += 1;
    }

    placesLayer.addTo(map);
    return count;
}

async function init() {
    if (!document.getElementById("map")) {
        throw new Error("Map element #map was not found");
    }

    map = L.map("map").setView(DEFAULT_VIEW, DEFAULT_ZOOM);
    map.createPane("searchResultsPane");
    map.getPane("searchResultsPane").style.zIndex = "640";
    map.createPane("selectedPlacePane");
    map.getPane("selectedPlacePane").style.zIndex = "650";

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        opacity: 0.58,
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    await loadProvinces();
    buildProvinceLayer();
    const placeCount = buildPlacesLayer();

    L.control.layers(null, {
        Provinces: provinceLayer,
        Places: placesLayer
    }, { collapsed: false }).addTo(map);

    if (provinceLayer.getBounds().isValid()) {
        map.fitBounds(provinceLayer.getBounds(), { padding: [10, 10] });
    }

    requestAnimationFrame(() => map.invalidateSize());
    setStatus(`Map ready — ${placeCount} places`);
    console.log(`Provinces loaded: ${provinceGeoJSON.features?.length || 0}`);
    console.log(`Places loaded on map: ${placeCount}`);
}

const MapView = {
    init,
    clearSelection,
    clearSearchResults,
    beginSearchMode,
    setPlacesLayerVisible,
    hasPlace,
    showPlace,
    showPlaceName,
    showSearchResults,
    showRegion,
    showProvince,
    showProvinceObjectIds,
    getProvinceForPlace,
    getProvinceForPlaceName,
    findProvince
};

window.MapView = MapView;
export default MapView;
export {
    init,
    clearSelection,
    clearSearchResults,
    beginSearchMode,
    setPlacesLayerVisible,
    hasPlace,
    showPlace,
    showPlaceName,
    showSearchResults,
    showRegion,
    showProvince,
    showProvinceObjectIds,
    getProvinceForPlace,
    getProvinceForPlaceName,
    findProvince
};
