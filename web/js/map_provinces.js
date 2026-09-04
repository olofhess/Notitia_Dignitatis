//
// Living Notitia
// map_provinces.js
//
// Province GeoJSON, lookup and selection helpers extracted from map.js.
// Behaviour is intentionally unchanged.
//

import {
    provinceStyle,
    selectedProvinceStyle
} from "./map_styles.js";

const PROVINCE_FILE = "../data/provinces.geojson";

let provinceGeoJSON = null;
let provinceLayer = null;
let selectedProvinceLayers = [];

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

async function loadProvinces() {
    const response = await fetch(PROVINCE_FILE, { cache: "no-store" });
    if (!response.ok) {
        throw new Error(`Could not load ${PROVINCE_FILE}: HTTP ${response.status}`);
    }
    provinceGeoJSON = await response.json();
    return provinceGeoJSON;
}

function buildProvinceLayer(map, onProvinceClick) {
    provinceLayer = L.geoJSON(provinceGeoJSON, {
        style: provinceStyle,
        onEachFeature(feature, layer) {
            layer.bindTooltip(provinceName(feature));
            if (typeof onProvinceClick === "function") {
                layer.on("click", () => onProvinceClick(feature));
            }
        }
    }).addTo(map);

    return provinceLayer;
}

function getProvinceLayer() {
    return provinceLayer;
}

function provinceFeatureCount() {
    return provinceGeoJSON?.features?.length || 0;
}

function clearProvince() {
    if (provinceLayer) {
        for (const layer of selectedProvinceLayers) {
            provinceLayer.resetStyle(layer);
        }
    }
    selectedProvinceLayers = [];
}

function selectProvinceLayers(layers) {
    const selected = Array.isArray(layers) ? layers : [];

    for (const layer of selected) {
        layer.setStyle(selectedProvinceStyle());
        selectedProvinceLayers.push(layer);
    }

    return selected;
}

function highlightProvince(feature) {
    clearProvince();

    if (!feature || !provinceLayer) {
        return [];
    }

    const layers = [];

    provinceLayer.eachLayer(layer => {
        if (layer.feature !== feature) return;
        layer.setStyle(selectedProvinceStyle());
        selectedProvinceLayers.push(layer);
        layers.push(layer);
    });

    return layers;
}

function findProvince(latitude, longitude) {
    if (!provinceGeoJSON) return null;

    const point = turf.point([
        Number(longitude),
        Number(latitude)
    ]);

    for (const feature of provinceGeoJSON.features || []) {
        const type = feature?.geometry?.type;

        if (
            type !== "Polygon" &&
            type !== "MultiPolygon"
        ) {
            continue;
        }

        if (turf.booleanPointInPolygon(point, feature)) {
            return feature;
        }
    }

    return null;
}

function layersForProvinceObjectIds(values) {
    const input = Array.isArray(values) ? values : [values];
    const wanted = new Set(
        input
            .map(Number)
            .filter(Number.isFinite)
    );

    if (!wanted.size || !provinceLayer) {
        return [];
    }

    const layers = [];

    provinceLayer.eachLayer(layer => {
        if (wanted.has(provinceObjectId(layer.feature))) {
            layers.push(layer);
        }
    });

    return layers;
}

function layersForProvinceNames(values) {
    const input = Array.isArray(values) ? values : [values];
    const wanted = new Set(
        input
            .map(normalize)
            .filter(Boolean)
    );

    if (!wanted.size || !provinceLayer) {
        return [];
    }

    const layers = [];

    provinceLayer.eachLayer(layer => {
        if (wanted.has(normalize(provinceName(layer.feature)))) {
            layers.push(layer);
        }
    });

    return layers;
}

export {
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
};
