//
// Living Notitia
// map.js
//

import Data from "./data.js";
import { resolvePlace as resolveStrictPlace } from "./place_resolver.js";
import { REGIONS } from "./regions.js";
import {
    placeName,
    mappedPlace as mappedPlaceUnchecked,
    placeKey,
    uniqueMappedPlaces,
    resolvePlace,
    hasPlace,
    findPlaceSourceNode,
    placeType,
    placeMarkerStyle
} from "./map_places.js";
import {
    PROVINCE_PLACE_MARKER_STYLE,
    SEARCH_MARKER_STYLE,
    SELECTED_PLACE_STYLE,
    addPlaceLegend
} from "./map_styles.js";
import {
    loadProvinces,
    buildProvinceLayer,
    getProvinceLayer,
    provinceFeatureCount,
    provinceName,
    provinceObjectId,
    clearProvince,
    selectProvinceLayers,
    highlightProvince,
    findProvince,
    layersForProvinceObjectIds,
    layersForProvinceNames
} from "./map_provinces.js";
import { resolveJurisdiction } from "./map_jurisdictions.js";


// Never convert missing Gazetteer coordinates to zero (Number(null) === 0).
// This local guard also protects callers of older map_places.js helpers.
function validCoordinates(place) {
    if (!place) return false;
    const lat = place.latitude;
    const lon = place.longitude;
    if (lat === null || lat === undefined || lon === null || lon === undefined) return false;
    if (String(lat).trim() === "" || String(lon).trim() === "") return false;
    const latitude = Number(lat);
    const longitude = Number(lon);
    return Number.isFinite(latitude) && Number.isFinite(longitude)
        && latitude >= -90 && latitude <= 90
        && longitude >= -180 && longitude <= 180;
}

function mappedPlace(place) {
    if (!validCoordinates(place)) return null;
    return mappedPlaceUnchecked(place);
}

const DEFAULT_VIEW = [41, 15];
const DEFAULT_ZOOM = 4;
const PLACE_ZOOM = 8;
const PLACE_LABEL_MIN_ZOOM = 6;

let map = null;
let placesLayer = null;
let roadsLayer = null;
let selectedPlaceMarker = null;
let searchResultsLayer = null;
let provincePlacesLayer = null;
let placesLayerWasVisibleBeforeSearch = null;
let placesLayerWasVisibleBeforeProvinceFocus = null;
let allPlaceMarkers = [];


function installPlaceLabelStyles() {
    if (document.getElementById("notitia-place-label-styles")) return;

    const style = document.createElement("style");
    style.id = "notitia-place-label-styles";
    style.textContent = `
        .notitia-place-label {
            background: transparent;
            border: 0;
            box-shadow: none;
            color: #222;
            font-size: 12px;
            font-weight: 600;
            line-height: 1.1;
            padding: 0 2px;
            white-space: nowrap;
            pointer-events: none;
            text-shadow:
                -1px -1px 0 rgba(255,255,255,.95),
                 1px -1px 0 rgba(255,255,255,.95),
                -1px  1px 0 rgba(255,255,255,.95),
                 1px  1px 0 rgba(255,255,255,.95);
        }

        .notitia-place-label::before {
            display: none;
        }

        #map.notitia-place-labels-hidden .notitia-place-label {
            display: none;
        }
    `;
    document.head.appendChild(style);
}

function updatePlaceLabelVisibility() {
    if (!map) return;

    const mapNode = document.getElementById("map");
    if (!mapNode) return;

    mapNode.classList.toggle(
        "notitia-place-labels-hidden",
        map.getZoom() < PLACE_LABEL_MIN_ZOOM
    );
}

function bindLatinPlaceLabel(marker, place) {
    const label = placeName(place);
    if (!label) return marker;

    marker.bindTooltip(label, {
        permanent: true,
        direction: "right",
        offset: [7, 0],
        opacity: 0.92,
        className: "notitia-place-label"
    });

    return marker;
}

