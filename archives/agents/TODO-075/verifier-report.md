# TODO-075 確認報告（PR #236、branch claude/todo-075-drop-arm64-test）

## 1. PR のチェック（一致）

- `gh pr checks 236 --watch --interval 60` は完了まで待ち、結果は `pytest  pass  1m18s`。
- `gh pr checks 236` でも 1 行のみ。arm のジョブは出ていない。
- ジョブの labels は `["ubuntu-latest"]`、conclusion は `success`（`gh api .../actions/runs/38875278223/jobs`）。
- 注: チェック名は job id の `pytest`。ワークフロー名は `test`。文書の「`test`」はワークフロー名を指している。

## 2. gnubg-wheel.yml の読み取り（一致、ただし実走なし）

- 変更は 2 行。`pip wheel` の後に `pip install -q /wheels/*.whl && cd / && python -c "import gnubg"` を足し、その後の `gh release create` は同じ job の次の step。
- `sh -ec` の最後の文が `pip install ... && cd / && python -c ...` なので、どこで失敗してもその文の終了コードが script の終了コードになり、docker run が非 0 で終わる。step が失敗すれば Release の step は GitHub の既定どおり走らない。
- `cd /` を挟んだので `import gnubg` は `/tmp/gnubg` のソースを読まずに、インストールされた wheel を読む。
- 補足（読みによる推測、未実行）: `git fetch ... && git checkout ...` のように `&&` の途中で失敗した場合、POSIX sh の `-e` は `&&` の先頭側を見ないため、その行では止まらず次の行へ進む。ただし `/tmp/gnubg` は空なので、後段の `pip wheel .` が失敗して止まると読める。この経路は今回の差分で変わっていない（既存の行）。
- 限界: この workflow は `tags: gnubg-*` の push でしか走らず、PR #236 のチェックでは検証されない。import まで通るかは、次に gnubg の tag を打つまで確かめられない。

## 3. 古い記述の検索（一致）

- `rg -n -e arm64 -e aarch64 -e ubuntu-24.04-arm ...`（指定どおり）は exit 0 で、残っていた箇所は次のとおり。どれも「test が arm64 で確かめる」とはしていない。
  - `docs/HANDOVER.md:96`: 「`test` が x86_64 で確かめる（arm64 は … Pi の確認 … TODO-075）」
  - `CLAUDE.md:87`: 「GitHub Actions は arm64 で流さない。TODO-075」
  - `README.md:155`: 「`test` は x86_64 で起動して … arm64 は … Pi で確かめます」
  - `.github/workflows/test.yml:12`: コメント（新しい記述）
  - `.github/workflows/gnubg-wheel.yml:16`: `runs-on: ubuntu-24.04-arm`（gnubg の wheel ビルド用。`test` ではない）
  - `docs/raspi.md:30,59`、`analyzer/README.md:109`、`pyproject.toml:29`、`README.md:131`: arm64 の gnubg は Release の wheel を使う、という説明のみ
- 追加で `x86|arm|ubuntu` を検索しても、古い「test が arm64 で確かめる」は見つからなかった（`samples/collected-ajxlol.truth.json` の "a person's arm" は無関係）。

## 4. 変更ファイル（指示の範囲との照合）

`git diff main...HEAD --stat`: 6 ファイル、12 insertions、14 deletions。
- `.github/workflows/gnubg-wheel.yml`（指示どおり）
- `.github/workflows/test.yml`（指示どおり。matrix を外して ubuntu-latest 固定）
- `CLAUDE.md`、`README.md`、`TODO.md`、`docs/HANDOVER.md`（文書の 1 行か 2 行。指示どおり）
- 作業ツリーは確認開始時点で clean。このレポート以外は変更していない。

## 判断が要る点

- なし。確かめられなかったのは、gnubg-wheel の `import gnubg` の成否（tag を打つまで走らない。実走は指示どおり行っていない）。
- `&&` による -e の抜けは読みによる推測で、実走していない。実害は未確認（後段の `pip wheel` で止まると読んだ）。
