# TODO-136 verifier への依頼

worktree `/home/ytani/work/bganalyzer-todo136`（ブランチ `claude/yolo-corners`、未コミット）で、四隅の推定に YOLO の手がかりを入れた変更が動くかを確かめる。
**ファイルは書き換えない**（報告ファイルを除く）。壊して落ちるかは、別のスクリプトで monkeypatch して確かめる。

## 確かめること（コマンドは worktree のトップで）

1. `uv run pytest analyzer/test_api.py -k corners -q` が通る（1 回）
2. テストが壊すと落ちるか。`analyzer/test_api.py` の 2 つのテスト関数を、次の 2 通りで直接呼ぶ（`sys.path` に `analyzer` と `recognizer` を足し、`import test_api`、`import corners` のあと値を差し替えてから関数を呼ぶ）
   - `corners.HINT_WEIGHT = 0` → `test_corners_are_found_on_photos`（関数名は `rg -n "def test_corners" analyzer/test_api.py` で確かめる）が synth-cube-photo4-2 で落ちること
   - `corners.locate = lambda img: None` → `test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part` が collected-sj1vrx で落ちること
   - 差し替えなしでは両方通ること
3. `uv run python recognizer/check_corners.py > archives/agents/TODO-136/check_corners-verify.txt` を 1 回だけ流し、最後の集計行を
   `archives/agents/TODO-136/check_corners-hint-rf.txt`（四隅の順をそろえる直しの前に main が測ったもの）と比べる。
   サンプルごとのずれが 0.05 ポイントより動いたものだけ並べる（時間の列は比べない）
4. `corners.locate` の 1 枚の時間: samples/photo2.jpg で 1 回目（読み込み込み）を除いて 5 回測り、最小と最大
5. モデルが無いときの振る舞い: `corners.MODEL` を存在しないパスにして（`corners._net = None` も）`find_corners` を 1 枚で呼び、何が起きるか（例外の名前）だけ書く

## やらないこと

- 学習のやり直し（`train_corners.py` の実行）はしない（2 時間かかる。main が済ませた）
- テスト全体（`uv run pytest` を絞らずに）は流さない（CI が流す）
- 原因の切り分けや、境界線上の判断はしない。期待と違えば、見たままを「実害は未確認」と添えて報告する

## 報告

`archives/agents/TODO-136/verifier-report.md` に、各項目の結果を 1〜3 行で（測った値を載せる）。期待どおりのものは 1 行でよい。
返事は「終わったか・報告ファイルのパス・判断が要る点」だけ。
