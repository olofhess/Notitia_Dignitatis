// Deterministic geographic resolution. Never guess from a homonymous name.
import Data from './data.js';

export function resolvePlace({gazetteerId, name, expectedPleiadesId, allowedIds} = {}) {
    if (gazetteerId) {
        const match = Data.getPlaceById(gazetteerId);
        return match ? {status:'identified',place:match,method:'gazetteerId'} :
            {status:'unresolved',place:null,reason:'Unknown Gazetteer ID'};
    }
    let candidates = Data.getPlacesByName(name);
    if (expectedPleiadesId) candidates = candidates.filter(p =>
        String(p.pleiadesId) === String(expectedPleiadesId));
    if (allowedIds) {
        const allowed = new Set(allowedIds.map(String));
        candidates = candidates.filter(p => allowed.has(String(p.gazetteerId)));
    }
    if (candidates.length === 1) return {status:'identified',place:candidates[0],method:'uniqueName'};
    if (!candidates.length) return {status:'unresolved',place:null,reason:'No matching place'};
    return {status:'ambiguous',place:null,candidates,reason:'Multiple distinct geographical sites'};
}
