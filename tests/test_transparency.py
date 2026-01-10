import numpy as np
from PIL import Image, ImageDraw
from src.se2_img_to_game import processing

def test_transparency_handling():
    # Create 100x100 image, mostly black (shape), but with a transparent center.
    # RGBA.
    img = Image.new("RGBA", (100, 100), (0, 0, 0, 255)) # Black Opaque

    # Create transparent hole
    draw = ImageDraw.Draw(img)
    # 20x20 hole in center
    draw.rectangle([40, 40, 60, 60], fill=(0, 0, 0, 0)) # Transparent

    scale = 2.5 / 100 # 2.5m total size -> 100px -> 10x10 grid (10px per unit)

    # Run processing
    blocks, _, w, h, _, _, inside = processing.generate_blocks_optimized(
        img, scale, ["25cm"], alpha_thresh=128, debug=True
    )

    # Check dimensions
    assert w == 10
    assert h == 10

    # Check center blocks are missing
    # Center corresponds to units (4,4), (4,5), (5,4), (5,5) approx.
    # 40px - 60px is 40% - 60%.
    # In 10 units: unit 4, 5.

    # Verify inside mask
    # inside is 10x10.
    # Center should be False.
    assert not inside[4, 4]
    assert not inside[5, 5]

    # Corners should be True (Black Opaque)
    assert inside[0, 0]
    assert inside[9, 9]

    # Block count should be 100 - (2x2 hole = 4) = 96 approx.
    # Actually 40-60 is 20 pixels. 100px total. 20/100 = 1/5.
    # 10 units * 1/5 = 2 units.
    # So hole is 2x2 units.
    # Total blocks should be 100 - 4 = 96.

    print(f"Blocks generated: {len(blocks)}")
    # Allow small variance due to resampling aliasing at borders
    assert len(blocks) < 100
    assert len(blocks) > 90
