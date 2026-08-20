from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .analyzer import analyze_all, analyze_text
from .enrichment import EnrichmentError, enrich_with_openai
from .formatters import format_json, format_json_many, format_text, format_text_many


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="incident-ai",
        description="Explain common Linux and service incidents from log text.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a log file or stdin.")
    analyze.add_argument(
        "source",
        nargs="?",
        default="-",
        help="Log file to analyze, or '-' to read from stdin (default).",
    )
    analyze.add_argument("--json", action="store_true", help="Emit JSON output.")
    analyze.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON. Implies --json.",
    )
    analyze.add_argument(
        "--all",
        action="store_true",
        help="Return every distinct recognized incident, ordered by confidence.",
    )
    analyze.add_argument(
        "--enrich",
        action="store_true",
        help="Opt in to remote OpenAI enrichment after local analysis and redaction.",
    )
    analyze.add_argument(
        "--model",
        default="gpt-5.6",
        help="OpenAI model used with --enrich (default: gpt-5.6).",
    )
    return parser


def _read_source(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8", errors="replace")


def _exit_code(severity: str, incident_type: str) -> int:
    if incident_type in {"unknown", "empty_input"}:
        return 0
    if severity == "critical":
        return 2
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text = _read_source(args.source)
    except OSError as exc:
        parser.exit(3, f"incident-ai: unable to read {args.source!r}: {exc}\n")

    if args.all:
        analyses = analyze_all(text)
        if args.enrich:
            try:
                analyses = tuple(enrich_with_openai(item, model=args.model) for item in analyses)
            except EnrichmentError as exc:
                parser.exit(4, f"incident-ai: {exc}\n")

        if args.json or args.compact:
            print(format_json_many(analyses, pretty=not args.compact))
        else:
            print(format_text_many(analyses))
        return max(_exit_code(item.severity, item.incident_type) for item in analyses)

    analysis = analyze_text(text)
    if args.enrich:
        try:
            analysis = enrich_with_openai(analysis, model=args.model)
        except EnrichmentError as exc:
            parser.exit(4, f"incident-ai: {exc}\n")

    if args.json or args.compact:
        print(format_json(analysis, pretty=not args.compact))
    else:
        print(format_text(analysis))
    return _exit_code(analysis.severity, analysis.incident_type)


if __name__ == "__main__":
    raise SystemExit(main())
