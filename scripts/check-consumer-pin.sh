#!/usr/bin/env bash
# Verify a consumer west.yml pins DynamicDevices/mender-mcu to the canonical DD_PIN.
#
# Usage:
#   ./scripts/check-consumer-pin.sh <path-to-west.yml>
#   curl -fsSL …/scripts/check-consumer-pin.sh | bash -s -- f1-controller/west.yml
#
# Env:
#   MENDER_MCU_PIN_BRANCH   branch hosting DD_PIN / PIN-POLICY (default: feature/zephyr-ram-stage-on-main)
#   MENDER_MCU_DD_PIN_URL   override raw DD_PIN URL
#   MENDER_MCU_DD_PIN_FILE  read pin from this file instead of URL
#   MENDER_MCU_PIN_POLICY_URL  override policy URL shown on drift (optional)
set -euo pipefail

WEST_YML=${1:?usage: check-consumer-pin.sh <west.yml>}
PIN_BRANCH=${MENDER_MCU_PIN_BRANCH:-feature/zephyr-ram-stage-on-main}
PIN_URL=${MENDER_MCU_DD_PIN_URL:-https://raw.githubusercontent.com/DynamicDevices/mender-mcu/${PIN_BRANCH}/DD_PIN}
POLICY_URL=${MENDER_MCU_PIN_POLICY_URL:-https://github.com/DynamicDevices/mender-mcu/blob/${PIN_BRANCH}/PIN-POLICY.md}

if [[ ! -f "$WEST_YML" ]]; then
  echo "error: west.yml not found: $WEST_YML" >&2
  exit 1
fi

ACTUAL=$(python3 - "$WEST_YML" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
# Match the mender-mcu project block, then its revision (full SHA preferred).
m = re.search(
    r"(?ms)^[ \t]*-[ \t]*name:[ \t]*mender-mcu\b.*?^[ \t]*revision:[ \t]*['\"]?([0-9a-fA-F]+)['\"]?",
    text,
)
if not m:
    sys.stderr.write(f"error: no mender-mcu revision in {path}\n")
    sys.exit(2)
print(m.group(1).lower())
PY
)

if [[ ${#ACTUAL} -ne 40 ]]; then
  echo "error: mender-mcu revision must be a full 40-char SHA (got ${#ACTUAL}: $ACTUAL)" >&2
  echo "hint: abbreviated SHAs break shallow CI west update" >&2
  exit 3
fi

EXPECTED=""
PIN_SRC=""
if [[ -n "${MENDER_MCU_DD_PIN_FILE:-}" ]]; then
  EXPECTED=$(tr -d '[:space:]' < "$MENDER_MCU_DD_PIN_FILE" | tr 'A-F' 'a-f')
  PIN_SRC="$MENDER_MCU_DD_PIN_FILE"
else
  # Prefer local DD_PIN when this script lives in a mender-mcu checkout.
  _src=${BASH_SOURCE[0]:-}
  if [[ -n "$_src" && -f "$_src" ]]; then
    _root=$(cd "$(dirname "$_src")/.." && pwd)
    if [[ -f "$_root/DD_PIN" ]]; then
      EXPECTED=$(tr -d '[:space:]' < "$_root/DD_PIN" | tr 'A-F' 'a-f')
      PIN_SRC="$_root/DD_PIN"
    fi
  fi
fi
if [[ -z "$EXPECTED" ]]; then
  EXPECTED=$(curl -fsSL "$PIN_URL" | tr -d '[:space:]' | tr 'A-F' 'a-f')
  PIN_SRC="$PIN_URL"
fi

if [[ ! "$EXPECTED" =~ ^[0-9a-f]{40}$ ]]; then
  echo "error: DD_PIN from $PIN_SRC is not a 40-char SHA (got: $EXPECTED)" >&2
  exit 4
fi

if [[ "$ACTUAL" != "$EXPECTED" ]]; then
  echo "error: mender-mcu pin drift" >&2
  echo "  west.yml ($WEST_YML): $ACTUAL" >&2
  echo "  DD_PIN ($PIN_SRC):    $EXPECTED" >&2
  echo "  policy: $POLICY_URL" >&2
  exit 5
fi

echo "ok: mender-mcu @$ACTUAL matches DD_PIN ($PIN_SRC)"
