#!/usr/bin/env bash
# Bump the shared mender-mcu pin across DD_PIN + sibling product west.yml files.
#
# Usage (from a mender-mcu checkout):
#   ./scripts/bump-consumer-pins.sh <full-40-char-sha>           # dry-run
#   ./scripts/bump-consumer-pins.sh <full-40-char-sha> --apply   # write files
#
# Expects sibling checkouts under DD_ROOT (default /data_drive/dd):
#   zephyr-rt1186-f1
#   zephyr-rt1170-room-display
#   zephyr-rt1170-eink
#
# Does not git commit/push — review, then commit each repo (and retag dd-pin-*).
set -euo pipefail

NEW=${1:?usage: bump-consumer-pins.sh <full-sha> [--apply]}
APPLY=0
[[ "${2:-}" == "--apply" ]] && APPLY=1

if [[ ! "$NEW" =~ ^[0-9a-fA-F]{40}$ ]]; then
  echo "error: need full 40-char SHA, got: $NEW" >&2
  exit 1
fi
NEW=$(echo "$NEW" | tr 'A-F' 'a-f')
SHORT=${NEW:0:7}

ROOT=$(cd "$(dirname "$0")/.." && pwd)
DD_ROOT=${DD_ROOT:-/data_drive/dd}

CONSUMERS=(
  "zephyr-rt1186-f1|f1-controller/west.yml"
  "zephyr-rt1170-room-display|room-display/west.yml"
  "zephyr-rt1170-eink|mender-mcu-integration/west.yml"
)

OLD=$(tr -d '[:space:]' < "$ROOT/DD_PIN" || true)
echo "mender-mcu pin: ${OLD:-"(none)"} → $NEW"
echo "tag suggestion: dd-pin-$SHORT  (annotate at $NEW)"
echo

replace_revision() {
  local file=$1
  python3 - "$file" "$NEW" <<'PY'
import re, sys
path, new = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
pat = re.compile(
    r"(?ms)(^[ \t]*-[ \t]*name:[ \t]*mender-mcu\b.*?^[ \t]*revision:[ \t]*)(['\"]?)([0-9a-fA-F]+)(['\"]?)",
)
m = pat.search(text)
if not m:
    sys.stderr.write(f"error: no mender-mcu revision in {path}\n")
    sys.exit(2)
out = pat.sub(rf"\g<1>{new}", text, count=1)
if out == text:
    sys.stderr.write(f"error: revision unchanged in {path}\n")
    sys.exit(3)
open(path, "w", encoding="utf-8").write(out)
print(f"updated {path}")
PY
}

update_pin_policy_table() {
  local file=$1
  python3 - "$file" "$NEW" "$SHORT" <<'PY'
import re, sys
path, new, short = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(path, encoding="utf-8").read()
text2, n = re.subn(
    r"(\|\s*\*\*West `revision`\*\*\s*\|\s*\*\*`)[0-9a-fA-F]{40}(`\*\*[^\n]*)",
    rf"\g<1>{new}\2",
    text,
    count=1,
)
if n != 1:
    sys.stderr.write(f"warning: PIN-POLICY West revision row not updated ({n} matches)\n")
text3, n2 = re.subn(
    r"(\|\s*Short\s*\|\s*`)[0-9a-fA-F]+(`)",
    rf"\g<1>{short}\2",
    text2,
    count=1,
)
if n2 != 1:
    sys.stderr.write(f"warning: PIN-POLICY Short row not updated ({n2} matches)\n")
text4, n3 = re.subn(
    r"(dd-pin-)[0-9a-fA-F]+",
    rf"\g<1>{short}",
    text3,
)
open(path, "w", encoding="utf-8").write(text4)
print(f"updated {path} (revision rows={n}, short={n2}, tag refs={n3})")
PY
}

if [[ "$APPLY" -eq 0 ]]; then
  echo "DRY-RUN (pass --apply to write):"
  echo "  $ROOT/DD_PIN"
  echo "  $ROOT/PIN-POLICY.md"
  for entry in "${CONSUMERS[@]}"; do
    IFS='|' read -r repo rel <<<"$entry"
    echo "  $DD_ROOT/$repo/$rel"
  done
  exit 0
fi

printf '%s\n' "$NEW" > "$ROOT/DD_PIN"
echo "wrote $ROOT/DD_PIN"
update_pin_policy_table "$ROOT/PIN-POLICY.md"

for entry in "${CONSUMERS[@]}"; do
  IFS='|' read -r repo rel <<<"$entry"
  path="$DD_ROOT/$repo/$rel"
  if [[ ! -f "$path" ]]; then
    echo "error: missing consumer checkout: $path" >&2
    exit 1
  fi
  replace_revision "$path"
done

echo
echo "Next:"
echo "  1) git -C $ROOT tag -a dd-pin-$SHORT $NEW -m 'Shared Zephyr 4.4 mender-mcu pin'"
echo "  2) commit/push mender-mcu (DD_PIN + PIN-POLICY) and each consumer west.yml"
echo "  3) git push <remote> dd-pin-$SHORT"
echo "  4) run smoke matrix in PIN-POLICY.md"
