#!/usr/bin/env bash
# ヘッドレスの Ralph Loop。Issue（または tasks/current.md）を目標に、
# check が通るか、AI がエスカレーションするか、上限回数に達するまで claude を繰り返し起動する。
#
#   ./scripts/loop.sh 42        # Issue #42 を目標に回す
#   MAX_ITER=5 ./scripts/loop.sh
#
# 止まり方は3つ。どれも観察材料なので、止まったら /postmortem で分類する。
#   exit 0: check が通った
#   exit 2: AI が .agent/BLOCKED を書いてエスカレーションした / 1周まるごと何も変わらなかった
#   exit 1: 上限回数に達した
set -uo pipefail
cd "$(dirname "$0")/.."

ISSUE=${1:-}
MAX_ITER=${MAX_ITER:-8}
mkdir -p .agent/logs
rm -f .agent/BLOCKED

# ヘッドレス実行では、未信頼ワークスペースだと settings.json の allow が無視される。
# ループが AI に渡す権限はここで明示する（docs/failures.md 2026-10-10 #1）。
ALLOWED=(
  "Bash(./scripts/check.sh)"
  "Bash(uv run:*)" "Bash(uv sync:*)"
  "Bash(git status:*)" "Bash(git diff:*)" "Bash(git log:*)"
  "Bash(git switch:*)" "Bash(git checkout -b:*)" "Bash(git add:*)" "Bash(git commit:*)"
)

# Issue 本文は人間側で取ってきて渡す。AI に gh の認証を持たせない。
if [ -n "$ISSUE" ]; then
  issue_file="tasks/issue-$ISSUE.md"
  if [ ! -f "$issue_file" ]; then
    gh issue view "$ISSUE" > "$issue_file" 2>/dev/null || {
      rm -f "$issue_file"
      echo "Issue #$ISSUE を取得できない。gh を認証するか、本文を $issue_file に置くこと。" >&2
      exit 2
    }
  fi
  GOAL="/goal $ISSUE"
else
  GOAL="tasks/current.md の目標を、AGENTS.md の Completion criteria を満たすまで進めて。"
fi

NOTE="これはヘッドレスのループ実行で、人間は途中で応答しない。前回までの進捗は tasks/current.md と git log にある。
今回の1回で進められるところまで進め、tasks/current.md を更新して終わること。
人間の判断が要る（AGENTS.md の Escalation に該当する）ときは、理由と選択肢を .agent/BLOCKED に書いて終わること。"

fingerprint() { { git rev-parse HEAD; git status --porcelain; git diff; } | sha1sum; }

for i in $(seq 1 "$MAX_ITER"); do
  ts=$(date +%Y%m%d-%H%M%S)
  echo "== iteration $i/$MAX_ITER ($ts)"
  before=$(fingerprint)
  claude -p "$GOAL" --append-system-prompt "$NOTE" \
    --permission-mode acceptEdits --allowedTools "${ALLOWED[@]}" \
    > ".agent/logs/$ts.md" 2>&1

  if ./scripts/check.sh > ".agent/logs/$ts.check" 2>&1; then
    echo "check passed at iteration $i"
    tail -n 1 ".agent/logs/$ts.check"
    exit 0
  fi
  head -n 1 ".agent/logs/$ts.check"

  if [ -f .agent/BLOCKED ]; then
    echo "AI escalated:"; cat .agent/BLOCKED
    exit 2
  fi
  if [ "$before" = "$(fingerprint)" ]; then
    echo "no change in this iteration. Read .agent/logs/$ts.md, then /postmortem."
    exit 2
  fi
done

echo "MAX_ITER reached without passing check. Run /postmortem on .agent/logs/."
exit 1
