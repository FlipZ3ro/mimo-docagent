# MiMo-DocAgent: Long-Context Document Analyst

> RAG-free deep document understanding for long PDFs (10-K filings, legal contracts, research papers) powered by **Xiaomi MiMo** vision + reasoning.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Most "chat-with-your-PDF" tools punt to embeddings + retrieval, which struggles on documents where the answer requires reasoning across many pages (financial filings, depositions, scientific papers). MiMo-DocAgent skips retrieval and feeds whole pages directly to `mimo-v2-omni` for vision parsing and `mimo-v2.5-pro` for multi-step reasoning. The result is a document analyst that can answer questions like *"Cross-reference the risk factors in section 1A with the auditor's commentary in section 9"* — questions that retrieval-based RAG cannot.

## Why MiMo

- **`mimo-v2-omni`** parses page images including tables, charts, and footnotes.
- **`mimo-v2.5-pro`** runs long chain-of-thought over the assembled context.
- **Prompt caching** makes repeated questions over the same document cheap.

## Features

- PDF → per-page image rendering (`pypdfium2`).
- Two-pass analysis: page-by-page extraction + cross-page synthesis.
- Citation-aware answers: every claim cites a page number.
- Streaming progress with rich UI.
- Output formats: markdown report, JSON, or interactive Q&A loop.

## Quick start

```bash
git clone https://github.com/FlipZ3ro/mimo-docagent
cd mimo-docagent
pip install -e .
cp .env.example .env  # add MIMO_API_KEY

# Analyze a 10-K filing
python -m docagent.cli analyze --pdf examples/sample-10k.pdf --question \
  "Summarize the company's three largest risks and any disclosed mitigation."
```

Interactive Q&A loop:

```bash
python -m docagent.cli chat --pdf examples/sample-10k.pdf
```

## Architecture

```
   PDF (50-500 pages)
            │
            ▼
   ┌──────────────────┐
   │  PDFParser       │  pypdfium2 -> page images + page text
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Page Extractor  │  mimo-v2-omni: per-page structured facts
   └────────┬─────────┘
            │ JSON facts per page
            ▼
   ┌──────────────────┐
   │  Document Index  │  in-memory page graph w/ section headers
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Analyst         │  mimo-v2.5-pro: long-CoT reasoning + cite
   └────────┬─────────┘
            ▼
       answer + citations
```

## Roadmap

- [x] PDF rendering and per-page extraction
- [x] Cross-page synthesis with mimo-v2.5-pro
- [x] Markdown report output
- [ ] Table-aware extraction (CSV export per detected table)
- [ ] Multi-document Q&A (compare two filings)
- [ ] Streaming output to a web UI

## Token economics

| Document size  | Tokens per Q&A   |
|----------------|------------------|
| 10 pages       | ~50K             |
| 50 pages       | ~250K            |
| 200 pages      | ~1M              |

A typical analyst session on a 100-page 10-K with 10 questions: **~5M tokens**.

## License

MIT — see [LICENSE](LICENSE).
