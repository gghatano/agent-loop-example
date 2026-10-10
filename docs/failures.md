# Failure log

AI が失敗したら、原因を**1つだけ**選んで1行追記する（`/postmortem` が書く）。
昇格したら `→` の先に移した場所を書く。昇格しなかった行も消さない（再発頻度の材料になる）。

| 分類 | 意味 | 打ち手 |
|---|---|---|
| Context | 固有の制約を知らなかった | AGENTS.md / docs/ に1行 |
| Permission | 権限・コマンド・環境がなかった | settings / CI / 環境 |
| Evaluation | 間違いを check が通した | scripts/check.sh に検査を追加 |
| Model | 上記を満たしても解けない | タスク分割・人間が持つ・再挑戦日を書く |

## Log

| 日付 | Issue | 分類 | 何が起きたか（1行） | → 昇格先 |
|---|---|---|---|---|
| YYYY-MM-DD | #0 | Context | 例) 金額を float で扱った。このプロジェクトは整数円 | AGENTS.md#Project rules |
