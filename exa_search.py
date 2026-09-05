#!/usr/bin/env python3
r"""Exa web-search helper for nano_SLMs agents.

Search the web, fetch page contents for known URLs, or get a grounded answer
via the Exa API (https://docs.exa.ai). The API key is read from EXA_API_KEY in
the project-root .env file (never hardcoded, never committed; .gitignore covers
.env). Get a key at https://dashboard.exa.ai/api-keys.

Run it with the project venv (exa-py lives there), from any cwd:

    .\.venv\Scripts\python.exe exa_search.py search "Latest news on Nvidia" --num 5
    exa_search.bat search "Latest news on Nvidia" --num 5 --json
    exa_search.bat contents https://exa.ai https://docs.exa.ai --max-chars 4000
    exa_search.bat answer "What makes some LLMs better than others?" --json

Programmatic use (venv python; importable because the file sits at project root):

    from exa_search import exa_search, exa_contents, exa_answer

    payload = exa_search("Latest news on Nvidia", num_results=10)
    for r in payload["results"]:
        print(r["title"], r["url"], (r.get("highlights") or [""])[0])

    pages = exa_contents(["https://exa.ai"], max_characters=5000)
    reply = exa_answer("What makes some LLMs better than others?")

All public functions return plain, JSON-serializable dicts. With --json the CLI
prints exactly that dict; without it you get a compact human digest. Prefer
highlights (the default) over --text when feeding an LLM context; --text is
token-heavy, cap it with --max-chars.

Search types: auto (default, ~1 s), fast, instant, deep-lite, deep,
deep-reasoning (multi-step synthesis, 4-40 s, higher cost; supports
system_prompt and output_schema, which land in payload["output"]).
num_results is 1-100. Category: company | people | publication | news |
personal site | financial report.

Exit codes: 0 ok, 1 API/runtime error, 2 config error (key or package missing).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

PROJECT_DIR = Path(__file__).resolve().parent
SEARCH_TYPES = ("auto", "fast", "instant", "deep-lite", "deep", "deep-reasoning")
ANSWER_MODELS = ("exa", "exa-pro")
_RESULT_FIELDS = (
    "id", "title", "url", "published_date", "author", "score", "crawl_date",
    "text", "summary", "highlights", "highlight_scores",
)


class ConfigError(RuntimeError):
    """Missing configuration: API key or required package."""


class ExaApiError(RuntimeError):
    """An Exa API call failed."""


# ---------------------------------------------------------------- config ----

def _load_dotenv() -> None:
    """Merge project-root .env into os.environ (real env vars win)."""
    env_path = PROJECT_DIR / ".env"
    if not env_path.is_file():
        return
    values: Dict[str, Any] = {}
    try:
        from dotenv import dotenv_values

        values = dict(dotenv_values(env_path))
    except ImportError:
        for raw in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    for key, val in values.items():
        if key and val is not None:
            os.environ.setdefault(key, val)


def _api_key() -> str:
    _load_dotenv()
    key = os.environ.get("EXA_API_KEY", "").strip()
    if not key:
        raise ConfigError(
            "EXA_API_KEY is not set. Add it to " + str(PROJECT_DIR / ".env")
            + " as EXA_API_KEY=<your key> (https://dashboard.exa.ai/api-keys)."
        )
    return key


def _get_exa():
    try:
        from exa_py import Exa
    except ImportError as exc:
        raise ConfigError(
            "exa-py is not installed for this interpreter. Run this helper with the "
            r"project venv ( .\.venv\Scripts\python.exe exa_search.py ... ) or "
            "install it with: uv pip install --python .venv exa-py"
        ) from exc
    return Exa(api_key=_api_key())


def _call(func, *args, **kwargs):
    """Run an SDK call; wrap transport/API errors in one clean ExaApiError."""
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        raise ExaApiError(f"Exa API call failed: {type(exc).__name__}: {exc}") from exc


# --------------------------------------------------------------- helpers ----

def _as_list(value: Union[str, Sequence[str], None], field: str) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [p.strip() for p in value.split(",")]
    else:
        items = [str(p).strip() for p in value]
    items = [p for p in items if p]
    if not items:
        raise ValueError(f"{field} must not be empty")
    return items


def _clean(value: Any, limit: int = 280) -> str:
    return " ".join(str(value).split())[:limit]


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _jsonable(dataclasses.asdict(value))
    if hasattr(value, "__dict__"):
        return {k: _jsonable(v) for k, v in vars(value).items()}
    return str(value)


def _highlight_text(item: Any) -> Any:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("highlight") or item.get("text") or json.dumps(item, ensure_ascii=False)
    return str(item)


def _response_payload(resp: Any, kind: str, label: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten an SDK SearchResponse into a JSON-friendly dict."""
    results: List[Dict[str, Any]] = []
    for r in getattr(resp, "results", None) or []:
        item = {f: getattr(r, f, None) for f in _RESULT_FIELDS}
        item = {k: v for k, v in item.items() if v is not None}
        if isinstance(item.get("highlights"), list):
            item["highlights"] = [_highlight_text(h) for h in item["highlights"]]
        results.append(item)
    payload: Dict[str, Any] = dict(label)
    payload["kind"] = kind
    payload["num_results"] = len(results)
    payload["results"] = results
    for attr in ("search_time", "cost_dollars", "output"):
        val = getattr(resp, attr, None)
        if val is not None:
            payload[attr] = _jsonable(val)
    return payload


