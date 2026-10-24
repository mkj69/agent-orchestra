#!/usr/bin/env bash
set -euo pipefail
# Configure ORCH_BUILD_CMD and ORCH_PREVIEWS_FILE. Each manifest line is NAME<TAB>SOURCE_DIR.
repo=${ORCH_REPO:-$PWD}
site=${ORCH_SITE_DIR:-"$repo/site"}
manifest=${ORCH_PREVIEWS_FILE:-"$repo/notes/previews.tsv"}
build=${ORCH_BUILD_CMD:-}
[[ -n "$build" ]] || { echo 'Set ORCH_BUILD_CMD to an executable build script' >&2; exit 2; }
[[ -x "$build" ]] || { echo "Build script is not executable: $build" >&2; exit 2; }
"$build"
mkdir -p "$site/preview"
if [[ -f "$manifest" ]]; then
  while IFS=$'\t' read -r name source; do
    [[ -z "$name" || "$name" == \#* ]] && continue
    [[ "$name" =~ ^[A-Za-z0-9_-]+$ && -n "$source" ]] || { echo "Invalid preview line: $name" >&2; exit 2; }
    [[ -d "$source" ]] || { echo "Missing preview source: $source" >&2; exit 2; }
    source_real=$(realpath "$source")
    dest_real=$(realpath -m "$site/preview/$name")
    [[ "$source_real" != "$dest_real" && "$source_real" != "$dest_real/"* ]] || {
      echo 'Preview source cannot be inside its destination' >&2; exit 2;
    }
    rm -rf -- "$site/preview/$name"
    cp -a -- "$source" "$site/preview/$name"
  done < "$manifest"
fi
printf 'Built %s and attached previews\n' "$site"
