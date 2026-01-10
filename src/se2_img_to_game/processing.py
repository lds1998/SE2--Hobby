# Core logic for Image to Game Block conversion
import numpy as np
from PIL import Image, ImageDraw

# Constants
UNIT_SIZE = 0.25 # meters

def calculate_target_dimensions(image_size, z_meters, y_meters=None):
    """
    Calculates the target grid dimensions where 1 unit = 0.25 meters.
    """
    target_height_units = int(z_meters / UNIT_SIZE)

    if y_meters is not None and y_meters > 0:
         target_width_units = int(y_meters / UNIT_SIZE)
    else:
        aspect_ratio = image_size[0] / image_size[1]
        target_width_units = int(target_height_units * aspect_ratio)

    return max(1, target_width_units), max(1, target_height_units)

def resize_image_to_grid(image, target_shape):
    """
    Resizes image to target dimensions using high-quality resampling.
    """
    return image.resize(target_shape, resample=Image.Resampling.LANCZOS)

def compute_masks(image_resized, color_threshold=30.0, alpha_threshold=128):
    """
    Computes the boolean mask of where the object is.
    Returns:
        inside_mask: boolean 2D array (True = inside object)
        img_arr: numpy array of the image (RGB or RGBA)
    """
    img_arr = np.array(image_resized)

    # Handle Alpha
    if image_resized.mode == 'RGBA':
        alpha = img_arr[:, :, 3]
        is_opaque = alpha > alpha_threshold
        # Create a "Luminance" view for thresholding
        # Standard Rec 601: 0.299 R + 0.587 G + 0.114 B
        rgb = img_arr[:, :, :3]
        lum = np.dot(rgb, [0.299, 0.587, 0.114])
        is_dark = lum < 250 # Hardcoded shape detection from original?

        inside_mask = is_dark & is_opaque
    else:
        # RGB or L
        gray = image_resized.convert("L")
        gray_arr = np.array(gray)
        inside_mask = gray_arr < 250

    return inside_mask, img_arr

def compute_edge_mask(inside_mask, distance=1):
    """
    Identifies 'edge' pixels within the inside_mask.
    """
    # Pad to handle borders
    p = np.pad(inside_mask, 1, mode='constant', constant_values=False)

    # Slice center
    center = p[1:-1, 1:-1]
    n1 = p[0:-2, 1:-1] # Up
    n2 = p[2:, 1:-1]   # Down
    n3 = p[1:-1, 0:-2] # Left
    n4 = p[1:-1, 2:]   # Right

    core = n1 & n2 & n3 & n4 # Only True if all neighbors are True
    edge = center & (~core) # Inside but not Core

    return edge

def generate_blocks(image_pil, allowed_types, scale, threshold=30.0, alpha_thresh=128, edge_pref=None, width_m=None):
    """
    Generates blocks.
    edge_pref: If set (e.g., "50cm"), any block size LARGER than this
               will be restricted from the 'edge' zone.
    width_m: Optional forced width in meters (X axis).
    """
    # 1. Scaling
    real_z = scale * image_pil.height # Length/Height in UI

    # Use explicitly provided Width X if available
    target_w, target_h = calculate_target_dimensions(image_pil.size, real_z, width_m)

    img_resized = resize_image_to_grid(image_pil, (target_w, target_h))

    # 2. Masks
    inside_mask, img_arr = compute_masks(img_resized, alpha_threshold=alpha_thresh)

    # 3. Edge Logic
    size_mapping = {"25cm": 1, "50cm": 2, "2.5m": 10}

    edge_mask = None
    if edge_pref and edge_pref in size_mapping:
        edge_mask = compute_edge_mask(inside_mask)

    # 4. Packing
    merged = np.zeros_like(inside_mask, dtype=bool)
    blocks = []

    sorted_types = sorted(allowed_types, key=lambda t: size_mapping[t], reverse=True)

    if img_arr.shape[-1] == 4:
        img_rgb = img_arr[:, :, :3]
    else:
        img_rgb = img_arr

    for b_type in sorted_types:
        bs = size_mapping[b_type]

        avoid_edge = False
        if edge_mask is not None and edge_pref:
            if bs > size_mapping[edge_pref]:
                avoid_edge = True

        if bs == 1:
            candidates = inside_mask & (~merged)
            ys, xs = np.where(candidates)
            for i in range(len(ys)):
                r, c = ys[i], xs[i]
                color = img_rgb[r, c]
                blocks.append({
                    "block_type": b_type,
                    "x": c, "y": r, "w": 1, "h": 1,
                    "color": color
                })
                merged[r, c] = True
            continue

        for r in range(0, target_h - bs + 1, bs):
            for c in range(0, target_w - bs + 1, bs):
                if np.any(merged[r:r+bs, c:c+bs]):
                    continue
                if not np.all(inside_mask[r:r+bs, c:c+bs]):
                    continue
                if avoid_edge:
                    if np.any(edge_mask[r:r+bs, c:c+bs]):
                        continue

                region = img_rgb[r:r+bs, c:c+bs]
                avg = np.mean(region, axis=(0,1))
                if threshold < 255:
                    ptp = np.ptp(region, axis=(0,1))
                    if np.any(ptp > threshold * 2):
                         continue

                merged[r:r+bs, c:c+bs] = True
                blocks.append({
                    "block_type": b_type,
                    "x": c, "y": r, "w": bs, "h": bs,
                    "color": avg
                })

    return blocks, target_w, target_h

def generate_instructions(blocks, z_offset_meters=0.0):
    """
    Converts grid blocks to physical instructions.
    """
    instructions = []
    thickness_map = {"25cm": 0.25, "50cm": 0.50, "2.5m": 2.50}

    for b in blocks:
        cx = (b['x'] + b['w'] / 2.0) * UNIT_SIZE
        cz = (b['y'] + b['h'] / 2.0) * UNIT_SIZE

        width_m = b['w'] * UNIT_SIZE
        height_m = b['h'] * UNIT_SIZE

        instructions.append({
            "block_type": b['block_type'],
            "position": {"x": round(cx, 2), "y": round(z_offset_meters, 2), "z": round(cz, 2)},
            "size": {"width": round(width_m, 2), "depth": round(height_m, 2), "height": thickness_map.get(b['block_type'], 0.25)},
            "color": b['color'].tolist()
        })
    return instructions

def generate_preview(target_w, target_h, blocks):
    img = Image.new("RGB", (target_w, target_h), "white")
    draw = ImageDraw.Draw(img)

    for b in blocks:
        x0, y0 = b['x'], b['y']
        x1, y1 = x0 + b['w'] - 1, y0 + b['h'] - 1
        c = tuple(map(int, b['color']))
        draw.rectangle([x0, y0, x1, y1], fill=c, outline="black")

    return img
