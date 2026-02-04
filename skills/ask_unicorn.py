#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List

DEFAULT_ENDPOINT = "https://gentweet.velvetdao.xyz/ask"

def _eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)

def post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout_s: int) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"meta_category": 0, "vu_category": None, "answer": raw, "txdata": None}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} from {url}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error calling {url}: {e}") from e

def parse_json_list(s: str) -> List[str]:
    s = (s or "").strip()
    if not s:
        return []
    try:
        v = json.loads(s)
        if isinstance(v, list):
            return [str(x) for x in v]
    except json.JSONDecodeError:
        pass
    return [p.strip() for p in s.split(",") if p.strip()]

def main() -> int:
    ap = argparse.ArgumentParser(description="Call Velvet Unicorn /ask endpoint and print JSON response.")
    ap.add_argument("--question", required=False, default="")
    ap.add_argument("--context", required=False, default="")
    ap.add_argument("--userid", required=False, default="")
    ap.add_argument("--userid-sol", dest="userid_sol", required=False, default="")
    ap.add_argument("--previous-questions", required=False, default="[]",
                    help='JSON list (preferred) or comma-separated string')
    ap.add_argument("--endpoint", required=False, default=os.getenv("VELVET_UNICORN_ENDPOINT", DEFAULT_ENDPOINT))
    ap.add_argument("--timeout", type=int, required=False, default=60)
    ap.add_argument("--stdin", action="store_true",
                    help="Read full payload JSON from stdin; CLI flags become defaults.")
    args = ap.parse_args()

    if args.stdin:
        try:
            incoming = json.loads(sys.stdin.read() or "{}")
            if not isinstance(incoming, dict):
                raise ValueError("stdin JSON must be an object")
        except Exception as e:
            _eprint(f"Failed to read payload from stdin: {e}")
            return 2
        payload = incoming
        payload.setdefault("question", args.question)
        payload.setdefault("context", args.context)
        payload.setdefault("userid", args.userid)
        payload.setdefault("userid_sol", args.userid_sol)
        payload.setdefault("previous_questions", parse_json_list(args.previous_questions))
    else:
        payload = {
            "question": args.question,
            "context": args.context,
            "userid": args.userid or None,
            "userid_sol": args.userid_sol or None,
            "previous_questions": parse_json_list(args.previous_questions),
        }

    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("VELVET_UNICORN_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        out = post_json(args.endpoint, payload, headers=headers, timeout_s=args.timeout)
    except Exception as e:
        out = {"meta_category": 0, "vu_category": None, "answer": f"ERROR: {e}", "txdata": None}

    if not isinstance(out, dict):
        out = {"meta_category": 0, "vu_category": None, "answer": str(out), "txdata": None}

    out.setdefault("meta_category", 0)
    out.setdefault("vu_category", None)
    out.setdefault("answer", "")
    out.setdefault("txdata", None)

    print(json.dumps(out, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
