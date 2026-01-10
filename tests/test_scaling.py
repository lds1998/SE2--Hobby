from src.se2_img_to_game import processing
from PIL import Image

def test_calculate_target_dimensions():
    # 100 px image, 100 meters Z.
    # Target height units = 100 / 0.25 = 400.
    # Aspect ratio 1:1 -> Width units = 400.
    w, h = processing.calculate_target_dimensions((100, 100), 100.0)
    assert w == 400
    assert h == 400

def test_calculate_target_dimensions_with_y():
    # 100 px image, 100 meters Z, 50 meters Y.
    # H = 400 units. W = 200 units.
    w, h = processing.calculate_target_dimensions((100, 100), 100.0, 50.0)
    assert w == 200
    assert h == 400

def test_resize_image_to_grid():
    img = Image.new("RGB", (100, 100), "white")
    target = (400, 400)
    resized = processing.resize_image_to_grid(img, target)
    assert resized.size == target
