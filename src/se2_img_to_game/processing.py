import numpy as np
from PIL import Image, ImageDraw

def compute_shape_mask(image, shape_thresh=250, alpha_thresh=128):
    """
    Converte a imagem para escala de cinza e retorna uma máscara booleana.
    Handles transparency if available.
    """
    if image.mode == 'RGBA':
        # Check alpha channel
        alpha = np.array(image.split()[-1])
        is_opaque = alpha > alpha_thresh

        gray = image.convert("L")
        arr = np.array(gray)
        is_dark = arr < shape_thresh

        mask = is_dark & is_opaque
    else:
        gray = image.convert("L")
        arr = np.array(gray)
        mask = arr < shape_thresh
    return mask

def calculate_target_dimensions(image_size, z_meters, y_meters=None):
    """
    Calculates the target grid dimensions where 1 unit = 0.25 meters.
    """
    base_unit = 0.25
    target_height_units = int(z_meters / base_unit)

    if y_meters is not None and y_meters > 0:
         target_width_units = int(y_meters / base_unit)
    else:
        aspect_ratio = image_size[0] / image_size[1]
        target_width_units = int(target_height_units * aspect_ratio)

    return max(1, target_width_units), max(1, target_height_units)

def resize_image_to_grid(image, target_shape):
    return image.resize(target_shape, resample=Image.Resampling.LANCZOS)

def generate_blocks_optimized(image_pil, scale, allowed_types, threshold=30.0, debug=False, alpha_thresh=128):
    """
    Optimized block generation using Grid-Aligned greedy strategy.

    Args:
        image_pil (PIL.Image): Input image.
        scale (float): Original scale (meters per pixel).
        allowed_types (list): List of allowed block types.
        threshold (float): Color variance threshold.
        debug (bool): Print debug info.
        alpha_thresh (int): Alpha transparency threshold (0-255).

    Returns:
        blocks, small_px, new_width, new_height, num_rows, num_cols, inside
    """
    real_z = scale * image_pil.height
    target_width, target_height = calculate_target_dimensions(image_pil.size, real_z)

    if debug:
        print(f"Optimized Processing: Resizing input {image_pil.size} to grid {target_width}x{target_height}")

    image_resized = resize_image_to_grid(image_pil, (target_width, target_height))
    small_px = 1 # 1 pixel = 0.25m

    num_cols = target_width
    num_rows = target_height

    # 1. Compute Mask and Inside
    # inside is True where pixel is dark (part of shape) AND opaque
    mask = compute_shape_mask(image_resized, shape_thresh=250, alpha_thresh=alpha_thresh)
    inside = mask # shape is where mask is True

    # 2. Prepare Data
    # For color calculations, we should convert to RGB to ignore Alpha in variance?
    # Or keep RGBA but handle it. Usually, we just care about visible color.
    img_rgb = image_resized.convert("RGB")
    img_np = np.array(img_rgb, dtype=np.float32)
    # cell_colors is the image itself
    cell_colors = img_np

    merged = np.zeros((num_rows, num_cols), dtype=bool)
    blocks = []

    size_mapping = {"25cm": 1, "50cm": 2, "2.5m": 10}

    # Sort allowed types by size descending
    allowed_order = sorted(allowed_types, key=lambda t: size_mapping[t], reverse=True)
    fallback = min(allowed_types, key=lambda t: size_mapping[t]) if allowed_types else None

    if not allowed_types:
        return [], 1, target_width, target_height, num_rows, num_cols, inside

    # 3. Grid Aligned Pass
    for t in allowed_order:
        bs = size_mapping[t]

        if bs == 1:
            continue

        rows_range = range(0, num_rows - bs + 1, bs)
        cols_range = range(0, num_cols - bs + 1, bs)

        for r in rows_range:
            for c in cols_range:
                if not np.all(inside[r:r+bs, c:c+bs]):
                    continue
                if np.any(merged[r:r+bs, c:c+bs]):
                    continue

                # Color Threshold Check
                region = cell_colors[r:r+bs, c:c+bs]
                avg = region.mean(axis=(0,1))
                diff = np.abs(region - avg)
                if diff.max() <= threshold:
                    merged[r:r+bs, c:c+bs] = True
                    blocks.append({
                        "row_start": r,
                        "col_start": c,
                        "cell_size": bs,
                        "avg_color": avg,
                        "block_type": t
                    })

    # 4. Fallback / Smallest Blocks (1x1)
    if fallback and size_mapping[fallback] == 1:
        unmerged = inside & (~merged)
        ys, xs = np.where(unmerged)
        for i in range(len(ys)):
            r, c = ys[i], xs[i]
            blocks.append({
                "row_start": r,
                "col_start": c,
                "cell_size": 1,
                "avg_color": cell_colors[r, c],
                "block_type": fallback
            })

    return blocks, small_px, target_width, target_height, num_rows, num_cols, inside

def generate_blocks_with_allowed(image_pil, scale, allowed_types, threshold=30.0, debug=False, alpha_thresh=128):
    return generate_blocks_optimized(image_pil, scale, allowed_types, threshold, debug, alpha_thresh)

def generate_instructions_from_blocks(blocks, small_px, scale, constant_y, use_3d=False):
    """
    Gera instruções de posicionamento a partir dos blocos detectados.
    blocks: lista de dicionários de blocos.
    small_px: tamanho da menor célula em pixels.
    scale: fator de conversão de pixels para metros.
    constant_y: valor Y aplicado a todas as instruções.
    use_3d: considera espessuras padrão ao calcular a altura.

    Retorna uma lista de dicionários com as chaves
    'block_type', 'x', 'y', 'z', 'width' e 'height'.
    """
    default_thickness = {"25cm": 0.25, "50cm": 0.50, "2.5m": 2.50}

    effective_scale = 0.25 if small_px == 1 else scale

    instructions = []
    for block in blocks:
        r = block["row_start"]
        c = block["col_start"]
        size = block["cell_size"]
        x0_px = c * small_px
        y0_px = r * small_px
        width_px = size * small_px
        height_px = size * small_px
        center_x = (x0_px + width_px/2) * effective_scale
        center_z = (y0_px + height_px/2) * effective_scale
        if use_3d:
            h_val = default_thickness.get(block["block_type"], round(height_px * effective_scale, 2))
        else:
            h_val = round(height_px * effective_scale, 2)
        instructions.append({
            "block_type": block["block_type"],
            "x": round(center_x, 2),
            "y": constant_y,
            "z": round(center_z, 2),
            "width": round(width_px * effective_scale, 2),
            "height": h_val
        })
    return instructions

def generate_schematic_image_from_blocks(image_size, blocks, small_px):
    schematic = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(schematic)
    for block in blocks:
        r = block["row_start"]
        c = block["col_start"]
        size = block["cell_size"]
        x0 = c * small_px
        y0 = r * small_px
        x1 = x0 + size * small_px
        y1 = y0 + size * small_px
        draw.rectangle([x0, y0, x1, y1], outline="black", width=1)
    return schematic
