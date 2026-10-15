# TODO-064 の依頼

目的: CI の無駄を減らす（TODO.md の TODO-064）。ユーザーが決めたこと:
- 文書だけの PR では `test` を走らせない（main への push では毎回走らせる）
- `cpu-match`（全サンプルの途中の値を x86_64・arm64 で比べる）はやめる。`accuracy` は残す

対象: `git diff main` と、消した `.github/workflows/cpu-match.yml`（`git show main:.github/workflows/cpu-match.yml`）。
保つもの: `recognizer/cpu_reference.json` と `trace_cpu.py --update` の決まり（`analyzer/test_exact.py` の
`test_a_sample_reads_like_the_cpu_reference` が x86_64・arm64 の `test` で 1 サンプルを比べ続けるため）。

## reviewer
見ること:
- `test.yml` の `paths-ignore` が意図どおりか（`**.md` などの glob の意味、push には掛けていないこと）
- `cpu-match` の参照が文書に残っていないか: `rg -n "cpu-match" --glob '!archives/**'`
- 文書（CLAUDE.md・recognizer/README.md）の記述が今の動きと合っているか
見ないこと: ワークフローを実際に走らせること（verifier が PR で見る）。コードは直さない。境界線上の判断は報告だけ。
報告: `archives/agents/TODO-064/reviewer-report.md`。問題なしは 1 行、問題だけ詳しく。返事は「終わったか・報告のパス・判断が要る点」だけ。
