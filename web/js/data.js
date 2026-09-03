const FILE = "../csv/PlaceGazetteer.csv";
const OCCURRENCE_FILE = "../csv/PlaceOccurrence_context.csv";

let places = [];
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

    const headers = rows.shift();

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

    places = rows
        .filter(row =>
            row.latitude.trim() !== "" &&
            row.longitude.trim() !== ""
        )
        .map(row => ({
            ...row,
            latitude: Number(row.latitude),
            longitude: Number(row.longitude)
        }));

    console.log(`Places loaded: ${places.length}`);

    return places;
}

function getAllPlaces() {
    return places;
}

function getPlace(placeName) {
    return places.find(place => place.placeName === placeName) || null;
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

    if (!aliases.size) {
        return [];
    }

    return placeMentions.filter(row =>
        aliases.has(normalizePlaceName(row.placeName))
    );
}

const Data = {
    loadAll,
    getAllPlaces,
    getPlace,
    getPlaceMentionsByProvince,
    getPlaceMentions
};

window.Data = Data;

export default Data;
export {
    loadAll,
    getAllPlaces,
    getPlace,
    getPlaceMentionsByProvince,
    getPlaceMentions
};