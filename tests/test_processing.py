import numpy as np
from PIL import Image, ImageDraw
from src.se2_img_to_game import processing

def test_dimensions():
    # 100px image, Z=25m -> 100 units.
    # Target height units = 100.
    w, h = processing.calculate_target_dimensions((100, 100), 25.0)
    assert h == 100
    assert w == 100

def test_transparency_mask():
    # Create RGBA image with transparent hole
    img = Image.new("RGBA", (10, 10), (0,0,0,255))
    img.putpixel((5,5), (0,0,0,0)) # Transparent pixel

    mask, _ = processing.compute_masks(img)
    assert mask[0,0] == True # Opaque Black -> Inside
    assert mask[5,5] == False # Transparent -> Outside

def test_edge_mask():
    # 5x5 block of True surrounded by False
    mask = np.zeros((7,7), dtype=bool)
    mask[1:6, 1:6] = True # Inner 5x5 is True

    edge = processing.compute_edge_mask(mask)

    # Center (3,3) should NOT be edge (surrounded by True)
    assert edge[3,3] == False

    # Border (1,1) should be edge (neighbor (0,1) is False)
    assert edge[1,1] == True

def test_block_generation_scaling():
    # Input 100x100. Z=2.5m (10 units).
    # So image resized to 10x10.
    img = Image.new("RGBA", (100, 100), (0,0,0,255))
    scale = 2.5 / 100

    blocks, w, h = processing.generate_blocks(img, ["2.5m"], scale)
    assert w == 10
    assert h == 10
    assert len(blocks) == 1
    assert blocks[0]['block_type'] == "2.5m"

def test_edge_preference():
    # 2.5m block fits (10x10).
    # But we set edge_pref="50cm".
    # And we make the image 10x10 units.
    # All pixels are "Edge" because 10x10 touches the void (0,0 is edge).
    # Wait, in a 10x10 image, (0,0) is edge. (5,5) is Core.
    # So 2.5m block covers (0,0). So it covers edge.
    # So it should be rejected.
    # We expect smaller blocks to fill it.

    img = Image.new("RGBA", (100, 100), (0,0,0,255))
    scale = 2.5 / 100 # 10x10 units

    # 2.5m is size 10.
    # 50cm is size 2.

    blocks, _, _ = processing.generate_blocks(img, ["2.5m", "50cm"], scale, edge_pref="50cm")

    # Should NOT contain 2.5m blocks because the only possible position (0,0) touches edge.
    types = [b['block_type'] for b in blocks]
    assert "2.5m" not in types
    assert "50cm" in types

    # If we disable edge pref, 2.5m should appear
    blocks_no_pref, _, _ = processing.generate_blocks(img, ["2.5m", "50cm"], scale, edge_pref=None)
    types_no_pref = [b['block_type'] for b in blocks_no_pref]
    assert "2.5m" in types_no_pref
