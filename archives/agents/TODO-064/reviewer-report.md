# TODO-064 reviewer の報告

対象: `git diff HEAD`（ブランチ claude/ci-waste、未コミット）と、消した `.github/workflows/cpu-match.yml`。

## 要修正

### docs/HANDOVER.md:32, 59-60, 111 — 文書だけの PR で `test` が走らないことが反映されていない

- 32 と 59-60 は「`uv run pytest analyzer` と GitHub Actions の test が（両方）通り、…マージ」と書いている。
  111 は「`test` が PR と main への push で `uv run pytest analyzer` を実行する」と書いている。
- 差分の後は、文書だけの PR では `test` が走らない（`test.yml` の `paths-ignore`）。CLAUDE.md:92 には
  「文書だけの PR では `test` は走らないので要らない」と足したが、HANDOVER.md は差分に入っておらず古いまま。
- なぜ問題か: HANDOVER.md は別アカウントの Claude が自動マージの手順として読む文書（CLAUDE.md「共同開発」）。
  書いてあるとおりに従うと、文書だけの PR で走らない `test` を待つか、通っていないとしてマージを止める。
  CLAUDE.md と HANDOVER.md で同じ決まりが食い違う。実害は未確認。
- 111 の `accuracy` の説明の隣にあった `cpu-match` の記述はもともと無いので、そこは直す必要なし。

## 検討

なし。

## 好みの範囲

なし。

## 問題なし（1 行ずつ）

- `test.yml` の `paths-ignore: ['**.md', 'docs/**', 'archives/**']`: `pull_request` だけに掛かり、`push`（main）には掛けていない。
  `**.md` はどの階層の `.md` にも当たる（GitHub の filter pattern で `**` は `/` も含む）。PR の変更が全部これに当たるときだけ飛ぶので、コードを含む PR は走る。
  `docs/` は `.md` しか無く、`analyzer` のテストはリポジトリの `.md`・`docs/`・`archives/` を読まない（`rg` で確認）。
- main にブランチ保護・ruleset は無い（`gh api .../branches/main/protection` が 404、`rulesets` が `[]`）ので、走らない `test` が必須チェックとして待ち続けることは無い。
- `rg -n "cpu-match" --glob '!archives/**'`: 残っているのは TODO.md:74, 78、CLAUDE.md:62、recognizer/README.md:106 で、いずれも「やめた」ことの説明。古い記述は無し。
- CLAUDE.md:16, 62, 92 と recognizer/README.md:106-107, 250, 612: 今の動き（`test` が x86_64・arm64 で `commons-diagram-prime` 1 枚を比べる、全サンプルは `trace_cpu.py check` を手で）と合っている。
- analyzer/test_exact.py:67、analyzer/test_api.py:206 のコメント: `trace_cpu.py` は全サンプルの四隅も比べる（trace_cpu.py:4-5, 39）ので記述どおり。行長は同じファイルの既存の行（117〜122 字）の範囲内。
- 保つもの: `recognizer/cpu_reference.json`、`trace_cpu.py --update` の決まり（CLAUDE.md:61）、`test_a_sample_reads_like_the_cpu_reference` はそのまま。
  version の一致の assert（test_exact.py:72）があるので、recognizer を変えて版を上げ `--update` を忘れた PR は `test` で落ちる。
- 範囲: 指示に無い変更は無し。recognizer・analyzer のコードは変えておらず、版を上げないのも CLAUDE.md「バージョン」どおり。

参考（ユーザーが決めた範囲なので報告だけ）: `uv.lock`・`pyproject.toml` の更新（OpenCV・NumPy の版上げなど）で arm64 の読みが変わったとき、
CI で見るのは arm64 の 1 枚だけになる（`accuracy` は ubuntu-latest のみ）。

## 作り込みすぎ

作り込みすぎ: なし（差分は 34 行のワークフローを消し、2 行足しただけ）。