def _build_contents(
    highlights: bool,
    text: bool,
    summary: bool,
    max_characters: Optional[int],
    max_age_hours: Optional[int],
) -> Dict[str, Any]:
    built: Dict[str, Any] = {}
    if highlights:
        built["highlights"] = {"max_characters": int(max_characters)} if (max_characters and not text) else True
    if text:
        built["text"] = {"max_characters": int(max_characters)} if max_characters else True
    if summary:
        built["summary"] = True
    if max_age_hours is not None:
        built["max_age_hours"] = int(max_age_hours)
    return built


# ------------------------------------------------------------ public API ----

def exa_search(
    query: str,
    *,
    num_results: int = 10,
    search_type: str = "auto",
    include_domains: Union[str, Sequence[str], None] = None,
    exclude_domains: Union[str, Sequence[str], None] = None,
    category: Optional[str] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    include_text: Union[str, Sequence[str], None] = None,
    exclude_text: Union[str, Sequence[str], None] = None,
    highlights: bool = True,
    text: bool = False,
    summary: bool = False,
    max_characters: Optional[int] = None,
    max_age_hours: Optional[int] = None,
    contents: Union[bool, Dict[str, Any], None] = None,
    system_prompt: Optional[str] = None,
    output_schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Search the web; return {kind, query, num_results, results, ...}.

    Defaults to query-relevant highlights per result (token-friendly for LLMs).
    text=True adds full page text (cap with max_characters); contents=False
    returns links only; contents=<dict> passes raw ContentsOptions verbatim.
    search_type: auto | fast | instant | deep-lite | deep | deep-reasoning.
    system_prompt/output_schema enable grounded structured output (best on the
    deep types); the synthesized result lands in payload["output"].
    """
    query = str(query).strip()
    if not query:
        raise ValueError("query must be a non-empty string")
    num_results = int(num_results)
    if not 1 <= num_results <= 100:
        raise ValueError("num_results must be between 1 and 100")
    if search_type not in SEARCH_TYPES:
        raise ValueError(f"search_type must be one of: {', '.join(SEARCH_TYPES)}")
    exa = _get_exa()
    kwargs: Dict[str, Any] = {"num_results": num_results, "type": search_type}
    if include_domains is not None:
        kwargs["include_domains"] = _as_list(include_domains, "include_domains")
    if exclude_domains is not None:
        kwargs["exclude_domains"] = _as_list(exclude_domains, "exclude_domains")
    if category:
        kwargs["category"] = str(category)
    if start_published_date:
        kwargs["start_published_date"] = str(start_published_date)
    if end_published_date:
        kwargs["end_published_date"] = str(end_published_date)
    if include_text is not None:
        kwargs["include_text"] = _as_list(include_text, "include_text")
    if exclude_text is not None:
        kwargs["exclude_text"] = _as_list(exclude_text, "exclude_text")
    if system_prompt:
        kwargs["system_prompt"] = str(system_prompt)
    if output_schema is not None:
        kwargs["output_schema"] = output_schema
    if contents is not None:
        kwargs["contents"] = contents
    else:
        built = _build_contents(highlights, text, summary, max_characters, max_age_hours)
        if built:
            kwargs["contents"] = built
    resp = _call(exa.search, query, **kwargs)
    return _response_payload(resp, "search", {"query": query})


def exa_contents(
    urls: Union[str, Sequence[str]],
    *,
    text: bool = True,
    highlights: bool = False,
    summary: bool = False,
    max_characters: int = 10000,
    max_age_hours: Optional[int] = None,
) -> Dict[str, Any]:
    """Fetch cleaned content for URLs/domains you already have.

    Returns {kind, urls, num_results, results}. max_age_hours: 0 forces a fresh
    livecrawl, -1 uses cache only, omit for the default cache-then-crawl.
    """
    url_list = _as_list(urls, "urls")
    exa = _get_exa()
    kwargs: Dict[str, Any] = {}
    if text:
        kwargs["text"] = {"max_characters": int(max_characters)} if max_characters else True
    if highlights:
        kwargs["highlights"] = True
    if summary:
        kwargs["summary"] = True
    if max_age_hours is not None:
        kwargs["max_age_hours"] = int(max_age_hours)
    if not kwargs:
        raise ValueError("pick at least one content mode (text, highlights, summary)")
    resp = _call(exa.get_contents, url_list, **kwargs)
    return _response_payload(resp, "contents", {"urls": url_list})


def exa_answer(
    question: str,
    *,
    model: str = "exa",
    system_prompt: Optional[str] = None,
    text: bool = False,
    output_schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ask a grounded question; return {kind, question, model, answer, citations}."""
    question = str(question).strip()
    if not question:
        raise ValueError("question must be a non-empty string")
    if model not in ANSWER_MODELS:
        raise ValueError(f"model must be one of: {', '.join(ANSWER_MODELS)}")
    exa = _get_exa()
    kwargs: Dict[str, Any] = {"model": model}
    if system_prompt:
        kwargs["system_prompt"] = str(system_prompt)
    if text:
        kwargs["text"] = True
    if output_schema is not None:
        kwargs["output_schema"] = output_schema
    resp = _call(exa.answer, question, **kwargs)
    answer = getattr(resp, "answer", None)
    if not isinstance(answer, str):
        answer = json.dumps(_jsonable(answer), ensure_ascii=False, default=str)
    citations = []
    for c in getattr(resp, "citations", None) or []:
        entry = {
            "title": getattr(c, "title", None),
            "url": getattr(c, "url", None),
            "published_date": getattr(c, "published_date", None),
            "author": getattr(c, "author", None),
            "text": _clean(getattr(c, "text", "") or "", 300) or None,
        }
        citations.append({k: v for k, v in entry.items() if v})
    payload: Dict[str, Any] = {
        "kind": "answer",
        "question": question,
        "model": model,
        "answer": answer,
        "citations": citations,
    }
    if getattr(resp, "cost_dollars", None) is not None:
        payload["cost_dollars"] = _jsonable(resp.cost_dollars)
    return payload


# ---------------------------------------------------------------- output ----

def _format_digest(payload: Dict[str, Any]) -> str:
    label = payload.get("query") or ", ".join(str(u) for u in payload.get("urls", []))
    lines = [f"Exa {payload.get('kind')}: {label} -> {payload.get('num_results')} result(s)"]
    for i, r in enumerate(payload.get("results") or [], 1):
        lines.append("")
        lines.append(f"{i}. {r.get('title') or '(no title)'}")
        if r.get("url"):
            lines.append(f"   {r['url']}")
        if r.get("published_date"):
            lines.append(f"   published: {r['published_date']}")
        for h in (r.get("highlights") or [])[:3]:
            lines.append(f"   >> {_clean(h)}")
        if r.get("summary"):
            lines.append(f"   summary: {_clean(r['summary'], 400)}")
        if r.get("text"):
            lines.append(f"   text: {_clean(r['text'], 400)}")
    if payload.get("output") is not None:
        lines.append("")
        lines.append("structured output: " + _clean(json.dumps(payload["output"], ensure_ascii=False, default=str), 800))
    return "\n".join(lines)


def _format_answer(payload: Dict[str, Any]) -> str:
    lines = [f"Exa answer [{payload.get('model')}]:", "", str(payload.get("answer", "")), "", "citations:"]
    for i, c in enumerate(payload.get("citations") or [], 1):
        lines.append(f"  {i}. {c.get('title') or '(no title)'} - {c.get('url')}")
    return "\n".join(lines)


# ------------------------------------------------------------------- CLI ----

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exa_search",
        description="Exa web-search helper: search, fetch contents, or get a grounded answer.",
        epilog=(
            "examples:\n"
            '  exa_search.bat search "Latest news on Nvidia" --num 5 --json\n'
            '  exa_search.bat search "GPU inference startups" --type deep --schema schema.json\n'
            '  exa_search.bat contents https://exa.ai https://docs.exa.ai --max-chars 4000\n'
            '  exa_search.bat answer "What makes some LLMs better than others?"\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("search", help="web search; highlights on by default")
    sp.add_argument("query")
    sp.add_argument("--num", type=int, default=10, metavar="N", help="1-100 results (default 10)")
    sp.add_argument("--type", default="auto", choices=SEARCH_TYPES, dest="search_type", help="search type (default auto)")
    sp.add_argument("--domains", help="comma-separated domains to include")
    sp.add_argument("--exclude-domains", help="comma-separated domains to exclude")
    sp.add_argument("--category", help="company | people | publication | news | personal site | financial report")
    sp.add_argument("--start-date", dest="start_published_date", metavar="YYYY-MM-DD", help="published on/after")
    sp.add_argument("--end-date", dest="end_published_date", metavar="YYYY-MM-DD", help="published on/before")
    sp.add_argument("--include-text", help="comma-separated strings each page must contain")
    sp.add_argument("--exclude-text", help="comma-separated strings to exclude")
    sp.add_argument("--text", action="store_true", help="full page text (token-heavy; pair with --max-chars)")
    sp.add_argument("--max-chars", type=int, metavar="N", help="cap characters per result (text if --text else highlights)")
    sp.add_argument("--summary", action="store_true", help="LLM summary per result")
    sp.add_argument("--max-age-hours", type=int, metavar="H", help="0=always livecrawl, -1=cache only")
    sp.add_argument("--system-prompt", help="synthesis rules for deep types")
    sp.add_argument("--schema", metavar="FILE", help="JSON schema file for structured output (deep types)")
    sp.add_argument("--no-contents", action="store_true", help="links only, no page content")
    sp.add_argument("--json", action="store_true", help="print the raw JSON payload")

    cp = sub.add_parser("contents", help="fetch content for known URLs/domains")
    cp.add_argument("urls", nargs="+", help="URLs or bare domains (e.g. exa.ai)")
    cp.add_argument("--highlights", action="store_true", help="query-relevant excerpts")
    cp.add_argument("--no-text", action="store_true", help="skip text (default: text up to --max-chars)")
    cp.add_argument("--max-chars", type=int, default=10000, metavar="N")
    cp.add_argument("--max-age-hours", type=int, metavar="H", help="0=always livecrawl, -1=cache only")
    cp.add_argument("--json", action="store_true")

    ap = sub.add_parser("answer", help="grounded answer with citations")
    ap.add_argument("question")
    ap.add_argument("--model", choices=ANSWER_MODELS, default="exa")
    ap.add_argument("--system-prompt", help="steer the answer synthesis")
    ap.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "search":
            contents: Union[bool, Dict[str, Any], None] = False if args.no_contents else None
            schema = None
            if args.schema:
                schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
                if not isinstance(schema, dict):
                    raise ValueError("schema file must contain a JSON object")
            payload = exa_search(
                args.query,
                num_results=args.num,
                search_type=args.search_type,
                include_domains=args.domains,
                exclude_domains=args.exclude_domains,
                category=args.category,
                start_published_date=args.start_published_date,
                end_published_date=args.end_published_date,
                include_text=args.include_text,
                exclude_text=args.exclude_text,
                highlights=not (args.no_contents or args.text or args.summary),
                text=args.text,
                summary=args.summary,
                max_characters=args.max_chars,
                max_age_hours=args.max_age_hours,
                contents=contents,
                system_prompt=args.system_prompt,
                output_schema=schema,
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=str) if args.json else _format_digest(payload))
        elif args.command == "contents":
            payload = exa_contents(
                args.urls,
                text=not args.no_text,
                highlights=args.highlights,
                max_characters=args.max_chars,
                max_age_hours=args.max_age_hours,
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=str) if args.json else _format_digest(payload))
        else:
            payload = exa_answer(args.question, model=args.model, system_prompt=args.system_prompt)
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=str) if args.json else _format_answer(payload))
    except ConfigError as exc:
        print(f"CONFIG ERROR: {exc}", file=sys.stderr)
        return 2
    except (ExaApiError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
