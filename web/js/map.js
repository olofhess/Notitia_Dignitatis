//
// Living Notitia
// map.js
//

import Data from "./data.js";
import { REGIONS } from "./regions.js";
import {
    placeName,
    mappedPlace,
    placeKey,
    uniqueMappedPlaces,
    resolvePlace,
    hasPlace,
    findPlaceSourceNode,
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


const DEFAULT_VIEW = [41, 15];
const DEFAULT_ZOOM = 4;
const PLACE_ZOOM = 8;

let map = null;
let placesLayer = null;
let selectedPlaceMarker = null;
let searchResultsLayer = null;
let provincePlacesLayer = null;
let placesLayerWasVisibleBeforeSearch = null;
let placesLayerWasVisibleBeforeProvinceFocus = null;

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

function buildPlacesLayer() {
    placesLayer = L.layerGroup();
    let count = 0;

    for (const place of Data.getAllPlaces()) {
        const item = mappedPlace(place);
        if (!item) continue;
        createPlaceMarker(item, placesLayer, placeMarkerStyle(place));
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
    const provinceLayer = buildProvinceLayer(map, showProvince);
    const placeCount = buildPlacesLayer();

    L.control.layers(null, {
        Provinces: provinceLayer,
        Places: placesLayer
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
    showJurisdiction,
    showProvince,
    showProvinceObjectIds,
    getProvinceForPlace,
    getProvinceForPlaceName,
    findProvince
};
