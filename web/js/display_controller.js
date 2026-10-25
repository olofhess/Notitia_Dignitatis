// Coordinates the three views from one selection store.
import * as State from './state.js';
import * as Inspector from './inspector.js';
import * as Map from './map.js';

export function initialize() {
    return State.subscribe(({node, updateMap = true, mapPlace = null, sourceNode = null}) => {
        if (!node) return;
        Inspector.show(node);
        if (mapPlace && typeof Inspector.showMapPlace === 'function') {
            Inspector.showMapPlace(mapPlace, sourceNode || node);
        }
        if (!updateMap) return;
        const label = (node.querySelector?.(':scope > title')?.textContent || node.textContent || '').trim();
        if (node.tagName === 'chapter' && /^dux\b/i.test(label)) {
            Map.showCommandStations(node);
            return;
        }
        // Existing non-command navigation remains in nav.js for this migration.
    });
}
