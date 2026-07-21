#!/bin/sh
set -eu
WS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$WS_ROOT/scripts/ws.py" "$@"
