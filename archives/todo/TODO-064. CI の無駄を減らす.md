# TODO-064. CI の無駄を減らす

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 58 | 18,042 | 76,239 | 2,865,879 | 86% |
| reviewer | Opus 5.5 | high | 20 | 1,918 | 43,646 | 302,220 | 10% |
| verifier | Haiku 5.5 | medium | 10 | 1,139 | 27,543 | 95,833 | 4% |
| 合計 |  |  | 88 | 21,099 | 147,428 | 3,263,932 | 計 3,432,547 |

- reviewer・verifier のモデルと effort は定義（`~/.claude/agents/`）のまま

## きっかけ

文書だけの PR でも `test` が x86_64・arm64 で走り、`accuracy` と `cpu-match` の x86_64 が同じ全サンプルを別々に読んでいた。

## やったこと

- 初めは `trace_cpu.py check` で精度も確かめ、読み取りを 1 回にまとめる形で作りかけた。
  途中でユーザーが `cpu-match` の要否を尋ね、選択肢から「cpu-match をやめる」を選んだので、作りかけの変更は戻した
- `.github/workflows/cpu-match.yml` を消した。`cpu_reference.json` と `trace_cpu.py --update` の決まりは残す
  （`analyzer/test_exact.py` の 1 サンプルの比較が `test` で x86_64・arm64 の両方を見続けるため）
- `test.yml` の `pull_request` に `paths-ignore`（`**.md`・`docs/**`・`archives/**`）。main への push では毎回走る
- `accuracy.yml` の `pull_request` で `recognizer/**.md` を外した（verifier の報告で、`recognizer/README.md` だけでも走っていたと分かったため）
- CLAUDE.md・recognizer/README.md・docs/HANDOVER.md・テストのコメントを直した（PR #211）

## 確かめたこと

- PR #211 で `pytest`（ubuntu-latest・ubuntu-24.04-arm）と `accuracy` が通り、`cpu-match` は走らなかった（verifier）
- 手元の `uv run pytest analyzer` は 83 件通った
- 文書だけの PR で `test` が走らないことは、この決着の PR（`TODO.md` と `archives/` だけ）で見る

## 分担の振り返り

- reviewer は docs/HANDOVER.md に「test が通ったら自動マージ」が残っていると見つけた（直した）。
  verifier は `accuracy` が `recognizer/README.md` だけで走ると見つけた（依頼に「走らないのが正しい」と誤って書いていた）
- 見込みどおりの編成。食い違いは方針の変更（まとめる → やめる）で、作りかけを戻した分の main のトークンが余計にかかった
- 次に CI を減らす項目では、各ワークフローが本当に要るかを立てるときにユーザーに聞く。今回は「まとめる」と決めてから「やめる」に変わった
