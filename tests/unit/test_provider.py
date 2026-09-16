"""Tests for Seedream provider request building."""

from pathlib import Path

from cat_sticker_skill.providers.seedream import SeedreamRequest, _build_request_body


class TestSingleReference:
    def test_single_image_is_string(self):
        req = SeedreamRequest(
            prompt="test",
            reference_images=[b"fake_image_bytes"],
        )
        body = _build_request_body(req, "test-model", "test-key")
        assert isinstance(body["image"], str)
        assert body["image"].startswith("data:image/png;base64,")
        assert body["model"] == "test-model"

    def test_no_reference_image_field(self):
        req = SeedreamRequest(prompt="test")
        body = _build_request_body(req, "test-model", "test-key")
        assert "image" not in body

    def test_required_fields(self):
        req = SeedreamRequest(prompt="a cat")
        body = _build_request_body(req, "model-v1", "key")
        assert body["prompt"] == "a cat"
        assert body["size"] == "2048x2048"
        assert body["response_format"] == "url"
        assert body["watermark"] is False


class TestMultipleReferences:
    def test_multiple_images_are_array(self):
        req = SeedreamRequest(
            prompt="test",
            reference_images=[b"img1", b"img2"],
        )
        body = _build_request_body(req, "test-model", "test-key")
        assert isinstance(body["image"], list)
        assert len(body["image"]) == 2
        assert all(x.startswith("data:image/png;base64,") for x in body["image"])

    def test_many_images(self):
        req = SeedreamRequest(
            prompt="test",
            reference_images=[b"img1", b"img2", b"img3"],
        )
        body = _build_request_body(req, "m", "k")
        assert isinstance(body["image"], list)
        assert len(body["image"]) == 3
