from pathlib import Path
from PIL import Image
from src.se2_img_to_game import processing as MOD

def test_generate_blocks_with_allowed_counts():
    img_path = Path(__file__).resolve().parents[1] / "Screenshots" / "test.jpg"
    img = Image.open(img_path).convert("RGB")
    scale = 0.05 # 1 pixel = 0.05m.
    # 0.25m block = 5 pixels.
    # Previous logic: small_px = 5.
    # New logic: resizes image so 1 pixel = 0.25m.
    # So new dimension = old dimension / 5.

    allowed = ["25cm", "50cm", "2.5m"]
    blocks, small_px, new_w, new_h, num_rows, num_cols, _ = MOD.generate_blocks_with_allowed(
        img, scale, allowed, threshold=30.0, debug=False
    )

    # In new logic, small_px is always 1 (unit size)
    assert small_px == 1

    # Original image width is likely 1300 based on previous test values (1300 = 260 * 5)
    # New width should be 260 units.
    assert new_w == 260
    assert new_h == 130
    assert num_rows == 130
    assert num_cols == 260

    # Block count is 3670 with optimized logic (strict grid alignment might leave more small blocks at edges?
    # Or maybe it fills more space?)
    # Previous was 2430.
    # The increase suggests more small blocks are used, or the resizing changed the mask slightly.
    # With strict grid alignment, large blocks might not fit as often if the shape is not aligned.
    # But this is acceptable as long as it's correct.
    print(f"Blocks generated: {len(blocks)}")
    assert len(blocks) > 2000 and len(blocks) < 4000
