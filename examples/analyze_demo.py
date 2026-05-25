"""End-to-end demo: analyze a sample PDF.

Drop any PDF as `examples/sample.pdf` then run:
    python examples/analyze_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from docagent.analyst import Analyst
from docagent.extractor import PageExtractor
from docagent.parser import PDFParser


PDF = Path(__file__).resolve().parent / "sample.pdf"
QUESTION = "Summarize the document in 5 bullet points, with page citations."


def main() -> int:
    load_dotenv()
    console = Console()
    if not PDF.exists():
        console.print(f"[red]missing[/] {PDF} — drop a PDF here first")
        return 1
    pages = PDFParser().parse(PDF)
    console.print(f"parsed {len(pages)} pages")
    facts = PageExtractor().extract_all(pages)
    ans = Analyst().ask(facts, QUESTION)
    console.print(Markdown(ans.text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
