# TODO-172. 四隅の検出処理をリファクタリングして速くする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | implementer（Opus 5.5 / high）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium）。コードが変わるので reviewer を入れ、先に回す |
| 実施 | Opus 5.5 / effort high | implementer（Opus 5.5 / high）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium）。reviewer を先に回した |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main と担当（分けられない） | Opus 5.5・Sonnet 5.5 | 上の表のとおり | 662 | 151,440 | 581,327 | 23,026,887 | 100% |
| 合計 |  |  | 662 | 151,440 | 581,327 | 23,026,887 | 計 23,760,316 |

- `token-usage.py TODO-172` の値（立ててから決着のコミットの直前まで）。teammate のログが担当ごとに分かれず、すべて main の行に出た
- 同じ時間に TODO-171・TODO-173・TODO-174 の担当も動いていたので、その分も入っている。この項目だけの量はこれより少ない
- モデル別では Opus 5.5 が 89%、Sonnet 5.5 が 11%
- implementer の定義（`~/.claude/agents/implementer.md`）は sonnet / medium。込み入った書き換えなので Opus 5.5 / high に上書きした。verifier の定義は haiku / medium で、Sonnet 5.5 に上書きした

## きっかけ

ユーザーが、アルゴリズムを変えずにリファクタリングして四隅の検出を速くすると決めた（2026-10-20）。

## やったこと

cProfile と line_profiler で 3 組を測り、時間のかかっている `_structure`（候補の点数づけ、約 40%）と `_Upright.__init__`（約 15%）を直した。出力は 1 画素も変えていない。

- `recognizer/corners.py` の `_structure`: Lab の値を 2 倍した整数で、チャンネルごとに計算するようにした。中央値は `np.partition` で真ん中の 2 つを取って出す。float で計算するのは、元と同じ式・同じ並びの相関の部分だけ
- `recognizer/corners.py` の `_Upright.__init__`: 傾きによるずれを行ごとの表から引き、`cumsum` を最後に 1 回だけかける
- recognizer 0.29.1（TODO-171 の 0.29.0 の後に rebase した）
- 測る道具を `archives/agents/TODO-172/` に置いた（`record_corners.py`、`ab_time.py`、前後の記録の JSON）

## 確かめたこと

- 87 組すべてで、書き換えの前後の四隅が完全に同じ（implementer と verifier がそれぞれ確かめた。`side` を持つ 5 組の `find_corners_side` も同じ）
- 速さ: 交互に流して組ごとの最速で比べると、87 組の合計は 58.5 s → 46.3 s（−21%、開発機。負荷が高い中で測った）
- `analyzer/test_side.py`、ruff、CI の pytest・accuracy・ruff が通った

## 残ること

- まだ時間のかかる所は `exact.warp` と `exact.homography`。盤面の読み取り（TODO-173）でも使うので、この項目では触っていない

## 分担の振り返り

- **implementer** は直す所を測って決め、前後の一致を確かめた。開発機の負荷が高く、1 回ずつ流した全サンプルの合計時間では差が出なかったので、交互に流して最速で比べる `ab_time.py` を作った。全サンプルは「前」1 回・「後」2 回流した（途中で直しを足したため）
- **reviewer** は直すべき点 0 件。コメントの読みにくさを 1 件見つけた
- **verifier** は 87 組の一致と速さを測り直し、`ab_time.py` が `side` の組を通らないことを見つけた。追加の依頼で 5 組を確かめた
- 見込みとの食い違いは無かった
- 次に同じ規模で組むなら、こうする:
  - 測る道具に、最初から「交互に流して最速をとる」作りと `side` の組を入れておく（verifier への追加の依頼が要らなくなる）
  - 全サンプルを流すのは、直しが出揃ってからにする
