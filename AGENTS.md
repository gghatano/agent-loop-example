# AGENTS.md

このファイルには**このプロジェクト固有の事情だけ**を書く。
言語・フレームワーク・ツールの一般的な使い方は書かない（モデルは知っている）。
1行足すときは、`docs/failures.md` の該当行を根拠として残す。

## Project rules
<!-- TODO: 例を消して自分の制約に置き換える -->
- TODO: 例) 既存の公開 API のシグネチャを壊さない
- TODO: 例) 新規依存を追加するときは PR 本文に理由を書く
- TODO: 例) API を変えたら `openapi.yaml` も更新する

## Completion criteria
タスクは次をすべて満たしたときだけ完了とする。満たせないまま完了と報告しない。
- `./scripts/check.sh` が exit 0
- Issue の `Done` の各項目について、満たした証拠（コマンドと結果）を PR に書いた
- Issue の `Constraints` に反する変更がない

## Escalation
次の場合は作業を止め、状況と選択肢を書いて人間に返す。推測で進めない。
- `Constraints` を破らないと `Done` を満たせない
- 同じ check の失敗を3回連続で直せない
- 秘密情報・本番環境・課金が絡む操作が必要
- Issue の `Done` が曖昧で、2通り以上の解釈がある

## Where things are
- 評価: `scripts/check.sh`（AI・hook・CI 共通）
- 作業メモ: `tasks/current.md`（使い捨て。正は Issue）
- 失敗ログ: `docs/failures.md`
- 判断の記録: `docs/decisions.md`
