from pathlib import Path

import pytest

from docpage2md_app.cost import (
    QWEN_VISION_DEFAULT_MAX_PIXELS,
    calculate_image_tokens,
    estimate_deepseek_chat_tokens,
    estimate_deepseek_text_tokens,
    smart_resize_dimensions,
)
from docpage2md_app.deepseek_tokenizer import encode_text


def test_deepseek_tokenizer_counts_basic_text():
    assert encode_text("Hello!") == [19923, 3]
    assert estimate_deepseek_text_tokens("Hello!") == 2
    assert estimate_deepseek_chat_tokens([{"role": "user", "content": "Hello!"}]) == 5
    assert estimate_deepseek_text_tokens("群论笔记") == 4


def test_qwen_image_smart_resize_default_max_pixels():
    resized_h, resized_w, max_pixels = smart_resize_dimensions(4096, 4096)

    assert (resized_h, resized_w) == (1600, 1600)
    assert max_pixels == QWEN_VISION_DEFAULT_MAX_PIXELS


def test_qwen_image_token_count_uses_real_dimensions(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image

    image = tmp_path / "crop.png"
    Image.new("RGB", (100, 100), "white").save(image)

    assert calculate_image_tokens(image) == 11


def test_qwen_image_token_count_scales_tiny_images_to_minimum(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image

    image = tmp_path / "tiny.png"
    Image.new("RGB", (1, 1), "white").save(image)

    assert calculate_image_tokens(image) == 6
