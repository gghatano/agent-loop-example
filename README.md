# agent-loop-template

AI に仕事を渡せる形へ、開発プロセスそのものを設計するためのリポジトリテンプレート。

人間が持つのは **Goal・評価・エスカレーション基準** の3つだけ。
**実装・観察・修正** は AI がループで回す。

```
Goal (Issue) ─▶ Action ─▶ Observation ─▶ Evaluation (scripts/check.sh) ─▶ Correction ─┐
                  ▲                                                                   │
                  └───────────────────────────────────────────────────────────────────┘
```

## 使い始める（最初の30分）

1. `AGENTS.md` の `TODO` を埋める。**このプロジェクト固有の事情だけ**。一般知識は書かない。
2. `scripts/check.sh` の `TODO` を埋め、`./scripts/check.sh` が通る状態にする。これが唯一の評価関数になる。
3. 最初のタスクを Issue（テンプレート「Agent task」）で書く。Done は機械判定できる形で。
4. 細かい手順を書かずに、まず一度丸投げする: `/goal #<issue番号>`
5. 失敗したら `/postmortem` で原因を4分類して `docs/failures.md` に記録する。

docs/ は空のままでいい。AI が実際に失敗した箇所だけが、知識として昇格していく。

## 何がどこにあるか

| ファイル | 持ち主 | 役割 |
|---|---|---|
| `AGENTS.md` | 人間 | 固有の制約・完了条件・エスカレーション基準。短く保つ |
| `scripts/check.sh` | 人間 | 評価関数。AI・Stop hook・CI がすべてこれを呼ぶ |
| `.github/ISSUE_TEMPLATE/` | 人間 | AI の仕事単位（Goal / Done / Constraints） |
| `tasks/current.md` | AI | 今のループの作業メモ。Issue が正、こちらは使い捨て |
| `docs/failures.md` | AI→人間 | 失敗の4分類ログ。昇格判断の材料 |
| `docs/decisions.md` | 両方 | 後から理由が分からなくなる判断だけを残す |
| `.claude/hooks/stop-gate.sh` | — | 変更があるのに check が赤いまま止まろうとしたら差し戻す |
| `scripts/loop.sh` | — | ヘッドレスで回す Ralph Loop（上限回数つき） |

## スキル

- `/goal <#issue>` — Issue の Done を満たすまで実装→検証→修正を回し、PR を出す
- `/explore <観点>` — コードベースを調査し、見つかった問題を Umbrella Issue の下書きにまとめる
- `/postmortem` — 直前の失敗を Context / Permission / Evaluation / Model に分類して記録
- `/unlearn` — AGENTS.md・スキル・docs を棚卸しし、もう効いていないルールの削除を提案

## 失敗の4分類と打ち手

| 分類 | 症状 | 打ち手 |
|---|---|---|
| Context | 固有の制約を知らなかった | `AGENTS.md` か `docs/` に**1行**昇格 |
| Permission | 必要なコマンド・権限・秘密情報がなかった | `.claude/settings.json` / CI / 環境を直す |
| Evaluation | 間違っていたのに check が緑だった | `scripts/check.sh` にテスト・検査を足す |
| Model | 上3つを満たしても解けない | タスクを割る。人間が持つ。半年後に再挑戦 |

プロンプト改善が効くのは Context だけ。残り3つにプロンプトで対処しない。
