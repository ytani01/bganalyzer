# TODO-053. キューブが写っていない写真を、真ん中のキューブと同じに数える

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium（実装） | reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium（実装） | reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium、2 回） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 90 | 17,557 | 76,457 | 3,237,242 | 82% |
| verifier | Sonnet 5.5 | medium | 32 | 284 | 125,822 | 326,301 | 11% |
| reviewer | Opus 5.5 | high | 16 | 90 | 48,374 | 244,704 | 7% |
| 合計 |  |  | 138 | 17,931 | 250,653 | 3,808,247 | 計 4,076,969 |

- verifier は定義のモデルが haiku。分岐の確認と壊して落ちるかの確認を含むので、見込みどおり Sonnet 5.5 に上書きした。effort は定義の medium
- reviewer は定義のまま（opus / high）。どちらも Agent ツールで見込みと同じ effort を渡した
- 始点は立てたコミット（8aeed5d）。立ててから着手まではほかの項目を挟んでいない

## きっかけ

collected/ の 16 組を recognizer 0.20.1 で測ると、キューブの食い違いが 12 組あった。多くはキューブが写っていない写真で、
読みは「無し」、正解は PWA の既定の centre。解析ではどちらもキューブ 1・真ん中で同じなので、一致として数えることにした（ai1 が決めた）。

## やったこと

- `recognizer/evaluate.py` に `same_cube()` を足し、読み無しと centre を一致とする。片側が正解のときに centre と読めば今までどおり WRONG。
  `evaluate.py` の表示、`check_accuracy.py`、`collected.py` の 3 か所がこれを使う。`run()` は元の読みを返すので、表示は `cube ok (read None, truth centre)` のようになる
- `recognizer/accuracy_baseline.json` を書き直した（commons-lg-cube-dice と commons-rollup-oblique のキューブが not found → ok。ポイントは 572/624 のまま）
- `recognizer/README.md` の「精度」と「キューブ」に数え方を書き足した。commons-rollup-oblique の正解が centre なのは、写真を見て、初期配置で飾りに置いたキューブだからと確かめ、表の行に書いた
- recognizer の版は上げない。読み取りは変わらず、道具だけを変えたときは上げていない前例に合わせた（reviewer の指摘）

## 確かめたこと

- `check_accuracy.py` が 572/624 で通り、`trace_cpu.py check` も通る（Pi、verifier）
- `same_cube` の 4 通り（None×centre、centre×なし は一致、centre×black は WRONG、None×black は not found）
- `or (...)` を消すと `check_accuracy.py` が 2 枚で worse を出して落ちる
- collected/ の写しで `collected.py` の報告の「キューブ」が 12 → 3 行（main が前後で測った。verifier は後だけ）

## 分担の振り返り

- reviewer: 読みを centre にそろえるやり方では、正解が片側なのに centre と読んだ誤りが not found に化けることを見つけた。
  版を上げた件と、表示で「見つけた／見つからない」が見分けられない件、rollup-oblique の正解と README の食い違いも挙げた。どれも直すきっかけになった
- verifier: 指示した 6 点をすべて実測で返した。直したあとの再確認も同じ担当に頼み、測り方の組み直しは無かった。食い違いは見つけていない
- 見込みとの食い違い: verifier が 2 回になった。reviewer の指摘を受けて直したあと、利用者の判断で表示も直したため。
  次に同じ規模なら、reviewer の報告の「判断が要る点」を利用者に先に聞いてから verifier を起こす（今回は聞く前に起こし、1 回分を測り直した）
