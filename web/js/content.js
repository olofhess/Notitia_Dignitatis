// Content adapter. The Gazetteer is loaded once by Data; no name is a unique key.
import Data from './data.js';

const Content = {
    gazetteer: [],
    context: [],
    gazetteerByName: new Map(),
    contextByName: new Map(),
    contextById: new Map(),
    async initialize() {
        this.gazetteer = Data.getAllRecords();
        this.gazetteerByName = new Map();
        for (const row of this.gazetteer) {
            const key = String(row.placeName || '').trim();
            if (!this.gazetteerByName.has(key)) this.gazetteerByName.set(key, []);
            this.gazetteerByName.get(key).push(row);
        }
        const response = await fetch('../csv/PlaceContext.csv', {cache:'no-store'});
        if (!response.ok) throw new Error(`Could not load PlaceContext.csv: HTTP ${response.status}`);
        this.context = this.parseCSV(await response.text());
        this.contextByName = new Map();
        this.contextById = new Map();
        for (const row of this.context) {
            const key = String(row.placeName || '').trim();
            if (!this.contextByName.has(key)) this.contextByName.set(key, []);
            this.contextByName.get(key).push(row);
            if (row.contextId) this.contextById.set(row.contextId, row);
        }
    },
    parseCSV(text) {
        // Reuse the same quote-aware CSV rules as Data, including embedded newlines.
        const rows = []; let fields = [], value = '', quoted = false;
        const commitField = () => { fields.push(value); value = ''; };
        const commitRow = () => { commitField(); rows.push(fields); fields = []; };
        text = String(text || '').replace(/^\uFEFF/, '');
        for (let i = 0; i < text.length; i++) {
            const ch = text[i];
            if (ch === '"') { if (quoted && text[i+1] === '"') {value+='"';i++;} else quoted=!quoted; }
            else if (ch === ',' && !quoted) commitField();
            else if ((ch === '\n' || ch === '\r') && !quoted) {
                if (ch === '\r' && text[i+1] === '\n') i++;
                commitRow();
            } else value += ch;
        }
        if (value || fields.length) commitRow();
        const headers = rows.shift() || [];
        return rows.filter(row => row.some(v => v !== '')).map(row =>
            Object.fromEntries(headers.map((h,i) => [h.trim(), (row[i] || '').trim()])));
    },
    getPlace(name) { return Data.getPlace(name); },
    getPlacesByName(name) { return Data.getPlacesByName(name); },
    getPlaceById(id) { return Data.getPlaceById(id); },
    getContext(name) { return this.contextByName.get(String(name || '').trim()) || []; },
    getContextById(id) { return this.contextById.get(id) || null; }
};
export default Content;
