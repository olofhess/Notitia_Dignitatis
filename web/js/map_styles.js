//
// Living Notitia
// map_styles.js
//

const PLACE_MARKER_STYLE = {
    radius: 3.8, weight: 1.1, color: "#111111", fillColor: "#555555",
    opacity: 0.95, fillOpacity: 0.82, bubblingMouseEvents: false
};
const PLACE_TYPE_STYLES = {

    dux: {
        radius: 4.5,
        weight: 1.2,
        color: "#003399",
        fillColor: "#0066ff",
        opacity: 0.95,
        fillOpacity: 0.85,
        bubblingMouseEvents: false
    },

    comes: {
        radius: 4.5,
        weight: 1.2,
        color: "#991b1b",
        fillColor: "#e53935",
        opacity: 0.95,
        fillOpacity: 0.85,
        bubblingMouseEvents: false
    },

    fabrica: {
        radius: 4.5,
        weight: 1.2,
        color: "#a65f00",
        fillColor: "#ffb000",
        opacity: 0.95,
        fillOpacity: 0.9,
        bubblingMouseEvents: false
    },

    office: {
        radius: 4.5,
        weight: 1.2,
        color: "#5b2182",
        fillColor: "#8e44ad",
        opacity: 0.95,
        fillOpacity: 0.85,
        bubblingMouseEvents: false
    },

    tribunus: {
        radius: 4.5,
        weight: 1.2,
        color: "#007f8f",
        fillColor: "#00cfe8",
        opacity: 0.95,
        fillOpacity: 0.88,
        bubblingMouseEvents: false
    },

    equites: {
        radius: 4.5,
        weight: 1.2,
        color: "#8a7800",
        fillColor: "#ffeb00",
        opacity: 0.95,
        fillOpacity: 0.9,
        bubblingMouseEvents: false
    },

    mixed: {
        radius: 5,
        weight: 1.4,
        color: "#006b3c",
        fillColor: "#00a651",
        opacity: 0.98,
        fillOpacity: 0.9,
        bubblingMouseEvents: false
    },

    other: PLACE_MARKER_STYLE
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

function addPlaceLegend(map, onTypeSelected = null) {
    const legend = L.control({ position: "bottomleft" });

    legend.onAdd = function () {
        const div = L.DomUtil.create("div", "place-legend");
        let activeType = null;

        const items = [
            ["dux", "#0066ff", "Dux"],
            ["comes", "#e53935", "Comes"],
            ["fabrica", "#ffb000", "Fabrica"],
            ["office", "#8e44ad", "Office"],
            ["tribunus", "#00cfe8", "Tribunus"],
            ["equites", "#ffeb00", "Equites"],
            ["mixed", "#00a651", "Mixed"],
            ["other", "#555555", "Other"]
        ];

        div.style.background = "rgba(255,255,255,0.94)";
        div.style.padding = "8px 10px";
        div.style.border = "1px solid #999";
        div.style.borderRadius = "5px";
        div.style.boxShadow = "0 1px 4px rgba(0,0,0,0.25)";
        div.style.font = "14px/1.35 Arial, sans-serif";
        div.style.color = "#222";

        const rows = new Map();

        function updateRows() {
            for (const [type, row] of rows) {
                const selected = activeType === type;
                row.style.opacity = activeType === null || selected ? "1" : "0.35";
                row.style.fontWeight = selected ? "700" : "400";
                row.setAttribute("aria-pressed", selected ? "true" : "false");
            }
        }

        for (const [type, color, label] of items) {
            const row = L.DomUtil.create("button", "place-legend-row", div);
            row.type = "button";
            row.dataset.placeType = type;
            row.setAttribute("aria-pressed", "false");
            row.title = `Show only ${label}; click again to show all`;
            row.style.display = "flex";
            row.style.alignItems = "center";
            row.style.gap = "7px";
            row.style.width = "100%";
            row.style.margin = "2px 0";
            row.style.padding = "2px 3px";
            row.style.border = "0";
            row.style.borderRadius = "3px";
            row.style.background = "transparent";
            row.style.color = "inherit";
            row.style.font = "inherit";
            row.style.textAlign = "left";
            row.style.cursor = "pointer";

            const dot = L.DomUtil.create("span", "", row);
            dot.style.width = "11px";
            dot.style.height = "11px";
            dot.style.borderRadius = "50%";
            dot.style.background = color;
            dot.style.border = "1px solid rgba(0,0,0,0.55)";
            dot.style.display = "inline-block";
            dot.style.flex = "0 0 11px";

            const text = L.DomUtil.create("span", "", row);
            text.textContent = label;

            L.DomEvent.on(row, "click", event => {
                L.DomEvent.stop(event);
                activeType = activeType === type ? null : type;
                updateRows();
                if (typeof onTypeSelected === "function") {
                    onTypeSelected(activeType, activeType ? label : "All");
                }
            });

            rows.set(type, row);
        }

        L.DomEvent.disableClickPropagation(div);
        L.DomEvent.disableScrollPropagation(div);
        updateRows();
        return div;
    };

    legend.addTo(map);
    return legend;
}

export {
    PLACE_MARKER_STYLE,
    PLACE_TYPE_STYLES,
    PROVINCE_PLACE_MARKER_STYLE,
    SEARCH_MARKER_STYLE,
    SELECTED_PLACE_STYLE,
    provinceStyle,
    selectedProvinceStyle,
    addPlaceLegend
};
