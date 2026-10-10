#!/usr/bin/env bash
# 唯一の評価関数。AI・Stop hook・CI はすべてこれを呼ぶ。
# 「いい感じ」を判定させない。通るか通らないかだけを返す。
#
# 各ステップは STEPS に「名前|コマンド」で並べる。
# TODO: プロジェクトに合わせて書き換える。未設定なら自動検出に任せる。
set -uo pipefail
cd "$(dirname "$0")/.."

STEPS=(
  # "lint|uv run ruff check ."
  # "type|uv run mypy src"
  # "test|uv run pytest -q"
  # "vrt|pnpm vrt"            # 見た目の差分 0 を完了条件にするなら
)

if [ ${#STEPS[@]} -eq 0 ]; then
  if [ -f pyproject.toml ]; then
    command -v ruff >/dev/null || [ -x .venv/bin/ruff ] && STEPS+=("lint|uv run ruff check .")
    STEPS+=("test|uv run pytest -q")
  elif [ -f package.json ]; then
    for s in lint typecheck test; do
      jq -e ".scripts.\"$s\"" package.json >/dev/null 2>&1 && STEPS+=("$s|npm run -s $s")
    done
  fi
fi

if [ ${#STEPS[@]} -eq 0 ]; then
  echo "CHECK: FAIL no steps configured (edit STEPS in scripts/check.sh)"
  exit 1
fi

mkdir -p .agent
log=.agent/check.log
: > "$log"
summary=()
failed=0
for entry in "${STEPS[@]}"; do
  name=${entry%%|*}
  cmd=${entry#*|}
  echo "::group::$name ($cmd)" >> "$log"
  if bash -c "$cmd" >> "$log" 2>&1; then
    summary+=("$name=ok")
  else
    summary+=("$name=FAIL")
    failed=1
  fi
  echo "::endgroup::" >> "$log"
done

if [ $failed -eq 0 ]; then
  echo "CHECK: PASS ${summary[*]}"
else
  echo "CHECK: FAIL ${summary[*]}"
  echo "--- tail of $log ---"
  tail -n 60 "$log"
fi
exit $failed
