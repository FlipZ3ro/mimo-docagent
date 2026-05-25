"""docagent CLI: analyze and chat over a PDF."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from docagent.analyst import Analyst
from docagent.client import DocClient
from docagent.extractor import PageExtractor
from docagent.parser import PDFParser


def _build_index(pdf_path: Path, console: Console):
    parser = PDFParser()
    console.print(f"[bold]parsing[/] {pdf_path.name} ...")
    pages = parser.parse(pdf_path)
    console.print(f"  -> {len(pages)} pages")

    client = DocClient()
    extractor = PageExtractor(client=client)
    console.print("[bold]extracting per-page facts[/] (vision pass) ...")
    facts = extractor.extract_all(pages)
    tokens = sum(f.tokens for f in facts)
    console.print(f"  -> {len(facts)} pages indexed, {tokens} tokens")
    return client, facts, tokens


def cmd_analyze(args: argparse.Namespace) -> int:
    load_dotenv()
    console = Console()
    pdf = Path(args.pdf)
    client, facts, idx_tokens = _build_index(pdf, console)

    analyst = Analyst(client=client)
    console.print("[bold]analyzing[/] (reasoning pass) ...")
    ans = analyst.ask(facts, args.question)
    console.print(Markdown(ans.text))
    console.print(f"\nindex_tokens={idx_tokens}  reasoning_tokens={ans.tokens}  total={idx_tokens + ans.tokens}")
    if args.out:
        Path(args.out).write_text(ans.text, encoding="utf-8")
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    load_dotenv()
    console = Console()
    pdf = Path(args.pdf)
    client, facts, idx_tokens = _build_index(pdf, console)
    analyst = Analyst(client=client)
    console.print(f"\nReady. Ask anything about {pdf.name}. (Ctrl-C to exit.)\n")
    while True:
        try:
            q = console.input("[bold cyan]?[/] ")
        except (EOFError, KeyboardInterrupt):
            break
        if not q.strip():
            continue
        ans = analyst.ask(facts, q)
        console.print(Markdown(ans.text))
        console.print(f"  [dim]+{ans.tokens} tokens[/]\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="docagent")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="answer one question about a PDF")
    a.add_argument("--pdf", required=True)
    a.add_argument("--question", required=True)
    a.add_argument("--out", default=None)
    a.set_defaults(func=cmd_analyze)

    c = sub.add_parser("chat", help="interactive Q&A loop over a PDF")
    c.add_argument("--pdf", required=True)
    c.set_defaults(func=cmd_chat)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
