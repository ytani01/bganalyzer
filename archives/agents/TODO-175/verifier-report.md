# TODO-175 verifier の報告

## 結果

画面のアプリの写真 13 枚で、四隅の検出を origin/main（9f2d922）と claude/corners-h-lines-slope（HEAD 8354f3f）で比べた。
**collected-galaxy-screen-9 だけが良くなり（2.5% → 0.9%）、ほかの 12 枚は値が同じ。悪くなった写真は無い。**

## 走らせたもの

- `recognizer/check_corners.py` に `samples/*screen*.truth.json` の 13 件を渡した（作業ツリーの絶対パスで指定。画像はそれぞれの truth.json の隣から読む）
- 両方の版で、素のまま（`--app` なし）と `--app`（PWA と同じ縮小）の 2 通り。4 回とも終了コード 0
- main 側は一時 worktree（`git worktree add --detach origin/main`）で流し、終わって削除した。collected-galaxy-screen-9 は main に無いので、ブランチの truth.json を両方に使った
- 値は「推定した四隅と目で読んだ四隅の最大の距離 ÷ 写真の長辺」。`within 3.6%` が目安（GOOD）

## 変わった写真

| 写真 | main | ブランチ | 条件 |
|---|---|---|---|
| collected-galaxy-screen-9 | 2.5% | **0.9%** | 素のまま・`--app` の両方で同じ |

## 変わらなかった写真（値は main = ブランチ、素のまま・`--app` とも同じ）

- collected-champions-screen 1.7%
- collected-galaxy-screen-1 0.3%
- collected-galaxy-screen-2 1.3%
- collected-galaxy-screen-3 0.0%
- collected-galaxy-screen-4 1.3%
- collected-galaxy-screen-5 3.0%
- collected-galaxy-screen-6 1.1%
- collected-galaxy-screen-7 6.5%（元から 3.6% の外。変わらず）
- collected-galaxy-screen-8 2.0%
- collected-teal-galaxy-screen 1.0%
- screen-app-green-far 1.8%
- screen-app-grey-shot 2.6%

集計行: main は `within 3.6%: 12, further: 1`、ブランチも同じ件数（further の 1 件は galaxy-screen-7 で、両方の版で同じ）。
screen-9 は main でも 3.6% の内（2.5%）なので、件数は変わらない。

## 判断できなかったこと・確かめていないこと

- 画面のアプリ以外の写真（実写など）は流していない（指示どおり）。`_swap` と `INNER_IN` は画面以外の写真にも効くので、そちらへの影響は未確認。CI の accuracy は正解の四隅で読むため、ここは見ない
- 表示は小数 1 桁なので、0.05% 未満の差は見えない。四隅の座標そのものは比べていない
- 時間は両版で同程度（0.7〜2.2 秒）。並行して流したため、速さの比較には使えない
- `_swap` の分岐を壊して効き方を見る確認は、頼まれていないのでやっていない

---

# 追記: 画面以外の写真（利用者の指示で全サンプルに広げた。2026-10-20）

## 結果

**悪くなった写真が 1 枚ある: commons-tavli-red-brown（1.1% → 2.7%）。** 目安の 3.6% の内には収まっている。
ほかの 74 枚は値が同じ。良くなった写真は無い。素のままと `--app` の両方で同じ結果。

## 走らせたもの

- 前回と同じ。`check_corners.py` を main（9f2d922、一時 worktree）とブランチ（8354f3f）で、素のまま・`--app` の 4 通り。終了コードはどれも 0
- 対象は `git ls-files samples` の `*.truth.json` のうち、画面のアプリの 13 枚（前回分）を除いた 83 件のうち **75 件**

## 変わった写真

| 写真 | main | ブランチ | 条件 |
|---|---|---|---|
| commons-tavli-red-brown | 1.1% | **2.7%** | 素のまま・`--app` とも同じ |

集計行は main もブランチも `within 3.6%: 45, further: 21, not found: 9`（75 件）。件数は変わらない。
red-brown は main でもブランチでも 3.6% の内。ブランチで 1.6 ポイント外れが増えた。
読み取りが実際に悪くなるかは未確認（CI の accuracy は正解の四隅で読むので、この変化は見ない）。
原因は調べていない。`_swap` の変更か `INNER_IN` 0.75→0.6 かの切り分けは、頼まれていないのでやっていない。

## 変わらなかった写真

上の 1 枚以外の 74 枚は、写真ごとの値が main と同じ（`further` の 21 枚と `not found` の 9 枚も、どちらの版でも同じ写真）。

## 流せなかったもの

`samples/external/` の 8 件は画像が無く、流せなかった（画像は `.gitignore` の対象で、この機械にも本体の作業ツリーにも無い。truth.json だけがある）:
bray-beginners-106 / 107 / 108、bray-experts-105 / 106、bray-intermediates-105 / 106、galaxy-cube2-near。
これらは変化を測っていない。最初に全件をまとめて流したときは、bray-beginners-106 の画像が読めず `AttributeError` で止まった（check_corners.py が画像の無い件を飛ばさないため）。

---

# 追記 2: 直し（083f805）のあとの全サンプル比較（2026-10-20）

## 結果

**良くなった写真は collected-galaxy-screen-9 の 1 枚（2.5% → 0.9%）。悪くなった写真は無い。**
前回悪くなった commons-tavli-red-brown は main と同じ値（1.1%）に戻った。ほかの 86 枚も値が同じ。
素のままと `--app` の両方で同じ結果。

## 走らせたもの

- ブランチは 8c43c9b（083f805 を含む）。main は 9f2d922（一時 worktree。終わって削除）
- `check_corners.py` を、画面のアプリ 13 枚と画面以外 75 枚の計 88 件に、main とブランチで素のまま・`--app` の 4 通り。終了コードはどれも 0
- 集計行は 4 回とも `within 3.6%: 57, further: 22, not found: 9`。件数は変わらない

## 変わった写真

| 写真 | main | ブランチ |
|---|---|---|
| collected-galaxy-screen-9 | 2.5% | **0.9%** |

## 変わらなかった写真

上の 1 枚以外の 87 枚（commons-tavli-red-brown を含む）は、写真ごとの値が main と同じ。

## 流せなかったもの（前回と同じ）

`samples/external/` の 8 件（bray-beginners-106 / 107 / 108、bray-experts-105 / 106、bray-intermediates-105 / 106、galaxy-cube2-near）は画像が無く、測っていない。
表示は小数 1 桁なので、0.05% 未満の差は見えない。
