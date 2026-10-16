# TODO-078 確認報告（verifier）

## 走らせた検証

| 検証 | 終了コード | 結果 |
|---|---|---|
| `recognizer/check_corners.py`（変更後、全 56 サンプル） | 0 | `after.txt` に保存。利用者の確認は出なかった |
| `recognizer/check_corners.py`（main を worktree に出して実行） | 0 | `before.txt` に保存 |
| `uv run pytest analyzer/test_api.py -k corners` | 1 | 1 failed, 3 passed。落ちたのは `test_corners_are_found_on_samples` |

pytest の失敗（`archives/agents/TODO-078/pytest.txt` より引用）:

```
analyzer/test_api.py:207: AssertionError
E           AssertionError: screen1
E           assert 0.06988417875058234 < 0.035
```

main での pytest は走らせていない。変更前に通っていたかは未確認。

worktree は `git worktree remove --force` で削除済み（`git worktree list` で本体のみを確認）。

## 集計行（前後の比較）

| | within 3.6% | further | not found |
|---|---|---|---|
| main（before） | 35 | 17 | 4 |
| 変更後（after） | 32 | 21 | 3 |

## 変わったサンプル（38 件）

変わらなかったのは 18 件（件数のみ）。

### 1. 3.6% の内側から外へ出たもの（5 件）

| サンプル | main | 変更後 |
|---|---|---|
| collected-o32w4i | 1.7% | 32.2% |
| screen1 | 2.5% | 7.0% |
| synth-cube-photo4-16 | 2.4% | 4.7% |
| synth-cube-photo4-32 | 2.8% | 4.9% |
| synth-cube-photo4-64 | 3.6% | 4.9% |

### 2. ずれが 0.1 ポイントより大きく増えたもの（上の 1 を含む）

| サンプル | main | 変更後 | 増減 |
|---|---|---|---|
| collected-o32w4i | 1.7% | 32.2% | +30.5 |
| screen1 | 2.5% | 7.0% | +4.5 |
| synth-cube-photo4-16 | 2.4% | 4.7% | +2.3 |
| synth-cube-photo4-32 | 2.8% | 4.9% | +2.1 |
| synth-cube-photo4-64 | 3.6% | 4.9% | +1.3 |
| collected-94jhut | 0.0% | 1.3% | +1.3 |
| collected-er0y2w | 0.0% | 1.3% | +1.3 |
| collected-jpc616 | 0.0% | 1.3% | +1.3 |
| collected-q0k95c | 0.0% | 1.3% | +1.3 |
| commons-case-dice | 13.7% | 14.9% | +1.2 |
| commons-leather-cups | 2.5% | 3.2% | +0.7 |
| tv-vegas-open | 1.5% | 2.4% | +0.9 |
| photo4 | 4.5% | 4.9% | +0.4 |
| photo2 | 3.1% | 3.4% | +0.3 |
| commons-diagram-holding | 2.1% | 2.3% | +0.2 |
| commons-set-cube-dice | 4.1% | 4.3% | +0.2 |
| commons-tavli-blue | 1.4% | 1.6% | +0.2 |

### 3. 見つかる／見つからないが変わったもの

| サンプル | main | 変更後 |
|---|---|---|
| collected-ajxlol | - | 13.4% |
| photo5 | - | 3.5% |
| commons-rollup-oblique | 28.5% | - |

### 4. 改善したもの（参考、件数のみ列挙）

collected-4b88u3（41.3→39.6）、collected-a8qvq6（2.7→2.2）、collected-si3vsd（3.6→2.9）、collected-w8eaks（2.8→1.5）、commons-dark-homeleft（3.0→2.6）、commons-tavli-red-diamond（4.6→1.9、3.6% の外から内へ）、commons-travel-case（2.0→1.0）、synth-cube-photo4-8（4.9→3.8、まだ外）、synth-cube-photo2 の 6 件（3.3→3.1）ほか。

## 集計行との整合

表示された値（小数 1 桁）から数えると、3.6% 以内は 35 → 32 で集計行と一致する。内訳は、内から外が 5 件、外から内が 2 件（commons-tavli-red-diamond、photo5）。
ただし判定は表示前の値で行われる。表示が 3.6 となるもの（collected-si3vsd、synth-cube-photo4-64 の main 側）は、表示の丸めの都合で境界の判定が確定しない。表示値では 3.6 以内に数えている。

## 判断できなかったこと・確かめていないこと

- 中で何が変わったかの切り分けはしていない（指示どおり）。screen1、collected-o32w4i、synth-cube-photo4-* が外へ出た理由は分からない。
- 完了条件「main より悪くならないこと」は、上の 1〜2 の一覧が示すとおり満たしていない。判断は管理者に任せる。
- pytest の screen1 の失敗は、上の表の screen1 の値（7.0%）と一致する。ただし pytest の閾値 0.035 の意味や、main で通っていたかは確かめていない。
- 時間（秒）は比べていない（指示どおり）。
- 既知の事項（photo5 が main で「-」、commons-tavli-red-white が 1.9% のまま、commons-rollup-oblique が main で 28.5% から「-」）は、結果と一致していることだけ確認した。tavli-red-white は 1.9% のまま変わらなかった。

## 変更されたファイル

このレポートの範囲では、変更ファイルの一覧（git status）は確認していない。作成したのは `archives/agents/TODO-078/` の `after.txt`、`before.txt`、`pytest.txt`、本報告のみ。コードは変更していない。
