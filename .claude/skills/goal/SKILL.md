---
name: goal
description: Issue の Done を満たすまで、実装→検証→修正のループを自分で回し、PR を出す
argument-hint: <#issue番号>
---

`$ARGUMENTS` の Issue を目標として、完了条件を満たすまで自走する。

## 手順
1. Issue の Goal / Done / Constraints / Out of scope を読む。`tasks/issue-<番号>.md` があればそれを、なければ `gh issue view <番号>` を使う。
   Done が機械判定できない・解釈が2通り以上あるなら、ここで止めて質問する。
2. `tasks/current.md` に Issue 番号と Done のチェックリストを書く。
3. 作業ブランチを切る（`agent/<issue番号>-<短い名前>`）。
4. ループ:
   - 実装する
   - `./scripts/check.sh` を実行する
   - 赤なら原因を読んで直す。同じ失敗が3回続いたら AGENTS.md の Escalation に従う
   - Done の各項目を、実行したコマンドと結果で1つずつ確かめ、`tasks/current.md` を更新する
5. 全部緑になったら PR を作る。本文は `.github/pull_request_template.md` の形で、
   **何を変えたか・なぜ正しいか（証拠）・確かめていないこと** を書く。人間はコード全文を読まない前提で書く。
6. `tasks/current.md` を空に戻す。

## 途中で失敗・中断したら
最後に `/postmortem` を実行して原因を1つに分類し、`docs/failures.md` に残す。
