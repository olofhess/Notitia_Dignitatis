const FILE = "../csv/PlaceGazetteer.csv";
const OCCURRENCE_FILE = "../csv/PlaceOccurrence_context.csv";

let places = [];
let allRecords = [];
let byId = new Map();
let byName = new Map();
let placeMentions = [];

function parseCSV(text) {
    const rows = [];
    let row = [];
    let field = "";
    let quoted = false;

    for (let i = 0; i < text.length; i++) {
        const c = text[i];

        if (c === '"') {
            if (quoted && text[i + 1] === '"') {
                field += '"';
                i++;
            } else {
                quoted = !quoted;
            }
        } else if (c === "," && !quoted) {
            row.push(field);
            field = "";
        } else if ((c === "\n" || c === "\r") && !quoted) {
            if (c === "\r" && text[i + 1] === "\n") i++;
            row.push(field);
            rows.push(row);
            row = [];
            field = "";
        } else {
            field += c;
        }
    }

    if (field || row.length) {
        row.push(field);
        rows.push(row);
    }

    const headers = rows.shift() || [];

    return rows.map(values =>
        Object.fromEntries(
            headers.map((h, i) => [h.trim(), values[i] ?? ""])
        )
    );
}

async function loadAll() {
    const [response, occurrenceResponse] = await Promise.all([
        fetch(FILE, { cache: "no-store" }),
        fetch(OCCURRENCE_FILE, { cache: "no-store" })
    ]);

    if (!response.ok) {
        throw new Error(`Could not load ${FILE}: HTTP ${response.status}`);
    }
    if (!occurrenceResponse.ok) {
        throw new Error(`Could not load ${OCCURRENCE_FILE}: HTTP ${occurrenceResponse.status}`);
    }

    const rows = parseCSV(await response.text());
    placeMentions = parseCSV(await occurrenceResponse.text());

    allRecords = rows.map(row => {
        const lat = String(row.latitude ?? '').trim();
        const lon = String(row.longitude ?? '').trim();
        const latitude = lat === '' ? null : Number(lat);
        const longitude = lon === '' ? null : Number(lon);
        return { ...row, latitude: Number.isFinite(latitude) ? latitude : null,
            longitude: Number.isFinite(longitude) ? longitude : null };
    });
    byId = new Map();
    byName = new Map();
    for (const record of allRecords) {
        const id = String(record.gazetteerId || '').trim();
        if (id) {
            if (byId.has(id)) console.warn('Duplicate gazetteerId:', id);
            byId.set(id, record);
        }
        for (const name of [record.placeName, record.sourcePlaceName, record.pleiadesName]) {
            const key = normalizePlaceName(name);
            if (!key) continue;
            if (!byName.has(key)) byName.set(key, []);
            if (!byName.get(key).includes(record)) byName.get(key).push(record);
        }
    }
    // Backwards compatibility: existing map code expects only mapped places.
    places = allRecords.filter(row => row.latitude !== null && row.longitude !== null);

    console.log(`Places loaded: ${places.length}`);

    return places;
}

function getAllPlaces() {
    return places;
}

function getAllRecords() { return allRecords; }
function getPlaceById(id) { return byId.get(String(id || '').trim()) || null; }
function getPlacesByName(name) { return [...(byName.get(normalizePlaceName(name)) || [])]; }
function getPlace(placeName) {
    // Never silently choose between homonymous geographical sites.
    const hits = getPlacesByName(placeName);
    return hits.length === 1 ? hits[0] : null;
}

function getPlaceMentionsByProvince(provinceName) {
    const wanted = String(provinceName || "").trim().toLowerCase();

    return placeMentions.filter(row =>
        [
            row.hardProvince,
            row.softProvince,
            row.declaredProvince,
            row.expectedProvince
        ].some(value =>
            String(value || "").trim().toLowerCase() === wanted
        )
    );
}

function normalizePlaceName(value) {
    return String(value || "").trim().toLowerCase();
}

function placeAliases(value) {
    const fields = [
        "placeName",
        "sourcePlaceName",
        "pleiadesName",
        "name",
        "candidate"
    ];

    const aliases = new Set();

    if (value && typeof value === "object") {
        for (const field of fields) {
            const name = normalizePlaceName(value[field]);
            if (name) aliases.add(name);
        }
    } else {
        const name = normalizePlaceName(value);
        if (name) aliases.add(name);
    }

    const seedNames = new Set(aliases);

    const matchedPlaces = places.filter(place =>
        fields.some(field =>
            seedNames.has(normalizePlaceName(place[field]))
        )
    );

    const canonicalNames = new Set(
        matchedPlaces
            .map(place => normalizePlaceName(place.placeName))
            .filter(Boolean)
    );

    for (const place of places) {
        const canonical = normalizePlaceName(place.placeName);

        if (
            matchedPlaces.includes(place) ||
            (canonical && canonicalNames.has(canonical))
        ) {
            for (const field of fields) {
                const name = normalizePlaceName(place[field]);
                if (name) aliases.add(name);
            }
        }
    }

    return aliases;
}

function getPlaceMentions(value) {
    const aliases = placeAliases(value);
    const ids = new Set();

    // Gazetteer IDs are more reliable than names (especially for adjectival
    // administrative forms in the Notitia).
    if (value && typeof value === "object") {
        const id = String(value.gazetteerId || "").trim();
        if (id) ids.add(id);
    }
    for (const alias of aliases) {
        for (const place of byName.get(alias) || []) {
            const id = String(place.gazetteerId || "").trim();
            if (id) ids.add(id);
        }
    }

    return placeMentions.filter(row => {
        // PlaceOccurrence_context.csv uses source_form and gazetteer_ids,
        // not placeName. Multiple IDs may be separated by punctuation.
        const rowIds = String(row.gazetteer_ids || "")
            .split(/[;,|\s]+/).map(id => id.trim()).filter(Boolean);
        if (rowIds.some(id => ids.has(id))) return true;
        const rowName = normalizePlaceName(row.source_form || row.placeName);
        return !!rowName && aliases.has(rowName);
    });
}

const Data = {
    loadAll,
    getAllPlaces,
    getAllRecords,
    getPlaceById,
    getPlacesByName,
    getPlace,
    getPlaceMentionsByProvince,
    getPlaceMentions
};

window.Data = Data;

export default Data;
export {
    loadAll,
    getAllPlaces,
    getAllRecords,
    getPlaceById,
    getPlacesByName,
    getPlace,
    getPlaceMentionsByProvince,
    getPlaceMentions
};