function setStatus(text) {
    const node = document.getElementById("status");
    if (node) node.textContent = text;
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

function clearSelection(resetView = false, clearSearch = true) {
    clearPlace(resetView);
    clearProvince();
    if (clearSearch) clearSearchResults();
    clearProvincePlaces();
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
    if (!region || !map || !getProvinceLayer()) return [];

    clearSelection(false);

    const layers = layersForProvinceNames(region.provinces);
    selectProvinceLayers(layers);

    fitLayerBounds(layers, { padding: [40, 40], animate: false });
    setStatus(`${region.label} — ${layers.length} province areas`);
    return layers;
}

function showJurisdiction(node) {
    const spec = resolveJurisdiction(node);
    if (!spec || !map || !getProvinceLayer()) return false;

    clearSelection(false);
    beginProvinceFocus();

    const layers = layersForProvinceNames(spec.provinceNames || []);
    selectProvinceLayers(layers);

    if (layers.length) {
        fitLayerBounds(layers, { padding: [40, 40], maxZoom: 8, animate: false });

        const unresolved = Number(spec.unresolved || 0);
        const suffix = unresolved
            ? ` — ${unresolved} entries not mapped`
            : "";

        setStatus(`${spec.label} — ${layers.length} jurisdiction areas${suffix}`);
        return true;
    }

    map.setView(DEFAULT_VIEW, DEFAULT_ZOOM, { animate: false });
    setStatus(`${spec.label} — ${spec.note || "jurisdiction not mapped"}`);
    return true;
}


function normalizePlaceText(value) {
    return String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
}

function sourcePlaceName(place) {
    return String(
        place?.sourcePlaceName ||
        place?.source_place_name ||
        placeName(place) ||
        ""
    ).trim();
}

function placeQualifier(place) {
    const match = String(placeName(place) || "").match(/\(([^)]+)\)\s*$/);
    return match ? match[1].trim() : "";
}

function nodeContextText(node) {
    if (!node) return "";

    const parts = [];
    let current = node;

    while (current) {
        if (current.getAttribute) {
            for (const attr of ["line", "id", "number"]) {
                const value = current.getAttribute(attr);
                if (value) parts.push(value);
            }
        }

        for (const child of Array.from(current.children || [])) {
            if (["place", "province", "region", "title"].includes(child.tagName)) {
                const text = String(child.textContent || "").trim();
                if (text) parts.push(text);
            }
        }

        if (current === node) {
            const text = String(current.textContent || "").trim();
            if (text) parts.push(text);
        }

        if (current.tagName === "chapter" || current.tagName === "document") break;
        current = current.parentElement;
    }

    return normalizePlaceText(parts.join(" "));
}

function latinContextScore(qualifier, context) {
    const q = normalizePlaceText(qualifier);
    if (!q || !context) return 0;
    if (context.includes(q)) return 100;

    const tokens = q.split(/\s+/).filter(token => token.length >= 3);
    let score = 0;

    for (const token of tokens) {
        const stem = token.slice(0, Math.min(token.length, 6));
        if (stem.length >= 4 && context.includes(stem)) score += 15;
    }

    return score;
}

function placeCandidatesForSource(value) {
    const wanted = normalizePlaceText(
        typeof value === "string" ? value : sourcePlaceName(value)
    );
    if (!wanted) return [];

    return Data.getAllPlaces().filter(place => {
        const source = normalizePlaceText(sourcePlaceName(place));
        const display = normalizePlaceText(placeName(place).replace(/\s*\([^)]*\)\s*$/, ""));
        return source === wanted || display === wanted;
    });
}

// Verified occurrence mapping: the Aeliae of Dux Palaestinae is
// Aelia Capitolina (Jerusalem), not the homonymous site in Byzacena.
// Keep this local to its source chapter; do not rename the African site.
function verifiedOccurrencePlace(value, sourceNode) {
    if (!sourceNode) return null;
    const name = String(typeof value === "string" ? value :
        (value?.sourcePlaceName || value?.placeName || ""))
        .trim().toLowerCase().replace(/[.,]$/, "");
    if (name !== "aeliae" && name !== "adada") return null;
    let node = sourceNode;
    while (node && String(node.tagName).toLowerCase() !== "chapter") {
        node = node.parentElement;
    }
    if (!node) return null;
    const title = [...node.children].find(child =>
        String(child.tagName).toLowerCase() === "title")?.textContent || "";
    if (name === "aeliae" && /\bdux\s+palaestinae\b/i.test(title)) {
        return Data.getPlaceById("GAZ00424");
    }
    if (name === "adada" && /\bdux\s+syriae\b/i.test(title)) {
        // Notitia's Adada in Syria is not the Pisidian town. The station is
        // unlocated, so never fall back to an unrelated coordinate-bearing match.
        return Data.getPlaceById("GAZ00606") || {
            gazetteerId: "GAZ00606", placeName: "Adada", sourcePlaceName: "Adada",
            latitude: "", longitude: ""
        };
    }
    return null;
}

