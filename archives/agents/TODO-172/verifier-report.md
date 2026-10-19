# TODO-172 verifier の報告

対象: PR #513（HEAD 7a4e5ba）。コードは直していない。

## 1. 四隅の一致

- 一致: **87 組すべて `same=True`**（`rg -c "same=True"` が 87、`same=False` は 0 件）。終了コード 0。
- 方法: `archives/agents/TODO-172/ab_time.py` に、`git show origin/main:recognizer/corners.py` を一時ディレクトリへ出したもの（`corners_model.onnx` を横に置いた）を渡し、
  全サンプル（`samples/*.truth.json`）を 1 回だけ流した。比べたのは `find_corners(img)` の戻り値どうし（`==`）。
  「前」のファイルは、この PR の分岐元（5a4585e）の `recognizer/corners.py` とバイト単位で同じことを `cmp` で確かめた。
- 確かめていないこと: `side` を持つ 5 組の `side.find_corners_side`（`_Upright` を使う）の前後の比較は、今回の実行に入っていない
  （`ab_time.py` は `find_corners` しか呼ばない）。実装の担当の `corners-before.json` / `corners-after.json` に記録があるが、私は流し直していない。実害は未確認。

## 2. 速さ

同じ 1 回の実行の中で、組ごとに前・後を交互に 3 回ずつ流し、組ごとの最速をとった（開発機の load average は 13 前後）。

| | 前 | 後 | 比（後 / 前） |
|---|---|---|---|
| 87 組の合計（最速の和） | 58.49 s | 46.30 s | **0.79**（−21%） |
| 組ごとの比の中央値 | | | 0.78（最小 0.55、最大 1.38） |

遅い組の上位 5（前の順）:

| 組 | 前 | 後 |
|---|---|---|
| commons-case-dice | 1.48 s | 0.97 s |
| collected-black-red-oblique | 1.43 s | 1.05 s |
| collected-galaxy-screen-3 | 1.23 s | 0.91 s |
| collected-blue-felt-oblique | 1.13 s | 0.83 s |
| collected-app-green-shot | 1.12 s | 0.81 s |

後のほうが遅く出た組は 4 つ（最速どうしの比較）:
collected-galaxy-screen-7 0.65 → 0.90 s、collected-grey-brown-oblique 0.90 → 0.96 s、collected-tan-black-side-1 0.37 → 0.38 s、collected-tv-vegas-1 0.73 → 0.81 s。
負荷のぶれか実際の遅れかは区別していない（3 回の最速でも galaxy-screen-7 は +0.25 s）。実害は未確認。

## 3. 版

recognizer の `__version__` は 0.28.0 → **0.28.1**（`recognizer/board.py`）。patch で上がっている。

## 変更されたファイル（`git diff origin/main...HEAD --stat`）

- `recognizer/corners.py`、`recognizer/board.py`（版）、`TODO.md`（TODO-172 のチェックボックス 4 つ）
- `archives/agents/TODO-172/`: `ab_time.py`、`record_corners.py`、`corners-before.json`、`corners-after.json`、`implementer-report.md`
- 未追跡: `archives/agents/TODO-172/reviewer-report.md`（reviewer の報告。まだコミットされていない）

指示の範囲（四隅の検出の書き換えと版の patch 上げ）に収まっている。`analyzer/` など範囲外のファイルの変更は無い。

## 判断できなかったこと

- 上の「後のほうが遅い 4 組」を問題とするか。
- `side` の 5 組を今回の実行で比べていないこと（上の 1）を、実装の担当の記録で足りるとするか。

## 追加の確認（管理者の依頼）

### A. `side` を持つ 5 組の `find_corners_side`

- 一致: **5 組すべて前後で完全に同じ**（出力した JSON が `cmp` でバイト単位で一致）。ただし collected-brown-cream-oblique は前も後も `None`（四隅が見つからなかった）で、その `None` どうしが一致した。ほかの 4 組は 4 隅が返っている。`None` が truth の想定どおりかは見ていない。実害は未確認。終了コード 0（前・後とも）。
- 対象: collected-cream-black-oblique、collected-wood-tan-oblique、collected-red-blue-oblique、collected-brown-cream-oblique、collected-grey-brown-oblique。
- 方法: `side.py` は `import corners as C` で読むので、`recognizer/` を一時ディレクトリへ丸ごと写し、`corners.py` だけ分岐元（5a4585e）のものに替えた。
  前・後を別のプロセスで 1 回ずつ流した（スクリプトの中で、読んだ `corners` がそのディレクトリのものであることを assert で確かめた）。
  スクリプトは一時ディレクトリにあり、リポジトリには入れていない。

### B. 後のほうが遅く出た 4 組を、前後交互 5 回ずつ（`ab_time.py`、最速、同じ実行）

| 組 | 前 | 後 | 比 |
|---|---|---|---|
| collected-galaxy-screen-7 | 0.47 s | 0.38 s | 0.81 |
| collected-grey-brown-oblique | 0.80 s | 0.77 s | 0.96 |
| collected-tan-black-side-1 | 0.35 s | 0.27 s | 0.77 |
| collected-tv-vegas-1 | 0.64 s | 0.49 s | 0.77 |
| 4 組の合計 | 2.27 s | 1.91 s | 0.84 |

4 組とも遅くなっていない。前の実行で遅く出たのは負荷のぶれと読める（推定。load average は前の実行で 13、今回は 5 前後）。
grey-brown-oblique だけは差が小さい（0.96）。この比較は `find_corners` のもので、この組は `side` の組なので、実際のアプリでは `find_corners_side` が呼ばれる。その時間は測っていない。実害は未確認。
