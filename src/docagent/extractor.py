"""Per-page extraction: vision pass to pull structured facts."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from docagent.client import DocClient, pil_to_data_url
from docagent.parser import Page


SYSTEM = """You extract structured facts from a single document page image.
Return strict JSON with:
- section_header: the section heading the page belongs to (or "")
- summary: 1-2 sentence factual summary of the page
- key_points: list of up to 5 short bullet points (each <= 20 words)
- tables: list of table descriptions (each <= 30 words), or []
- figures: list of figure/chart descriptions (each <= 30 words), or []
Do not invent details. If the page is blank or boilerplate, return empty values."""


@dataclass
class PageFacts:
    page: int
    section_header: str
    summary: str
    key_points: list[str]
    tables: list[str]
    figures: list[str]
    tokens: int = 0
    raw: dict = field(default_factory=dict)


class PageExtractor:
    def __init__(self, client: DocClient | None = None) -> None:
        self.client = client or DocClient()
        self.model = os.environ.get("MIMO_VISION_MODEL", "mimo-v2-omni")
        self.max_tokens = int(os.environ.get("DOCAGENT_MAX_PAGE_TOKENS", "2048"))

    def _one(self, page: Page) -> PageFacts:
        url = pil_to_data_url(page.image)
        prompt = f"This is page {page.number} of a document. Extract facts."
        try:
            text, usage = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": url}},
                        ],
                    },
                ],
                max_tokens=self.max_tokens,
                temperature=0,
                response_format={"type": "json_object"},
            )
            payload = json.loads(text)
        except Exception as e:
            return PageFacts(page=page.number, section_header="",
                             summary=f"[extract error: {e}]",
                             key_points=[], tables=[], figures=[], tokens=0, raw={})

        return PageFacts(
            page=page.number,
            section_header=str(payload.get("section_header", "")),
            summary=str(payload.get("summary", "")),
            key_points=list(payload.get("key_points", []))[:5],
            tables=list(payload.get("tables", [])),
            figures=list(payload.get("figures", [])),
            tokens=usage["total_tokens"],
            raw=payload,
        )

    def extract_all(self, pages: list[Page], *, workers: int | None = None) -> list[PageFacts]:
        workers = workers or int(os.environ.get("DOCAGENT_MAX_PARALLEL_PAGES", "4"))
        out: list[PageFacts] = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(self._one, p): p for p in pages}
            for fut in as_completed(futs):
                out.append(fut.result())
        out.sort(key=lambda f: f.page)
        return out