function resolvePlaceForContext(value, sourceNode = null) {
    const verified = verifiedOccurrencePlace(value, sourceNode);
    if (verified) return verified;
    if (!sourceNode) return resolvePlace(value);

    const candidates = placeCandidatesForSource(value);
    if (!candidates.length) return resolvePlace(value);
    if (candidates.length === 1) return candidates[0];

    const context = nodeContextText(sourceNode);
    const line = String(sourceNode.getAttribute?.("line") || "").trim();

    let best = null;
    let bestScore = -1;

    for (const candidate of candidates) {
        let score = 0;

        const qualifier = placeQualifier(candidate);
        score += latinContextScore(qualifier, context);

        const sourceLines = String(
            candidate?.sourceLines ||
            candidate?.sourceLine ||
            ""
        );
        if (line && sourceLines) {
            const lines = sourceLines.split(/[|;,]/).map(item => item.trim());
            if (lines.includes(line)) score += 250;
        }

        const status = String(
            candidate?.masterDecision ||
            candidate?.masterStatus ||
            candidate?.confidence ||
            ""
        ).toLowerCase();

        if (status.includes("accepted")) score += 5;
        if (status.includes("confirmed")) score += 3;
        if (status.includes("provisional") || status.includes("hold")) score -= 20;

        // Prefer an occurrence-qualified gazetteer row when its qualifier
        // agrees with the source context. Unqualified duplicates stay fallback.
        if (qualifier && latinContextScore(qualifier, context) > 0) score += 25;

        if (score > bestScore) {
            best = candidate;
            bestScore = score;
        }
    }

    return bestScore > 0 ? best : resolvePlace(value);
}

function activeSearchQuery() {
    const candidates = [
        document.getElementById("search"),
        document.getElementById("searchInput"),
        document.querySelector('input[type="search"]'),
        document.querySelector('input[placeholder*="Search" i]')
    ].filter(Boolean);

    for (const input of candidates) {
        const value = String(input.value || "").trim();
        if (value) return value;
    }

    return "";
}

function searchStem(value) {
    const normalized = normalizePlaceText(value).replace(/\s+/g, "");
    if (!normalized) return "";

    // Six letters is long enough to avoid most accidental matches while
    // still grouping Latin inflections: Pannonia/Pannoniae/Pannoniorum.
    return normalized.slice(0, Math.min(6, normalized.length));
}

function sourceMatchesActiveSearch(sourceNode, query) {
    if (!sourceNode || !query) return true;

    const context = nodeContextText(sourceNode).replace(/\s+/g, "");
    if (!context) return false;

    const normalizedQuery = normalizePlaceText(query).replace(/\s+/g, "");
    if (!normalizedQuery) return true;
    if (context.includes(normalizedQuery)) return true;

    const stem = searchStem(query);
    return Boolean(stem && stem.length >= 4 && context.includes(stem));
}

function searchInput(value) {
    if (
        value &&
        typeof value === "object" &&
        value.sourceNode &&
        ("name" in value || "placeName" in value || "value" in value)
    ) {
        return {
            value: value.name ?? value.placeName ?? value.value,
            sourceNode: value.sourceNode
        };
    }

    return { value, sourceNode: null };
}

function createPlaceMarker(
    item,
    targetLayer,
    markerStyle,
    showOptions = {},
    tooltipOptions = {},
    sourceNode = null
) {
    if (!validCoordinates(item)) return null;
    const marker = L.circleMarker([item.latitude, item.longitude], markerStyle);
    marker.bindTooltip(item.name, tooltipOptions);
    marker.on("click", () => {
        const node = sourceNode || findPlaceSourceNode(item.place);
        if (!showPlace(item.place, { ...showOptions, sourceNode: node })) return;
        notifyPlaceSelection(item.place, node);
    });
    marker.addTo(targetLayer);
    return marker;
}

