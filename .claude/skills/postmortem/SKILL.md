---
name: postmortem
description: 直前の AI の失敗を Context / Permission / Evaluation / Model の1つに分類し、docs/failures.md に記録して昇格を提案する
argument-hint: [Issue番号 または ログのパス]
---

直前のセッション、または `$ARGUMENTS`（Issue / `.agent/logs/` のログ）で起きた失敗を診断する。

## 分類（1つだけ選ぶ）
判定は上から順に。最初に Yes になったものを採る。
1. **Permission** — 必要なコマンド・権限・秘密情報・ネットワークがなかったか
2. **Context** — このプロジェクト固有の制約を知っていれば避けられたか（一般知識の不足は該当しない）
3. **Evaluation** — 間違った変更を `scripts/check.sh` が通した、または正しいかどうかを判定する手段がなかったか
4. **Model** — 上の3つがそろっていても解けなかったか

## 出力
1. `docs/failures.md` の Log に1行追記する。
2. 分類ごとの打ち手を**差分の形で**提案する。適用は人間の確認を取ってから。
   - Context → `AGENTS.md` か `docs/` に追記する**1行**。2行以上になるなら、書く場所か粒度を疑う
   - Permission → `.claude/settings.json` / CI / 環境の変更
   - Evaluation → `scripts/check.sh` に足す検査、または追加すべきテスト
   - Model → タスクの分割案、または「人間が持つ」判断と再挑戦の目安日
3. 同じ分類・同じ原因の行が過去にあれば、それも指摘する（再発は昇格の強い根拠になる）。

プロンプトの言い回しを変える提案は、Context のときだけにする。
