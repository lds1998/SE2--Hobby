import numpy as np
from PIL import Image
from src.se2_img_to_game import processing

def test_packing_large_block():
    # 2.5m = 10 units.
    # Create an image that results in a 10x10 grid (2.5m x 2.5m).
    # Since 1 unit = 0.25m, we need 2.5m Z -> 10 units height.
    # Aspect 1:1 -> 10 units width.
    # Image size doesn't matter much as it gets resized, but let's make it easy.
    # If we pass 100x100 image, Z=2.5, it resizes to 10x10.

    img = Image.new("RGB", (100, 100), "black") # Black is shape (mask < 250)
    scale = 2.5 / 100 # meters per pixel
    allowed = ["2.5m"] # Only large blocks allowed

    blocks, small_px, w, h, rows, cols, inside = processing.generate_blocks_optimized(
        img, scale, allowed, threshold=30.0, debug=True
    )

    # Expect 1 block of 2.5m
    assert w == 10
    assert h == 10
    assert len(blocks) == 1
    assert blocks[0]["block_type"] == "2.5m"
    assert blocks[0]["cell_size"] == 10

def test_packing_mixed_blocks():
    # 2.5m x 2.5m area (10x10 units).
    # Allowed: 2.5m, 50cm, 25cm.
    # Should prefer 2.5m.
    img = Image.new("RGB", (100, 100), "black")
    scale = 2.5 / 100
    allowed = ["25cm", "50cm", "2.5m"]

    blocks, _, _, _, _, _, _ = processing.generate_blocks_optimized(
        img, scale, allowed, threshold=30.0
    )
    assert len(blocks) == 1
    assert blocks[0]["block_type"] == "2.5m"

def test_packing_edge_case():
    # 1.25m x 1.25m area (5x5 units).
    # 2.5m (10x10) won't fit.
    # 50cm (2x2) should fit 4 times (covering 4x4 area = 16 units) ? No.
    # 5x5 grid.
    # 0,0: 2x2 fits.
    # 0,2: 2x2 fits.
    # 0,4: 1 col left.
    # 2,0: 2x2 fits.
    # 2,2: 2x2 fits.
    # ...
    # It should tile 2x2 blocks as much as possible, then 1x1.

    img = Image.new("RGB", (50, 50), "black")
    z = 1.25
    scale = z / 50
    allowed = ["25cm", "50cm", "2.5m"]

    blocks, _, w, h, _, _, _ = processing.generate_blocks_optimized(
        img, scale, allowed
    )
    assert w == 5
    assert h == 5

    # 2x2 blocks: 4 fit?
    # Grid:
    # 0 1 2 3 4
    # 1
    # 2
    # 3
    # 4
    # (0,0), (0,2), (2,0), (2,2) -> 4 blocks of 2x2.
    # Remaining: row 4 (5 cells), col 4 (5 cells). overlap at (4,4).
    # Total cells = 25. 4*4 = 16 covered. 9 remaining.
    # So 4 blocks of 50cm + 9 blocks of 25cm. Total 13 blocks.

    # Let's count types
    counts = {}
    for b in blocks:
        t = b["block_type"]
        counts[t] = counts.get(t, 0) + 1

    assert counts.get("2.5m", 0) == 0
    assert counts.get("50cm", 0) == 4
    assert counts.get("25cm", 0) == 9
