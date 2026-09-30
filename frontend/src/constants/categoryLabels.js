export const CATEGORY_LABELS = {
    bottle: 'Top View of Bottle',
    top_bottle_view: 'Top View of Bottle',
    bottle_top_view: 'Top View of Bottle',
    'top bottle view': 'Top View of Bottle',
    'bottle/top bottle view': 'Top View of Bottle',
    metal_nut: 'Metal Nut',
    'metal nut': 'Metal Nut',
    cable: 'Cable',
    capsule: 'Capsule',
    pill: 'Pill',
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

