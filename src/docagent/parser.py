"""Render PDF -> per-page PIL images + extracted text."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image


@dataclass
class Page:
    index: int           # 0-based page index
    number: int          # 1-based human-readable page number
    image: Image.Image
    text: str            # raw text layer (empty for scanned PDFs)


class PDFParser:
    def __init__(self, dpi: int | None = None) -> None:
        self.dpi = dpi or int(os.environ.get("DOCAGENT_PAGE_DPI", "144"))

    def parse(self, pdf_path: Path | str) -> list[Page]:
        pdf = pdfium.PdfDocument(str(pdf_path))
        out: list[Page] = []
        scale = self.dpi / 72
        for i in range(len(pdf)):
            p = pdf[i]
            tp = p.get_textpage()
            text = tp.get_text_bounded() if tp else ""
            tp.close() if tp else None
            img = p.render(scale=scale).to_pil()
            p.close()
            out.append(Page(index=i, number=i + 1, image=img, text=text))
        pdf.close()
        return out
