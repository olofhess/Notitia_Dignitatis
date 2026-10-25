// Shared selection store. Display components subscribe instead of controlling one another.
let xml = null;
let selection = null;
const listeners = new Set();
export function initialize(document) { xml = document; }
export function document() { return xml; }
export function select(node, metadata = {}) {
    selection = { node, ...metadata };
    for (const callback of [...listeners]) callback(selection);
}
export function selected() { return selection?.node ?? null; }
export function currentSelection() { return selection; }
export function subscribe(callback) {
    listeners.add(callback);
    return () => listeners.delete(callback);
}
