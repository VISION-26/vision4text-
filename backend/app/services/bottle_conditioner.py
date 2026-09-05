"""Real-world camera conditioner and background isolator for Bottle inspection.

Adapts arbitrary phone camera, webcam, and internet photos of bottles to match
the MVTec AD studio dark backdrop ([12, 12, 14]) distribution used by EfficientAD
and PatchCore specialists.
"""
from typing import Any, Tuple
import numpy as np
from PIL import Image, ImageFilter, ImageOps


def _find_bottle_salient_box(small_gray: Image.Image) -> Tuple[int, int, int, int] | None:
    """Find the central vertical bottle structure using edge detection and aspect weighting."""
    gw, gh = small_gray.size
    arr = np.asarray(small_gray, dtype=np.float32)

    # Edge filter to find bottle contours
    edges = small_gray.filter(ImageFilter.FIND_EDGES)
    dilated = edges.filter(ImageFilter.MaxFilter(size=5))
    edge_arr = np.asarray(dilated, dtype=np.float32)

    # Prioritize center region vertically and horizontally
    Y, X = np.ogrid[:gh, :gw]
    cx, cy = gw / 2.0, gh / 2.0
    dist_sq = ((X - cx) / (gw * 0.40)) ** 2 + ((Y - cy) / (gh * 0.45)) ** 2
    center_weight = np.exp(-0.5 * dist_sq)
    weighted = edge_arr * center_weight

    thresh = float(np.percentile(weighted, 82))
    if thresh < 2.0:
        return None
    active = weighted >= thresh

    visited = np.zeros((gh, gw), dtype=bool)
    components = []

    for y in range(gh):
        for x in range(gw):
            if active[y, x] and not visited[y, x]:
                comp = []
                queue = [(y, x)]
                visited[y, x] = True
                while queue:
                    cy_curr, cx_curr = queue.pop(0)
                    comp.append((cx_curr, cy_curr))
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        ny, nx = cy_curr + dy, cx_curr + dx
                        if 0 <= ny < gh and 0 <= nx < gw and active[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            queue.append((ny, nx))
                if len(comp) >= 16:
                    xs = [p[0] for p in comp]
                    ys = [p[1] for p in comp]
                    min_x, max_x = min(xs), max(xs)
                    min_y, max_y = min(ys), max(ys)
                    bw = max_x - min_x + 1
                    bh = max_y - min_y + 1
                    # Bottles are typically taller than wide
                    aspect_score = min(2.0, float(bh) / max(1.0, bw))
                    cent_dist = np.hypot(np.mean(xs) - cx, np.mean(ys) - cy)
                    score = len(comp) * aspect_score / max(1.0, cent_dist)
                    components.append((score, (min_x, min_y, max_x, max_y)))

    if not components:
        return None

    components.sort(key=lambda item: item[0], reverse=True)
    # Merge top candidates if close
    top_box = components[0][1]
    if len(components) > 1 and components[1][0] > 0.4 * components[0][0]:
        b2 = components[1][1]
        top_box = (
            min(top_box[0], b2[0]),
            min(top_box[1], b2[1]),
            max(top_box[2], b2[2]),
            max(top_box[3], b2[3]),
        )
    return top_box


def condition_bottle_input(image: Image.Image) -> Tuple[Image.Image, dict[str, Any]]:
    """Isolate, center, and background-neutralize a Bottle for real-world photos.

    Preserves standard MVTec AD images untouched while making real phone, webcam,
    and internet images robust against background table disturbances.
    """
    orig_rgb = image.convert("RGB")
    orig_w, orig_h = orig_rgb.size
    arr = np.asarray(orig_rgb, dtype=np.float32)

    # 1. Check if image is already a clean studio MVTec image
    c_size = min(20, orig_w // 8, orig_h // 8)
    if c_size > 4:
        c1 = arr[:c_size, :c_size]
        c2 = arr[:c_size, -c_size:]
        c3 = arr[-c_size:, :c_size]
        c4 = arr[-c_size:, -c_size:]
        corners = np.concatenate([c1, c2, c3, c4], axis=0)
        if float(corners.mean()) < 28.0 and float(corners.std()) < 18.0:
            return orig_rgb.resize((256, 256), Image.Resampling.LANCZOS), {
                "roi_state": "studio_mvtec",
                "bbox": {"x": 0, "y": 0, "width": orig_w, "height": orig_h},
                "crop_side": max(orig_w, orig_h),
                "confidence": 1.0,
            }

    # 2. Downscale for structural analysis
    target_dim = 384
    scale = min(1.0, float(target_dim) / max(orig_w, orig_h))
    proc_w = max(32, int(round(orig_w * scale)))
    proc_h = max(32, int(round(orig_h * scale)))
    small = orig_rgb.resize((proc_w, proc_h), Image.Resampling.BILINEAR)
    gray = small.convert("L")

    bbox_small = _find_bottle_salient_box(gray)
    if bbox_small is None:
        pad_x = int(orig_w * 0.15)
        pad_y = int(orig_h * 0.10)
        bbox_orig = (pad_x, pad_y, orig_w - pad_x, orig_h - pad_y)
    else:
        bx0 = max(0, int(round(bbox_small[0] / scale)))
        by0 = max(0, int(round(bbox_small[1] / scale)))
        bx1 = min(orig_w, int(round(bbox_small[2] / scale)))
        by1 = min(orig_h, int(round(bbox_small[3] / scale)))
        bbox_orig = (bx0, by0, bx1, by1)

    bw = max(32, bbox_orig[2] - bbox_orig[0])
    bh = max(48, bbox_orig[3] - bbox_orig[1])
    cx = (bbox_orig[0] + bbox_orig[2]) // 2
    cy = (bbox_orig[1] + bbox_orig[3]) // 2

    # Canonical bottle extent: height-dominated
    bottle_extent = max(bh, int(bw * 1.4))
    side = int(round(bottle_extent * 1.30))
    side = max(side, 96)

    crop_x0 = cx - side // 2
    crop_y0 = cy - side // 2
    crop_x1 = crop_x0 + side
    crop_y1 = crop_y0 + side

    # Create MVTec neutral studio dark canvas (12, 12, 14)
    canvas = Image.new("RGB", (side, side), (12, 12, 14))

    src_x0 = max(0, crop_x0)
    src_y0 = max(0, crop_y0)
    src_x1 = min(orig_w, crop_x1)
    src_y1 = min(orig_h, crop_y1)

    if src_x1 > src_x0 and src_y1 > src_y0:
        patch = orig_rgb.crop((src_x0, src_y0, src_x1, src_y1))
        dst_x0 = src_x0 - crop_x0
        dst_y0 = src_y0 - crop_y0
        canvas.paste(patch, (dst_x0, dst_y0))

    # Elliptical soft vignette suited for elongated bottles
    rx = max(16.0, bw * 0.70)
    ry = max(24.0, bh * 0.65)
    r_inner = 1.05
    r_outer = 1.35

    Y_canvas, X_canvas = np.ogrid[:side, :side]
    normalized_dist = np.sqrt(((X_canvas - side / 2.0) / rx) ** 2 + ((Y_canvas - side / 2.0) / ry) ** 2)
    vignette = np.clip((r_outer - normalized_dist) / max(0.01, r_outer - r_inner), 0.0, 1.0).astype(np.float32)
    vignette = np.expand_dims(vignette, axis=-1)

    canvas_arr = np.asarray(canvas, dtype=np.float32)
    studio_bg = np.array([12.0, 12.0, 14.0], dtype=np.float32)
    blended = (canvas_arr * vignette + studio_bg * (1.0 - vignette)).astype(np.uint8)
    conditioned = Image.fromarray(blended, mode="RGB")

    # Gentle autocontrast
    conditioned = ImageOps.autocontrast(conditioned, cutoff=1)
    final_output = conditioned.resize((256, 256), Image.Resampling.LANCZOS)

    return final_output, {
        "roi_state": "isolated_real_camera",
        "bbox": {"x": int(bbox_orig[0]), "y": int(bbox_orig[1]), "width": int(bw), "height": int(bh)},
        "crop_side": side,
        "confidence": 0.95,
    }
