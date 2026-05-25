"""Document analyst: long-CoT reasoning over assembled page facts."""

from __future__ import annotations

import os
from dataclasses import dataclass

from docagent.client import DocClient
from docagent.extractor import PageFacts


SYSTEM = """You are a document analyst. The user provides:
- A question about a document.
- A condensed page-by-page index of that document.

Answer the question using ONLY the index. Cite every claim as (p. N). If the
index doesn't contain the answer, say so explicitly — never invent facts.
Use short paragraphs, with a final 'Sources' line listing the cited pages."""


def _facts_to_index(facts: list[PageFacts]) -> str:
    rows = []
    for f in facts:
        if not f.summary and not f.key_points:
            continue
        header = f"p.{f.page}"
        if f.section_header:
            header += f" — {f.section_header}"
        bullets = "; ".join(f.key_points) if f.key_points else ""
        line = f"{header}: {f.summary}"
        if bullets:
            line += f" KEY: {bullets}"
        if f.tables:
            line += f" TABLES: {' | '.join(f.tables[:2])}"
        rows.append(line)
    return "\n".join(rows)


@dataclass
class Answer:
    text: str
    tokens: int


class Analyst:
    def __init__(self, client: DocClient | None = None) -> None:
        self.client = client or DocClient()
        self.model = os.environ.get("MIMO_REASONING_MODEL", "mimo-v2.5-pro")

    def ask(self, facts: list[PageFacts], question: str, *, max_tokens: int = 4096) -> Answer:
        index = _facts_to_index(facts)
        prompt = f"Question: {question}\n\nDocument index:\n{index}"
        text, usage = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0,
        )
        return Answer(text=text, tokens=usage["total_tokens"])
