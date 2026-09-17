"""Seedream (Volcengine / Ark) image generation provider.

v1 only implements the Ark/Seedream backend. All credentials come from
environment variables. API keys are never logged or written to disk.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class GenerationResult:
    success: bool
    output_path: Optional[Path] = None
    error: Optional[str] = None
    error_class: Optional[str] = None  # auth/rate_limit/network/invalid_input/provider_rejected/invalid_image/download_failed/processing_failed
    retryable: bool = False
    http_status: Optional[int] = None
    request_id: Optional[str] = None
    generated_images: int = 0
    retries_used: int = 0
    duration_seconds: float = 0.0


@dataclass
class SeedreamRequest:
    prompt: str
    reference_images: List[bytes] = field(default_factory=list)  # raw image bytes
    output_path: Path = field(default_factory=lambda: Path("output.png"))
    size: str = "2048x2048"
    response_format: str = "url"


def _detect_mime(data: bytes) -> str:
    """Detect image MIME type from magic bytes. Returns "" for unknown."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return ""


def _build_request_body(req: SeedreamRequest, model: str, api_key: str) -> dict:
    # Always append prompt hardening
    hardened_prompt = req.prompt + (
        ". No text, no letters, no watermark, no logo, "
        "no irrelevant decoration. Avoid extra limbs, avoid extra animals."
    )
    body = {
        "model": model,
        "prompt": hardened_prompt,
        "size": req.size,
        "response_format": req.response_format,
        "watermark": False,
        "stream": False,
        "sequential_image_generation": "disabled",
    }
    if req.reference_images:
        images = []
        for img_bytes in req.reference_images:
            mime = _detect_mime(img_bytes)
            if not mime:
                raise ValueError("invalid_input: reference image format not recognized")
            b64 = base64.b64encode(img_bytes).decode()
            images.append(f"data:{mime};base64,{b64}")
        body["image"] = images if len(images) > 1 else images[0]
    return body


def generate_image(
    req: SeedreamRequest,
    api_key: str,
    model: str,
    max_retries: int = 2,
    timeout: int = 120,
) -> GenerationResult:
    """Call Seedream API to generate one image.

    Retries on transient errors (5xx, network). Does not retry on
    auth errors or bad parameters.
    """
    endpoint = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    body = _build_request_body(req, model, api_key)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    start = time.time()
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            data = json.dumps(body).encode("utf-8")
            http_req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(http_req, timeout=timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

            # Extract image from response
            images = resp_data.get("data", [])
            if not images:
                last_error = "No image in response"
                continue

            img_url = images[0].get("url")
            img_b64 = images[0].get("b64_json")

            if img_url:
                # Download the image from URL
                try:
                    with urllib.request.urlopen(img_url, timeout=timeout) as img_resp:
                        img_bytes = img_resp.read()
                except Exception as e:
                    return GenerationResult(
                        success=False, error=f"download_failed: {e}",
                        error_class="download_failed", retryable=True,
                        duration_seconds=round(time.time() - start, 2),
                    )
            elif img_b64:
                img_bytes = base64.b64decode(img_b64)
            else:
                last_error = "No image data in response"
                continue

            # Validate and normalize: decode, strip metadata, re-encode as real PNG
            try:
                import io

                from PIL import Image
                im = Image.open(io.BytesIO(img_bytes))
                im.verify()
                im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            except Exception as e:
                return GenerationResult(
                    success=False, error=f"invalid_image: {e}",
                    error_class="invalid_image", retryable=False,
                    http_status=200,
                    request_id=resp_data.get("id"),
                    duration_seconds=round(time.time() - start, 2),
                )

            req.output_path.parent.mkdir(parents=True, exist_ok=True)
            # Atomic write via temp file
            tmp = req.output_path.with_suffix(".png.tmp")
            im.save(tmp, "PNG")
            tmp.replace(req.output_path)

            return GenerationResult(
                success=True,
                output_path=req.output_path,
                request_id=resp_data.get("id"),
                generated_images=1,
                retries_used=attempt,
                duration_seconds=round(time.time() - start, 2),
            )

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")[:500]
            except Exception:
                pass
            if e.code in (401, 403):
                return GenerationResult(
                    success=False,
                    error=f"Auth error ({e.code}): check ARK_API_KEY. {error_body}",
                    error_class="auth",
                    retryable=False,
                    http_status=e.code,
                    retries_used=attempt,
                    duration_seconds=round(time.time() - start, 2),
                )
            if e.code == 400:
                return GenerationResult(
                    success=False,
                    error=f"Bad request (400): {error_body}",
                    error_class="invalid_input",
                    retryable=False,
                    http_status=400,
                    retries_used=attempt,
                    duration_seconds=round(time.time() - start, 2),
                )
            if e.code == 429:
                return GenerationResult(
                    success=False,
                    error="Rate limited (429)",
                    error_class="rate_limit",
                    retryable=True,
                    http_status=429,
                    retries_used=attempt,
                    duration_seconds=round(time.time() - start, 2),
                )
            if 500 <= e.code < 600:
                last_error = f"HTTP {e.code}: {error_body}"
            else:
                return GenerationResult(
                    success=False,
                    error=f"Provider rejected ({e.code}): {error_body}",
                    error_class="provider_rejected",
                    retryable=False,
                    http_status=e.code,
                    retries_used=attempt,
                    duration_seconds=round(time.time() - start, 2),
                )
        except (urllib.error.URLError, TimeoutError) as e:
            last_error = f"network: {e}"

        # Wait before retry
        if attempt < max_retries:
            time.sleep(2 ** attempt)

    return GenerationResult(
        success=False,
        error=last_error or "Unknown error",
        error_class="network",
        retryable=True,
        retries_used=max_retries,
        duration_seconds=round(time.time() - start, 2),
    )
