"""Shared MiMo client used by extractor and analyst."""

from __future__ import annotations

import base64
import io
import os

from openai import OpenAI
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential


def pil_to_data_url(img: Image.Image, max_side: int = 1280, quality: int = 85) -> str:
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"


class DocClient:
    def __init__(self) -> None:
        self.api_key = os.environ.get("MIMO_API_KEY")
        if not self.api_key:
            raise RuntimeError("MIMO_API_KEY missing — see .env.example")
        self.base_url = os.environ.get(
            "MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1"
        )
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=15))
    def chat(self, *, model: str, messages: list[dict], **kw) -> tuple[str, dict]:
        r = self._client.chat.completions.create(model=model, messages=messages, **kw)
        u = r.usage
        return (r.choices[0].message.content or "").strip(), {
            "prompt_tokens": u.prompt_tokens,
            "completion_tokens": u.completion_tokens,
            "total_tokens": u.total_tokens,
        }
