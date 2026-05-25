"""MiMo-DocAgent: long-context PDF analyst."""

from docagent.parser import PDFParser, Page
from docagent.extractor import PageExtractor, PageFacts
from docagent.analyst import Analyst, Answer

__all__ = ["PDFParser", "Page", "PageExtractor", "PageFacts", "Analyst", "Answer"]
__version__ = "0.1.0"
