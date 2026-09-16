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
    request_id: Optional[str] = None
    retries_used: int = 0
    duration_seconds: float = 0.0


@dataclass
class SeedreamRequest:
    prompt: str
    reference_images: List[bytes] = field(default_factory=list)  # raw image bytes
    output_path: Path = field(default_factory=lambda: Path("output.png"))
    size: str = "2048x2048"
    response_format: str = "url"


def _build_request_body(req: SeedreamRequest, model: str, api_key: str) -> dict:
    body = {
        "model": model,
        "prompt": req.prompt,
        "size": req.size,
        "response_format": req.response_format,
        "watermark": False,
        "stream": False,
        "sequential_image_generation": "disabled",
    }
    if req.reference_images:
        # Seedream expects reference images as a single base64 data URI
        b64 = base64.b64encode(req.reference_images[0]).decode()
        body["image"] = f"data:image/png;base64,{b64}"
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
                with urllib.request.urlopen(img_url, timeout=timeout) as img_resp:
                    img_bytes = img_resp.read()
            elif img_b64:
                img_bytes = base64.b64decode(img_b64)
            else:
                last_error = "No image data in response"
                continue
            req.output_path.parent.mkdir(parents=True, exist_ok=True)
            req.output_path.write_bytes(img_bytes)

            return GenerationResult(
                success=True,
                output_path=req.output_path,
                request_id=resp_data.get("id"),
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
                    retries_used=attempt,
                    duration_seconds=round(time.time() - start, 2),
                )
            if e.code == 400:
                return GenerationResult(
                    success=False,
                    error=f"Bad request (400): {error_body}",
                    retries_used=attempt,
                    duration_seconds=round(time.time() - start, 2),
                )
            last_error = f"HTTP {e.code}: {error_body}"
        except (urllib.error.URLError, TimeoutError) as e:
            last_error = f"Network: {e}"

        # Wait before retry
        if attempt < max_retries:
            time.sleep(2 ** attempt)

    return GenerationResult(
        success=False,
        error=last_error or "Unknown error",
        retries_used=max_retries,
        duration_seconds=round(time.time() - start, 2),
    )
