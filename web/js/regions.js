//
// Living Notitia
// regions.js
// Fixed mapping between Notitia administrative regions and GeoJSON province names.
//

export const REGIONS = {
    ITALIA: {
        label: "Italia",
        chapter: 2,
        aliases: ["Italia"],
        provinces: [
            "VENETIA ET HISTRIA",
            "AEMILIA ET LIGURIA",
            "FLAMINIA ET PICENUM",
            "TUSCIA ET UMBRIA",
            "PICENUM SUBURBICARIUM",
            "CAMPANIA",
            "SICILIA",
            "APULIA ET CALABRIA",
            "LUCANIA ET BRUTTII",
            "ALPES COTTIAE",
            "RAETIA",
            "SAMNIUM",
            "VALERIA",
            "SARDINIA",
            "CORSICA"
        ]
    },
    ILLYRICUM: {
        label: "Illyricum",
        chapter: 2,
        aliases: ["Illyricum"],
        provinces: [
            "PANNONIA INFERIOR",
            "SAVIA",
            "DALMATIA",
            "PANNONIA SUPERIOR",
            "NORICUM MEDITERRANEUM",
            "NORICUM RIPENSE"
        ]
    },
    AFRICA: {
        label: "Africa",
        chapter: 2,
        aliases: ["Africa"],
        provinces: [
            "BYZACENA",
            "NUMIDIA CIRTENSIS",
            "NUMIDIA MILITIANA",
            "MAURETANIA SITIFENSIS",
            "MAURETANIA CAESARIENSIS",
            "TRIPOLITANA"
        ]
    },
    ORIENS: {
        label: "Oriens",
        chapter: 2,
        aliases: ["Oriens"],
        provinces: [
            "PALAESTINA",
            "PHOENICE",
            "SYRIA COELE",
            "CILICIA",
            "CYPRUS",
            "ARABIA",
            "ISAURIA",
            "AUGUSTA LIBANENSIS",
            "AUGUSTA EUPHRATENSIS",
            "OSRHOENE",
            "MESOPOTAMIA"
        ]
    },
    AEGYPTUS: {
        label: "Aegypttus",
        chapter: 2,
        aliases: ["Aegypttus", "Aegyptus"],
        provinces: [
            "LIBYA SUPERIOR",
            "LIBYA INFERIOR",
            "THEBAIS",
            "AEGYPTUS HERCULIA",
            "AEGYPTUS IOVIA",
            "ARCADIA"
        ]
    },
    ASIANA: {
        label: "Asiana",
        chapter: 2,
        aliases: ["Asiana"],
        provinces: [
            "LYCIA ET PAMPHYLIA",
            "HELLESPONTUS",
            "LYDIA",
            "PISIDIA",
            "LYCAONIA",
            "PHRYGIA I",
            "PHRYGIA II",
            "CARIA",
            "INSULAE"
        ]
    },
    PONTICA: {
        label: "Pontica",
        chapter: 2,
        aliases: ["Pontica"],
        provinces: [
            "GALATIA",
            "BITHYNIA",
            "HONORIAS",
            "CAPPADOCIA",
            "PONTUS POLEMONIACUS",
            "DIOSPONTUS",
            "ARMENIA MINOR"
        ]
    },
    THRACIA: {
        label: "Thracia",
        chapter: 2,
        aliases: ["Thracia"],
        provinces: [
            "EUROPA",
            "THRACIA",
            "HAEMIMONTUS",
            "RHODOPE",
            "MOESIA INFERIOR",
            "SCYTHIA"
        ]
    },
    HISPANIA: {
        label: "Hispania",
        chapter: 3,
        aliases: ["Hispaniae", "Hispaniarum VII", "Hispania"],
        provinces: [
            "BAETICA",
            "LUSITANIA",
            "GALLAECIA",
            "TARRACONENSIS",
            "CARTBAGINIENSIS",
            "MAURETANIA TINGITANA"
        ]
    },
    SEPTEM_PROVINCIAE: {
        label: "Septem provinciae",
        chapter: 3,
        aliases: [
            "Septem provinciae",
            "Septem provinciarum XVII",
            "Gallia",
            "Galliae"
        ],
        provinces: [
            "VIENNENSIS",
            "LUGDUNENSIS I",
            "GERMANIA I",
            "GERMANIA II",
            "BELGICA I",
            "BELGICA II",
            "ALPES MARITIMAE",
            "ALPES GRAIAE ET POENINAE",
            "SEQUANIA",
            "AQUITANIA I",
            "AQUITANIA II",
            "NOVEM POPULI",
            "NARBONENSIS I",
            "NARBONENSIS II",
            "LUGDUNENSIS II"
        ]
    },
    BRITANNIA: {
        label: "Britannia",
        chapter: 3,
        aliases: ["Britanniae", "Britanniarum V", "Britannia"],
        provinces: [
            "BRITANNIAE I AND II"
        ]
    },
    MACEDONIA: {
        label: "Macedonia",
        chapter: 3,
        aliases: ["Macedonia", "Provinciae Macedoniae sex"],
        provinces: [
            "ACHAIA",
            "MACEDONIA",
            "CRETA",
            "THESSALIA",
            "EPIRUS VETUS",
            "EPIRUS NOVA"
        ]
    },
    DACIA: {
        label: "Dacia",
        chapter: 3,
        aliases: ["Dacia", "Provinciae Daciae quinque"],
        provinces: [
            "DACIA MEDITERRANEA",
            "DACIA RIPENSIS",
            "MOESIA SUPERIOR",
            "DARDANIA",
            "PRAEVALITANA"
        ]
    }
};

function normalizeLabel(value) {
    return String(value || "")
        .replace(/\s+/g, " ")
        .replace(/\.$/, "")
        .trim()
        .toLowerCase();
}

export function regionKeyForNavigation(chapter, label) {
    const wanted = normalizeLabel(label);

    for (const [key, region] of Object.entries(REGIONS)) {
        if (region.chapter !== chapter) {
            continue;
        }

        if (region.aliases.some(alias => normalizeLabel(alias) === wanted)) {
            return key;
        }
    }

    return null;
}
