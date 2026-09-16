"""Tests for provider MIME detection and prompt hardening."""

from cat_sticker_skill.providers.seedream import SeedreamRequest, _build_request_body, _detect_mime


def test_detect_png():
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    assert _detect_mime(png_bytes) == "image/png"


def test_detect_jpeg():
    jpg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    assert _detect_mime(jpg_bytes) == "image/jpeg"


def test_detect_webp():
    webp_bytes = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100
    assert _detect_mime(webp_bytes) == "image/webp"


def test_detect_fallback():
    assert _detect_mime(b"unknown") == "image/png"


def test_prompt_hardening_applied():
    req = SeedreamRequest(prompt="a cat")
    body = _build_request_body(req, "model", "key")
    assert "No text" in body["prompt"]
    assert "no watermark" in body["prompt"].lower()


def test_reference_mime_detected():
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    req = SeedreamRequest(prompt="test", reference_images=[png_bytes])
    body = _build_request_body(req, "model", "key")
    assert "data:image/png;base64," in body["image"]
