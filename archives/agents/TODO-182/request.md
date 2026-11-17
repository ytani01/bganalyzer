# TODO-182 依頼（reviewer → verifier の順）

作業ツリー: /home/ytani/work/bganalyzer/.claude/worktrees/todo-182（ブランチ claude/fix-oblique3-bottom-colour、未コミット）
差分: `git diff`（2 ファイル）
- samples/collected-black-red-oblique-3.truth.json の bottom_colour を 0 → 1
- recognizer/accuracy_baseline.json のこの組の home を false → true（evaluate.py で home guess ok になったため）

背景: archives/agents/TODO-182/main-findings.md。写真の手前の駒は明るい駒で 1 のはず。
維持するもの: 正解のほかの値（points・四隅・home・side など）、ほかのサンプルの基準。
修正はせず、境界線上の判断は報告だけ。原因も調べない。一致したものは 1 行、食い違いだけ詳しく。

## reviewer
差分が上の 2 点だけか。bottom_colour=1 が main-findings.md の根拠と矛盾しないか。
基準の書き換えが CLAUDE.md の「精度の確認」と合うか（--update を使わず手で 1 行直した）。
報告: archives/agents/TODO-182/reviewer-report.md

## verifier
1. `uv run python recognizer/evaluate.py samples/collected-black-red-oblique-3.truth.json` を 1 回実行し、
   points 20/24・bar ok・home guess ok・dice ok・cube ok かを、出力の値を載せて報告。基準の行と一致するか。
2. 壊すと失敗するか: 一時的に bottom_colour を 0 に戻して同じコマンドを 1 回実行し、home guess が ok でなくなるかを報告し、元に戻す（`git diff` が依頼時と同じことを確かめる）。
全サンプルや check_accuracy.py は流さない（CI の accuracy に任せる）。
報告: archives/agents/TODO-182/verifier-report.md
