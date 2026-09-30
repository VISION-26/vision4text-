export const CATEGORY_LABELS = {
    bottle: 'Top View of Bottle',
    metal_nut: 'Metal Nut',
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
    const key = String(value || '').trim();
    if (!key) return 'Unknown';
    if (CATEGORY_LABELS[key]) return CATEGORY_LABELS[key];
    return key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
};
