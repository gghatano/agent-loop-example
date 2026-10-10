#!/usr/bin/env bash
# Stop hook: コードを変えたのに check が赤いまま止まろうとしたら差し戻す。
# 無限ループを避けるため、連続差し戻しは MAX 回まで。超えたら止めて人間に返す。
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"

MAX=3
state=.agent/stop-attempts
mkdir -p .agent

# 変更がなければ（質問への回答だけなど）評価しない
if [ -z "$(git status --porcelain -- . ':!.agent' ':!tasks' ':!docs' 2>/dev/null)" ]; then
  rm -f "$state"; exit 0
fi

if out=$(./scripts/check.sh 2>&1); then
  rm -f "$state"; exit 0
fi

n=$(( $(cat "$state" 2>/dev/null || echo 0) + 1 ))
echo "$n" > "$state"
if [ "$n" -gt $((MAX + 1)) ]; then
  rm -f "$state"; exit 0          # エスカレーション報告を書いたあとの終了は通す
fi
if [ "$n" -gt "$MAX" ]; then
  echo "check が ${MAX} 回続けて赤いまま。これ以上直そうとせず、AGENTS.md の Escalation に従って状況・試したこと・選択肢を要約し、人間に返して終了すること。" >&2
  exit 2
fi

{
  echo "まだ完了していない（差し戻し $n/$MAX）。scripts/check.sh の結果:"
  echo "$out" | tail -n 40
  echo "原因を直してから終了すること。直せない理由があるなら、それを報告して終了してよい。"
} >&2
exit 2
