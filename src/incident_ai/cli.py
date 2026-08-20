from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze_all, analyze_text
from .models import IncidentAnalysis
from .redaction import redact_analysis
from .webhook import post_webhook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze Linux and service incident logs.")
    analyze = parser.add_subparsers(dest="command", required=True).add_parser("analyze")
    analyze.add_argument("source", nargs="?", help="Log file; omit to read from stdin.")
    analyze.add_argument("--format", choices=("text", "json", "compact-json", "sarif"), default="text")
    analyze.add_argument("--input-format", choices=("auto", "text", "jsonl"), default="auto")
    analyze.add_argument("--all", action="store_true", dest="all_incidents")
    analyze.add_argument("--group-by", choices=("host", "service", "unit", "container"))
    analyze.add_argument("--host")
    analyze.add_argument("--service")
    analyze.add_argument("--unit")
    analyze.add_argument("--container")
    analyze.add_argument("--include-context", action="store_true")
    analyze.add_argument("--redact", action="store_true")
    analyze.add_argument(
        "--webhook",
        help="POST the structured analysis to this explicit HTTP(S) webhook; requires --redact.",
    )
    analyze.add_argument(
        "--webhook-retries",
        type=int,
        default=0,
        help="Retry transient webhook failures with bounded exponential backoff (default: 0).",
    )
    analyze.add_argument(
        "--enrich",
        action="store_true",
        help=(
            "Opt in to remote OpenAI enrichment after local analysis and redaction."
        ),
    )
    analyze.add_argument("--model", default="gpt-5.6", help="OpenAI model used with --enrich (default: gpt-5.6).")
    return parser


def _read_source(source: str) -> str:
    if source:
        return Path(source).read_text(encoding="utf-8")
    return sys.stdin.read()


def _serialize(analysis: IncidentAnalysis, output_format: str) -> str:
    if output_format == "text":
        return analysis.to_text()
    if output_format == "compact-json":
        return json.dumps(analysis.to_dict(), separators=(",", ":"))
    if output_format == "json":
        return json.dumps(analysis.to_dict(), indent=2)
    return analysis.to_sarif()


def main() -> int:
    args = build_parser().parse_args()
    text = _read_source(args.source)
    analyses = analyze_all(
        text,
        input_format=args.input_format,
        group_by=args.group_by,
        host=args.host,
        service=args.service,
        unit=args.unit,
        container=args.container,
        include_context=args.include_context,
    )
    if not args.all_incidents:
        analyses = analyses[:1]

    if args.redact:
        analyses = [redact_analysis(item) for item in analyses]

    output = _serialize(analyses[0], args.format) if len(analyses) == 1 else json.dumps(
        {"analyses": [item.to_dict() for item in analyses]},
        indent=None if args.format == "compact-json" else 2,
    )
    print(output)

    if args.webhook:
        if not args.redact:
            print("--webhook requires --redact", file=sys.stderr)
            return 2
        for analysis in analyses:
            result = post_webhook(
                args.webhook,
                analysis,
                retries=args.webhook_retries,
            )
            if not result.success:
                print(result.error, file=sys.stderr)
                return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
