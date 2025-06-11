import importlib.util
from pathlib import Path
from PIL import Image

MODULE_PATH = Path(__file__).resolve().parents[1] / "SE2-IMGtoGame.py"
SPEC = importlib.util.spec_from_file_location("se2_imgtogame", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_generate_blocks_with_allowed_counts():
    img_path = Path(__file__).resolve().parents[1] / "Screenshots" / "test.jpg"
    img = Image.open(img_path).convert("RGB")
    scale = 0.05
    allowed = ["25cm", "50cm", "2.5m"]
    blocks, small_px, new_w, new_h, num_rows, num_cols, _ = MOD.generate_blocks_with_allowed(
        img, scale, allowed, threshold=30.0, debug=False
    )
    assert small_px == 5
    assert (new_w, new_h) == (1300, 650)
    assert (num_rows, num_cols) == (130, 260)
    assert len(blocks) == 2430
