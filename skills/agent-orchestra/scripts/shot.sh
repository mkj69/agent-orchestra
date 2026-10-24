#!/usr/bin/env bash
set -euo pipefail
usage() { echo 'Usage: shot.sh URL OUTPUT.png [WIDTH HEIGHT]. Set ORCH_CLIP=x,y,width,height to crop without scrolling.' >&2; exit 2; }
[[ $# -ge 2 && $# -le 4 ]] || usage
url=$1; output=$(realpath -m "$2")
width=${3:-1440}; height=${4:-3200}
[[ "$width" =~ ^[0-9]+$ && "$height" =~ ^[0-9]+$ ]] || usage
(( width >= 320 && height >= 320 )) || usage
[[ "$url" != *'#'* ]] || { echo 'Avoid anchors in headless screenshots' >&2; exit 2; }
chrome=${ORCH_CHROME:-}
if [[ -z "$chrome" ]]; then
  chrome=$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)
fi
[[ -n "$chrome" ]] || { echo 'Chrome or Chromium not found' >&2; exit 2; }
mkdir -p "$(dirname "$output")"
"$chrome" --headless --disable-gpu --hide-scrollbars --no-first-run --window-size="$width,$height" --screenshot="$output" "$url" >/dev/null 2>&1
[[ -s "$output" ]] || { echo "Screenshot missing: $output" >&2; exit 1; }
if [[ -n "${ORCH_CLIP:-}" ]]; then
  python3 - "$output" "$ORCH_CLIP" <<'PY'
import sys
from PIL import Image

path, spec = sys.argv[1:]
try:
    x, y, width, height = (int(part) for part in spec.split(','))
except ValueError as exc:
    raise SystemExit('ORCH_CLIP must be x,y,width,height') from exc
if min(x, y) < 0 or min(width, height) < 1:
    raise SystemExit('ORCH_CLIP values are out of range')
with Image.open(path) as source:
    if x + width > source.width or y + height > source.height:
        raise SystemExit('ORCH_CLIP exceeds screenshot bounds')
    source.crop((x, y, x + width, y + height)).save(path)
PY
fi
printf '%s\n' "$output"
