# TODO-173. 四隅の検出の後の盤面の読み取りをリファクタリングして速くする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | implementer（Opus 5.5 / high）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium）。コードが変わるので reviewer を入れ、先に回す |
| 実施 | Opus 5.5 / effort high | implementer（Opus 5.5 / high）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium）。reviewer を先に回した |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main と担当（分けられない） | Opus 5.5・Sonnet 5.5 | 上の表のとおり | 336 | 89,210 | 446,538 | 11,503,266 | 100% |
| 合計 |  |  | 336 | 89,210 | 446,538 | 11,503,266 | 計 12,039,350 |

- `token-usage.py TODO-173 --since '2026-10-20 06:30:00'` の値（着手から決着のコミットの直前まで）。立てたあと TODO-172 の決着を挟んだので、着手の時刻で切った。teammate のログが担当ごとに分かれず、すべて main の行に出た
- 同じ時間に TODO-175 を立てる担当も動いていたので、その分も入っている
- モデル別では Opus 5.5 が 93%、Sonnet 5.5 が 7%
- implementer の定義（`~/.claude/agents/implementer.md`）は sonnet / medium。込み入った書き換えなので Opus 5.5 / high に上書きした。verifier の定義は haiku / medium で、Sonnet 5.5 に上書きした

## きっかけ

ユーザーが、四隅が決まった後の読み取り（石・バー・サイコロ・キューブなど）を、アルゴリズムを変えずにリファクタリングして速くすると決めた（2026-10-20）。四隅の検出（TODO-172）は含めない。

## やったこと

cProfile と line_profiler で 3 組を測り、`radial._maps`（約 38%）、`dice._bodies`（約 15%）、`geometry.find_tips`（約 14%）、`geometry.fit_columns`（約 9%）を直した。出力は変えていない。

- `recognizer/radial.py`: 箱の和を整数の累積和から `cv2.boxFilter`（float64 で整数を足すので正確）に、k 番目に小さい値を `np.partition` から `np.bincount` の累積に、両側の票の `bincount` を 4 回から 2 回に
- `recognizer/dice.py` の `_bodies`: 連結成分の大きさのふるい分けを numpy でまとめて行う
- `recognizer/exact.py` の `min_area_rect`: 辺ごとのループを、全部の辺をまとめて計算する形に
- `recognizer/geometry.py`: `fit_columns` の格子の得点をまとめて計算（選ぶループはそのまま）、`_run_at` の端の探索を bytes の検索に
- `recognizer/README.md`: 箱の和と順位の書き方を今の実装に合わせた（`exact.box_sum` は整数のまま）
- recognizer 0.29.2
- 測る道具を `archives/agents/TODO-173/` に置いた（`record_reading.py`、`ab_time.py`）

## 確かめたこと

- 87 組すべて（`side` を持つ 5 組を含む）で、四隅を正解に固定した読み取りの出力すべて（`pos.to_dict()` と `info` 全体）が書き換えの前後で同じ（verifier）
- 速さ: 87 組を前後 1 回ずつ流して 502.1 s → 319.6 s（−36%、開発機。続けて流したので目安）。implementer が 5 組を交互に流して最速で比べると 20.3 s → 14.4 s
- `analyzer/test_exact.py`・`analyzer/test_side.py`、ruff、CI の test・accuracy・ruff が通った

## 分担の振り返り

- **implementer** は直す所を測って決め、5 組（side を 1 つ含む）で前後の一致を確かめた。`min_area_rect`・`fit_columns`・`_run_at` は旧版と直接比べる試験も流した。float のまま `//` する案が元より遅いことを測って捨てた。`ab_time.py` の worker が最初は新しい版を 2 つ読んでいたのに、結果がおかしいことで気づいて直した
- **reviewer** は直すべき点を 1 件見つけた（README の箱の和の書き方が `exact.box_sum` に合わない）。コードの等価性は問題なし
- **verifier** は 87 組の一致と時間を 1 回で測った。食い違い 0 件
- 見込みとの食い違いは無かった
- 次に同じ規模で組むなら、こうする:
  - implementer の依頼に「実装の説明を書いた README の行も同じ PR で直す」と書いておく（今回は README の直しが 2 回に割れ、reviewer の指摘で 1 回足した）
  - 前後を比べる道具は、モジュールの読み込み先を引数か環境変数で切り替える形を最初から作り、読み込んだ場所を assert で確かめる