function placesInProvince(feature) {
    if (!feature) return [];
    const result = [];

    for (const item of uniqueMappedPlaces(Data.getAllPlaces())) {
        if (!validCoordinates(item)) continue;
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

function showProvinceObjectIds(values, label = "") {
    if (!map || !getProvinceLayer()) return [];

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

    selectProvinceLayers(layers);

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

function showPlace(value, options = {}) {
    if (Array.isArray(value)) return showSearchResults(value);
    if (!map) return null;

    const preserveSearchResults = Boolean(options.preserveSearchResults);
    const preserveView = Boolean(options.preserveView);
    const sourceNode = options.sourceNode || null;
    clearSelection(false, !preserveSearchResults);

    const place = resolvePlaceForContext(value, sourceNode);
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

// A command is represented by its station points, not an invented polygon.
// Ambiguous, missing, and unlocated stations are counted but never plotted arbitrarily.
// Preserve category colours in search/command overlays; only use the search pane
// for stacking order. A static legend describes these same categories.
function categorySearchMarkerStyle(place) {
    return { ...placeMarkerStyle(place), pane: "searchResultsPane", radius: 5.5 };
}

function showCommandStations(chapter) {
    if (!map || !chapter) return null;
    const placeNodes = [...chapter.querySelectorAll('place')];
    const entries = [];
    const unresolved = [];
    const seen = new Set();
    for (const mention of placeNodes) {
        const name = (mention.textContent || '').trim();
        if (!name) continue;
        const verified = verifiedOccurrencePlace(name, mention);
        const result = verified
            ? {status: 'identified', place: verified}
            : resolveStrictPlace({ name });
        if (result.status !== 'identified') {
            unresolved.push({name, status: result.status});
            continue;
        }
        const place = result.place;
        const item = mappedPlace(place);
        if (!item) {
            unresolved.push({name, status: 'no coordinates'});
            continue;
        }
        const id = String(place.gazetteerId || placeKey(item));
        if (seen.has(id)) continue;
        seen.add(id);
        entries.push({ place, item, sourceNode: mention.parentElement });
    }
    clearSelection(false);
    beginSearchMode();
    searchResultsLayer = L.layerGroup().addTo(map);
    const bounds = L.latLngBounds([]);
    for (const entry of entries) {
        createPlaceMarker(entry.item, searchResultsLayer, categorySearchMarkerStyle(entry.place),
            {preserveSearchResults: true, preserveView: true}, {}, entry.sourceNode);
        bounds.extend([entry.item.latitude, entry.item.longitude]);
    }
    if (bounds.isValid()) {
        map.invalidateSize();
        map.fitBounds(bounds, {padding: [40, 40], maxZoom: PLACE_ZOOM, animate: false});
    }
    const label = chapter.querySelector(':scope > title')?.textContent?.trim() || 'Command';
    setStatus(`${label}: ${entries.length} distinct mapped stations; ${unresolved.length} unresolved mentions`);
    return { mapped: entries.map(e => e.place), unresolved };
}

function showSearchResults(values) {
    if (!map) return [];

    clearProvincePlaces();
    beginSearchMode();

    const input = Array.isArray(values) ? values : [values];
    const resolvedEntries = [];
    const query = activeSearchQuery();

    for (const raw of input) {
        const ref = searchInput(raw);

        // Search results may originate from a broad ancestor node. Keep only
        // occurrences whose own source context actually matches the active
        // search term. This prevents, for example, Constantiae in Lugdunensis
        // II from appearing in a search for Pannonia.
        if (ref.sourceNode && query && !sourceMatchesActiveSearch(ref.sourceNode, query)) {
            continue;
        }

        const place = resolvePlaceForContext(ref.value, ref.sourceNode);
        if (!place) continue;

        const item = mappedPlace(place);
        resolvedEntries.push({ place, item, sourceNode: ref.sourceNode });
    }

    const mappedEntries = [];
    const seen = new Set();

    for (const entry of resolvedEntries) {
        if (!entry.item) continue;
        const key = placeKey(entry.item);
        if (seen.has(key)) continue;
        seen.add(key);
        mappedEntries.push(entry);
    }

    clearPlace(false);
    clearProvince();

    if (searchResultsLayer) {
        map.removeLayer(searchResultsLayer);
        searchResultsLayer = null;
    }

    if (!mappedEntries.length) {
        map.setView(DEFAULT_VIEW, DEFAULT_ZOOM, { animate: false });
        setStatus("No mapped places in search results");
        return [];
    }

    if (mappedEntries.length === 1) {
        const entry = mappedEntries[0];
        showPlace(entry.place, {
            preserveSearchResults: true,
            sourceNode: entry.sourceNode
        });
        return [entry.place];
    }

    searchResultsLayer = L.layerGroup().addTo(map);
    const bounds = L.latLngBounds([]);

    for (const entry of mappedEntries) {
        createPlaceMarker(
            entry.item,
            searchResultsLayer,
            categorySearchMarkerStyle(entry.place),
            { preserveSearchResults: true, preserveView: true },
            {},
            entry.sourceNode
        );
        bounds.extend([entry.item.latitude, entry.item.longitude]);
    }

    map.invalidateSize();
    if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: PLACE_ZOOM, animate: false });
    }

    // Search mode is exclusive: never leave the ordinary Places layer on.
    setPlacesLayerVisible(false);

    const missingCoordinates = resolvedEntries.length - mappedEntries.length;
    const suffix = missingCoordinates ? ` — ${missingCoordinates} without coordinates` : "";
    setStatus(`${mappedEntries.length} places shown${suffix}`);
    return mappedEntries.map(entry => entry.place);
}

const showPlaceName = showPlace;

function getProvinceForPlace(place) {
    return validCoordinates(place) ? findProvince(Number(place.latitude), Number(place.longitude)) : null;
}

function getProvinceForPlaceName(name) {
    return getProvinceForPlace(resolvePlace(name));
}

function notifyPlaceSelection(place, sourceNode) {
    document.dispatchEvent(new CustomEvent("notitia:map-place", {
        detail: {
            place,
            gazetteerId: place?.gazetteerId || "",
            placeName: placeName(place),
            sourceNode
        }
    }));
}

function buildPlacesLayer() {
    placesLayer = L.layerGroup();
    allPlaceMarkers = [];
    let count = 0;

    for (const place of Data.getAllPlaces()) {
        const item = mappedPlace(place);
        if (!item) continue;
        const type = placeType(place);
        const marker = createPlaceMarker(item, placesLayer, placeMarkerStyle(place));

        // At closer zoom levels, show the normalized Latin place name.
        // The label deliberately comes from placeName(place), never Pleiades.
        bindLatinPlaceLabel(marker, place);

        allPlaceMarkers.push({ marker, type });
        count += 1;
    }

    placesLayer.addTo(map);
    return count;
}

// Independent, optional overlay. Fetch relative to this module so the path
// works both on Netlify and when the site is served from a subdirectory.
async function buildRoadsLayer() {
    const roadsUrl = new URL("../../data/roman_roads.geojson", import.meta.url);
    roadsLayer = L.geoJSON(null, {
        pane: "romanRoadsPane",
        interactive: false,
        style: {
            color: "#875b3a",
            weight: 2,
            opacity: 0.62,
            lineCap: "round",
            lineJoin: "round"
        }
    });

    try {
        const response = await fetch(roadsUrl);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (!data || data.type !== "FeatureCollection" || !Array.isArray(data.features)) {
            throw new Error("Invalid roads GeoJSON FeatureCollection");
        }
        roadsLayer.addData(data);
        console.log(`Roman roads loaded: ${data.features.length} segments`);
    } catch (error) {
        console.warn("Roman roads could not be loaded:", error);
    }
    // Deliberately do not add to map: unchecked by default.
    return roadsLayer;
}

async function init() {
    if (!document.getElementById("map")) {
        throw new Error("Map element #map was not found");
    }

    map = L.map("map").setView(DEFAULT_VIEW, DEFAULT_ZOOM);

    installPlaceLabelStyles();
    updatePlaceLabelVisibility();
    map.on("zoomend", updatePlaceLabelVisibility);

    map.createPane("searchResultsPane");
    map.getPane("searchResultsPane").style.zIndex = "640";
    map.createPane("selectedPlacePane");
    map.getPane("selectedPlacePane").style.zIndex = "650";

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        opacity: 0.58,
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    map.createPane("romanRoadsPane");
    map.getPane("romanRoadsPane").style.zIndex = "425";

    await loadProvinces();
    const provinceLayer = buildProvinceLayer(map, showProvince);
    const placeCount = buildPlacesLayer();
    const roadsOverlay = await buildRoadsLayer();

    L.control.layers(null, {
        Provinces: provinceLayer,
        Places: placesLayer,
        "Roman roads": roadsOverlay
    }, { collapsed: false }).addTo(map);

    addPlaceLegend(map);

    if (provinceLayer.getBounds().isValid()) {
        map.fitBounds(provinceLayer.getBounds(), { padding: [10, 10] });
    }

    requestAnimationFrame(() => map.invalidateSize());
    setStatus(`Map ready — ${placeCount} places`);
    console.log(`Provinces loaded: ${provinceFeatureCount()}`);
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
    showJurisdiction,
    showCommandStations,
    showProvince,
    showProvinceObjectIds,
    getProvinceForPlace,
    getProvinceForPlaceName,
    findProvince,
    resolvePlaceForContext
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
    showJurisdiction,
    showCommandStations,
    showProvince,
    showProvinceObjectIds,
    getProvinceForPlace,
    getProvinceForPlaceName,
    findProvince,
    resolvePlaceForContext
};
