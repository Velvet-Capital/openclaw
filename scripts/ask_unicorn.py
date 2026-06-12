#!/usr/bin/env python3
"""
Velvet Unicorn — openclaw skill client.

Calls the API-key-gated Velvet Unicorn endpoints and prints the JSON response.
All endpoints authenticate with a vuk_ API key (create one at
https://vu.velvetdao.xyz/agent → My Profile → API Keys; 1,000 free requests).

Auth:
  Set the key via env:  VELVET_API_KEY=vuk_...   (or pass --api-key)
  Base URL override:     VELVET_API_URL=https://vu.velvetdao.xyz/agent-api

Commands:
  ask        General DeFi/crypto chat            POST /v1/ask        {question, context?, userid?, userid_sol?, previous_questions?}
  token      Multi-agent token analysis          POST /v1/token      {token}
  trending   Trending-token discovery            POST /v1/trending   {instruction?}
  swap       NL swap -> signable tx               POST /v1/swap       {instruction}
  wallet     Wallet analysis                     POST /v1/wallet_analysis {wallet}
  usage      Remaining free-request quota        GET  /v1/usage

Examples:
  export VELVET_API_KEY=vuk_xxx
  python3 ask_unicorn.py ask --question "What's trending on Base?"
  python3 ask_unicorn.py token --token VELVET
  python3 ask_unicorn.py trending --instruction "meme coins on Solana"
  python3 ask_unicorn.py swap --instruction "Swap 10 USDC to VELVET on base from wallet 0x1234..."
  python3 ask_unicorn.py wallet --wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
  python3 ask_unicorn.py usage

  # Back-compat: no command defaults to `ask`
  python3 ask_unicorn.py --question "Analyze $VELVET" --context "swing trader"
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

DEFAULT_BASE_URL = "https://vu.velvetdao.xyz/agent-api"
COMMANDS = ("ask", "token", "trending", "swap", "wallet", "usage")


def _eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def _request(method: str, url: str, payload: Optional[Dict[str, Any]],
             headers: Dict[str, str], timeout_s: int) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url=url, data=data, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining is not None:
                _eprint(f"[quota] {remaining} requests remaining")
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"answer": raw}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        detail = body
        try:
            detail = json.loads(body).get("error", body)
        except json.JSONDecodeError:
            pass
        if e.code == 401:
            raise RuntimeError("Unauthorized (401): missing or invalid API key.") from e
        if e.code == 402:
            raise RuntimeError("Quota exhausted (402): create a new key or top up.") from e
        raise RuntimeError(f"HTTP {e.code} from {url}: {detail}") from e
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


def build_request(args: argparse.Namespace) -> (str, str, Optional[Dict[str, Any]]):
    """Return (method, path, payload) for the chosen command."""
    cmd = args.command
    if cmd == "ask":
        return "POST", "/v1/ask", {
            "question": args.question,
            "context": args.context or None,
            "userid": args.userid or None,
            "userid_sol": args.userid_sol or None,
            "previous_questions": parse_json_list(args.previous_questions),
        }
    if cmd == "token":
        return "POST", "/v1/token", {"token": args.token}
    if cmd == "trending":
        return "POST", "/v1/trending", {"instruction": args.instruction or ""}
    if cmd == "swap":
        return "POST", "/v1/swap", {"instruction": args.instruction}
    if cmd == "wallet":
        return "POST", "/v1/wallet_analysis", {"wallet": args.wallet}
    if cmd == "usage":
        return "GET", "/v1/usage", None
    raise ValueError(f"Unknown command: {cmd}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Call Velvet Unicorn API-key endpoints and print the JSON response.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--api-key", default=os.getenv("VELVET_API_KEY", os.getenv("VELVET_UNICORN_API_KEY", "")),
                    help="vuk_ API key (default: $VELVET_API_KEY).")
    ap.add_argument("--base-url", default=os.getenv("VELVET_API_URL", DEFAULT_BASE_URL),
                    help=f"API base URL (default: {DEFAULT_BASE_URL}).")
    ap.add_argument("--timeout", type=int, default=120)

    sub = ap.add_subparsers(dest="command")

    p_ask = sub.add_parser("ask", help="General DeFi/crypto chat")
    p_ask.add_argument("--question", required=True)
    p_ask.add_argument("--context", default="")
    p_ask.add_argument("--userid", default="")
    p_ask.add_argument("--userid-sol", dest="userid_sol", default="")
    p_ask.add_argument("--previous-questions", default="[]",
                       help='JSON list (preferred) or comma-separated string')

    p_token = sub.add_parser("token", help="Multi-agent token analysis")
    p_token.add_argument("--token", required=True, help="Symbol (VELVET) or contract address")

    p_trend = sub.add_parser("trending", help="Trending-token discovery")
    p_trend.add_argument("--instruction", default="", help="Optional NL filter, e.g. 'on Base'")

    p_swap = sub.add_parser("swap", help="Natural-language swap -> signable tx")
    p_swap.add_argument("--instruction", required=True,
                        help="Include the wallet address, e.g. 'Swap 10 USDC to VELVET on base from wallet 0x...'")

    p_wallet = sub.add_parser("wallet", help="Wallet analysis")
    p_wallet.add_argument("--wallet", required=True, help="0x... (EVM) or base58 (Solana)")

    sub.add_parser("usage", help="Remaining free-request quota")
    return ap


def main() -> int:
    argv = sys.argv[1:]
    # Back-compat: if no subcommand is given (first token is a flag or empty), default to `ask`.
    if not argv or (argv[0].startswith("-") and argv[0] not in ("-h", "--help")):
        argv = ["ask"] + argv

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 2

    api_key = (args.api_key or "").strip()
    if not api_key:
        _eprint("ERROR: no API key. Set VELVET_API_KEY=vuk_... or pass --api-key. "
                "Create one at https://vu.velvetdao.xyz/agent")
        return 2

    method, path, payload = build_request(args)
    url = args.base_url.rstrip("/") + path
    headers = {
        "Authorization": f"Bearer {api_key}",
        # A real UA — the API is behind Cloudflare, which blocks the default urllib agent.
        "User-Agent": "velvet-openclaw/1.0 (+https://vu.velvetdao.xyz)",
        "Accept": "application/json",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"

    try:
        out = _request(method, url, payload, headers=headers, timeout_s=args.timeout)
    except Exception as e:
        out = {"error": str(e), "answer": f"ERROR: {e}"}

    if not isinstance(out, dict):
        out = {"answer": str(out)}

    print(json.dumps(out, ensure_ascii=False))
    return 0 if "error" not in out else 1


if __name__ == "__main__":
    raise SystemExit(main())
