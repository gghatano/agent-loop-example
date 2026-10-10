# AGENTS.md

このファイルには**このプロジェクト固有の事情だけ**を書く。
言語・フレームワーク・ツールの一般的な使い方は書かない（モデルは知っている）。
1行足すときは、`docs/failures.md` の該当行を根拠として残す。

## Project rules
- `mock/` はデザインの正。実装をモックに合わせる。`mock/` と `fixtures/` は変更しない
- 画面に出すデータは `fixtures/projects.json` から描画する。テンプレートに値を直書きしない

## Completion criteria
タスクは次をすべて満たしたときだけ完了とする。満たせないまま完了と報告しない。
- `./scripts/check.sh` が exit 0
- Issue の `Done` の各項目について、満たした証拠（コマンドと結果）を PR に書いた
- Issue の `Constraints` に反する変更がない

## Escalation
次の場合は作業を止め、状況と選択肢を書いて人間に返す。推測で進めない。
ヘッドレス実行（`scripts/loop.sh`）では、同じ内容を `.agent/BLOCKED` に書いて終わる。
- `Constraints` を破らないと `Done` を満たせない
- 同じ check の失敗を3回連続で直せない
- 秘密情報・本番環境・課金が絡む操作が必要
- Issue の `Done` が曖昧で、2通り以上の解釈がある

## Where things are
- 評価: `scripts/check.sh`（AI・hook・CI 共通）。画面差分は `scripts/vrt.py`、差分画像は `.agent/vrt/*.diff.png`
- 作業メモ: `tasks/current.md`（使い捨て。正は Issue）
- 失敗ログ: `docs/failures.md`
- 判断の記録: `docs/decisions.md`
