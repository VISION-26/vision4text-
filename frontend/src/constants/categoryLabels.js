export const CATEGORY_LABELS = {
    bottle: 'Top View Of Bottle',
    top_bottle_view: 'Top View Of Bottle',
    bottle_top_view: 'Top View Of Bottle',
    'top bottle view': 'Top View Of Bottle',
    'bottle/top bottle view': 'Top View Of Bottle',
    metal_nut: 'Top View Of Metal Nut',
    'metal nut': 'Top View Of Metal Nut',
    cable: 'Top View Of Cable',
    capsule: 'Top View Of Capsule',
    pill: 'Top View Of Pill',
    zipper: 'Zipper',
    wood: 'Wood',
    leather: 'Leather',
    toothbrush: 'Toothbrush',
    screw: 'Screw',
    carpet: 'Carpet',
    grid: 'Grid',
    hazelnut: 'Hazelnut',
    tile: 'Tile',
    transistor: 'Transistor',
};

export const displayCategory = (value) => {
    const raw = String(value || '').trim();
    if (!raw) return 'Unknown';
    const lower = raw.toLowerCase();
    if (CATEGORY_LABELS[lower]) return CATEGORY_LABELS[lower];
    const normalized = lower.replace(/[-_]/g, ' ');
    if (CATEGORY_LABELS[normalized]) return CATEGORY_LABELS[normalized];
    return raw.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
};

