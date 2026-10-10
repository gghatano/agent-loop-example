#!/usr/bin/env bash
# ヘッドレスの Ralph Loop。tasks/current.md（または Issue）を目標に、
# check が通るか上限回数に達するまで claude を繰り返し起動する。
#
#   ./scripts/loop.sh 42        # Issue #42 を目標に回す
#   MAX_ITER=5 ./scripts/loop.sh
#
# 上限で止まったら、それ自体が観察材料。/postmortem で分類する。
set -uo pipefail
cd "$(dirname "$0")/.."

ISSUE=${1:-}
MAX_ITER=${MAX_ITER:-8}
CLAUDE_FLAGS=${CLAUDE_FLAGS:---permission-mode acceptEdits}
mkdir -p .agent/logs

if [ -n "$ISSUE" ]; then
  GOAL="/goal #$ISSUE"
else
  GOAL="tasks/current.md の目標を、AGENTS.md の Completion criteria を満たすまで進めて。"
fi

for i in $(seq 1 "$MAX_ITER"); do
  ts=$(date +%Y%m%d-%H%M%S)
  echo "== iteration $i/$MAX_ITER ($ts)"
  # shellcheck disable=SC2086
  claude -p "$GOAL
前回までの進捗は tasks/current.md と git log にある。今回の1回で進められるところまで進め、tasks/current.md を更新して終わること。" \
    $CLAUDE_FLAGS > ".agent/logs/$ts.md" 2>&1

  if ./scripts/check.sh > .agent/logs/$ts.check 2>&1; then
    echo "check passed at iteration $i"
    tail -n 1 .agent/logs/$ts.check
    exit 0
  fi
  head -n 1 .agent/logs/$ts.check
done

echo "MAX_ITER reached without passing check. Run /postmortem on .agent/logs/."
exit 1
