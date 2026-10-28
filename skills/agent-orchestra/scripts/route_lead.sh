#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 || ! ${ORCH_WEEKLY_USAGE_PERCENT:-} =~ ^[0-9]+$ ]]; then
  echo 'Usage: ORCH_WEEKLY_USAGE_PERCENT=0..100 route_lead.sh CLAUDE_ARGS...' >&2
  exit 2
fi
usage=$((10#$ORCH_WEEKLY_USAGE_PERCENT))
if (( usage > 100 )); then
  echo 'ORCH_WEEKLY_USAGE_PERCENT must be between 0 and 100' >&2
  exit 2
fi
launcher=${ORCH_SUBSCRIPTION_CLAUDE:-claude}
if (( usage >= 80 )); then
  launcher=${ORCH_API_CLAUDE:-}
  if [[ -z "$launcher" ]]; then
    echo 'Set ORCH_API_CLAUDE to a configured API-gateway launcher' >&2
    exit 2
  fi
fi
duration=${ORCH_LEAD_TIMEOUT:-8h}
timeout "$duration" true || { echo 'Invalid ORCH_LEAD_TIMEOUT' >&2; exit 2; }
exec timeout "$duration" "$launcher" "$@"
