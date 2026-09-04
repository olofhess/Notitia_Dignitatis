//
// Living Notitia
// map_jurisdictions.js
//
// Resolves territorial jurisdictions that are not physical place points.
// Territorial jurisdiction resolver.
// Step 5 adds the territorial comites immediately above Rationales.
//

import { REGIONS } from "./regions.js";
import * as ProvinceGazetteer from "./province_gazetteer.js";

function clean(value) {
    return String(value || "")
        .replace(/\s+/g, " ")
        .replace(/[.:;]+$/, "")
        .trim();
}

function normalize(value) {
    return clean(value).toLowerCase();
}

function directTitle(node) {
    if (!node) return "";
    const title = Array.from(node.children || [])
        .find(child => child.tagName === "title");
    return clean(title?.textContent);
}

function rationalesGroup(node) {
    let current = node;

    while (current) {
        if (
            current.tagName === "group" &&
            normalize(directTitle(current)) === "rationales"
        ) {
            return current;
        }

        if (current.tagName === "chapter" || current.tagName === "document") {
            break;
        }

        current = current.parentElement;
    }

    return null;
}

function ancestorChapter(node) {
    let current = node;

    while (current) {
        if (current.tagName === "chapter") return current;
        current = current.parentElement;
    }

    return null;
}

function isSacraeLargitionesChapter(node) {
    const title = normalize(directTitle(ancestorChapter(node)));
    return title.includes("comitis sacrarum largitionum");
}

function largitionesGroup(node) {
    if (!isSacraeLargitionesChapter(node)) return null;

    let current = node;
    while (current) {
        if (current.tagName === "group") {
            const title = normalize(directTitle(current));
            if (title.startsWith("sub dispositione") && title.includes("largition")) {
                return current;
            }
        }
        if (current.tagName === "chapter" || current.tagName === "document") break;
        current = current.parentElement;
    }

    return null;
}

function provinceNamesForCanonical(values) {
    const input = Array.isArray(values) ? values : [values];
    const names = input.flatMap(value => ProvinceGazetteer.geojsonNames(value));
    return [...new Set(names.filter(Boolean))];
}

function regionProvinceNames(key) {
    return [...new Set((REGIONS[key]?.provinces || []).filter(Boolean))];
}

function entrySpec(node) {
    const text = clean(node?.textContent);
    const wanted = normalize(text);

    if (wanted.includes("pannoniae secundae")) {
        return {
            label: text,
            provinceNames: provinceNamesForCanonical([
                "Pannonia Secunda",
                "Dalmatia",
                "Savia"
            ])
        };
    }

    if (wanted.includes("pannoniae prima")) {
        return {
            label: text,
            provinceNames: provinceNamesForCanonical([
                "Pannonia Prima",
                "Valeria",
                "Noricum Mediterraneum",
                "Noricum Ripense"
            ])
        };
    }

    if (wanted.includes("summarum italiae")) {
        return {
            label: text,
            provinceNames: regionProvinceNames("ITALIA")
        };
    }

    if (wanted.includes("urbis romae")) {
        return {
            label: text,
            provinceNames: [],
            note: "jurisdiction recorded, but no area polygon is assigned"
        };
    }

    if (wanted.includes("trum provinciarum")) {
        return {
            label: text,
            provinceNames: provinceNamesForCanonical([
                "Sicilia",
                "Sardinia",
                "Corsica"
            ])
        };
    }

    if (wanted.includes("summarum africae")) {
        return {
            label: text,
            provinceNames: regionProvinceNames("AFRICA")
        };
    }

    if (
        wanted.includes("summarum nimidiae") ||
        wanted.includes("summarum numidiae")
    ) {
        return {
            label: text,
            provinceNames: provinceNamesForCanonical("Numidia")
        };
    }

    if (wanted.includes("summarum hispaniae")) {
        return {
            label: text,
            provinceNames: regionProvinceNames("HISPANIA")
        };
    }

    if (wanted.includes("quinque provinciarum")) {
        return {
            label: text,
            provinceNames: [],
            note: "jurisdiction recorded, but its five provinces are not yet resolved"
        };
    }

    if (wanted.includes("summarum galliarum")) {
        return {
            label: text,
            provinceNames: regionProvinceNames("SEPTEM_PROVINCIAE")
        };
    }

    if (wanted.includes("summarum britanniarum")) {
        return {
            label: text,
            provinceNames: regionProvinceNames("BRITANNIA")
        };
    }

    return null;
}

function groupSpec(group) {
    const provinceNames = [];
    const seen = new Set();
    let unresolved = 0;

    for (const child of Array.from(group.children || [])) {
        if (child.tagName === "title") continue;

        const spec = entrySpec(child);
        if (!spec) continue;

        if (!spec.provinceNames.length) {
            unresolved += 1;
            continue;
        }

        for (const name of spec.provinceNames) {
            if (seen.has(name)) continue;
            seen.add(name);
            provinceNames.push(name);
        }
    }

    return {
        label: "Rationales",
        provinceNames,
        unresolved
    };
}

function largitionesEntrySpec(node) {
    const text = clean(node?.textContent);
    const wanted = normalize(text);

    if (wanted.includes("largitionum per illyricum")) {
        return {
            label: text,
            provinceNames: regionProvinceNames("ILLYRICUM")
        };
    }

    if (wanted.includes("largitionum italicianarum")) {
        return {
            label: text,
            provinceNames: regionProvinceNames("ITALIA")
        };
    }

    if (wanted.includes("titulorum largitionalium per africam")) {
        return {
            label: text,
            provinceNames: regionProvinceNames("AFRICA")
        };
    }

    return null;
}

function largitionesGroupSpec(group) {
    const provinceNames = [];
    const seen = new Set();
    let mapped = 0;
    let unresolved = 0;

    for (const child of Array.from(group.children || [])) {
        if (child.tagName === "title") continue;

        const spec = largitionesEntrySpec(child);
        if (!spec) {
            unresolved += 1;
            continue;
        }

        mapped += 1;
        for (const name of spec.provinceNames) {
            if (seen.has(name)) continue;
            seen.add(name);
            provinceNames.push(name);
        }
    }

    return {
        label: clean(directTitle(group)) || "Sacrae largitiones",
        provinceNames,
        unresolved,
        mapped
    };
}

function resolveJurisdiction(node) {
    const rationales = rationalesGroup(node);
    if (rationales) {
        if (node === rationales) return groupSpec(rationales);
        return entrySpec(node);
    }

    const largitiones = largitionesGroup(node);
    if (largitiones) {
        if (node === largitiones) return largitionesGroupSpec(largitiones);
        return largitionesEntrySpec(node);
    }

    return null;
}

export {
    resolveJurisdiction
};
