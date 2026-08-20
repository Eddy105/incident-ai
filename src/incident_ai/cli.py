from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .analyzer import analyze_all, analyze_text
from .enrichment import EnrichmentError, enrich_with_openai
from .formatters import (
    format_json,
    format_json_grouped,
    format_json_many,
    format_sarif,
    format_text,
    format_text_grouped,
    format_text_many,
)
from .ingest import InputFormatError, normalize_grouped_input, normalize_input
from .redaction import redact_analysis


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
        "--sarif",
        action="store_true",
        help="Emit SARIF 2.1.0 for CI and security tooling.",
    )
    analyze.add_argument(
        "--all",
        action="store_true",
        help="Return every distinct recognized incident, ordered by confidence.",
    )
    analyze.add_argument(
        "--input-format",
        choices=("auto", "text", "jsonl"),
        default="auto",
        help="Input format: auto-detect JSON Lines, force plain text, or require JSON Lines (default: auto).",
    )
    analyze.add_argument(
        "--include-context",
        action="store_true",
        help="Preserve host, service, unit, container, and PID metadata from structured JSON Lines in evidence.",
    )
    analyze.add_argument("--host", help="Analyze only JSON Lines records from this host.")
    analyze.add_argument("--service", help="Analyze only JSON Lines records from this service/application.")
    analyze.add_argument("--unit", help="Analyze only JSON Lines records from this systemd unit.")
    analyze.add_argument("--container", help="Analyze only JSON Lines records from this container.")
    analyze.add_argument(
        "--group-by",
        choices=("host", "service", "unit", "container"),
        help="Analyze structured records independently per source field to prevent cross-source correlation.",
    )
    analyze.add_argument(
        "--redact",
        action="store_true",
        help="Redact common secrets and identifiers from analysis output before exporting or displaying it.",
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


def _maybe_enrich_many(analyses, *, enabled: bool, model: str):
    if not enabled:
        return analyses
    return tuple(enrich_with_openai(item, model=model) for item in analyses)


def _maybe_redact(analysis: object, *, enabled: bool):
    return redact_analysis(analysis) if enabled else analysis


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source_filters = {
        key: value
        for key, value in {
            "host": args.host,
            "service": args.service,
            "unit": args.unit,
            "container": args.container,
        }.items()
        if value
    }

    if args.sarif and args.compact:
        parser.error("--sarif cannot be combined with --compact")

    try:
        raw_text = _read_source(args.source)
        if args.group_by:
            grouped_text = normalize_grouped_input(
                raw_text,
                args.group_by,
                args.input_format,
                include_context=args.include_context,
                source_filters=source_filters,
            )
        else:
            text = normalize_input(
                raw_text,
                args.input_format,
                include_context=args.include_context,
                source_filters=source_filters,
            )
    except OSError as exc:
        parser.exit(3, f"incident-ai: unable to read {args.source!r}: {exc}\n")
    except InputFormatError as exc:
        parser.exit(3, f"incident-ai: invalid structured input: {exc}\n")

    if args.group_by:
        grouped_analyses = []
        try:
            for value, group_text in grouped_text.items():
                analyses = analyze_all(group_text) if args.all else (analyze_text(group_text),)
                analyses = _maybe_enrich_many(analyses, enabled=args.enrich, model=args.model)
                analyses = tuple(_maybe_redact(item, enabled=args.redact) for item in analyses)
                grouped_analyses.append((value, analyses))
        except EnrichmentError as exc:
            parser.exit(4, f"incident-ai: {exc}\n")

        groups = tuple(grouped_analyses)
        if args.sarif:
            print(format_sarif(tuple(item for _value, analyses in groups for item in analyses)))
        elif args.json or args.compact:
            print(format_json_grouped(groups, group_by=args.group_by, pretty=not args.compact))
        else:
            print(format_text_grouped(groups, group_by=args.group_by))
        return max(
            (_exit_code(item.severity, item.incident_type) for _value, analyses in groups for item in analyses),
            default=0,
        )

    if args.all:
        analyses = analyze_all(text)
        try:
            analyses = _maybe_enrich_many(analyses, enabled=args.enrich, model=args.model)
        except EnrichmentError as exc:
            parser.exit(4, f"incident-ai: {exc}\n")
        analyses = tuple(_maybe_redact(item, enabled=args.redact) for item in analyses)

        if args.sarif:
            print(format_sarif(analyses))
        elif args.json or args.compact:
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
    analysis = _maybe_redact(analysis, enabled=args.redact)

    if args.sarif:
        print(format_sarif((analysis,)))
    elif args.json or args.compact:
        print(format_json(analysis, pretty=not args.compact))
    else:
        print(format_text(analysis))
    return _exit_code(analysis.severity, analysis.incident_type)


if __name__ == "__main__":
    raise SystemExit(main())
