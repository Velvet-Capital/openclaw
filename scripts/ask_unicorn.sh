#!/usr/bin/env bash
set -euo pipefail

QUESTION="${1:-}"
CONTEXT="${2:-}"
USERID="${3:-}"
USERID_SOL="${4:-}"
PREV="${5:-[]}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/ask_unicorn.py" \
  --question "${QUESTION}" \
  --context "${CONTEXT}" \
  --userid "${USERID}" \
  --userid-sol "${USERID_SOL}" \
  --previous-questions "${PREV}"
