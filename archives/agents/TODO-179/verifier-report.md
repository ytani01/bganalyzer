# TODO-179 verifier の報告

## 1. 塗り直した 3 組（green-felt-side-hand / blue-red-top / wood-side）

`git show origin/main:` の旧写真と新しい写真を PIL・numpy で測り、左右に並べた画像を Read で見た。

| 組 | 寸法 前→後 | 盤の中（四隅の四角）の平均差 | 四隅の四角の外の黒 前→後 | 1.1 倍の四角の外の黒（後） |
|---|---|---|---|---|
| green-felt-side-hand | 977x1180 → 同じ | 0.034 | 99.99% → 67.07% | 99.97% |
| blue-red-top | 2048x1538 → 同じ | 0.040 | 99.99% → 80.39% | 100.00% |
| wood-side | 620x503 → 同じ | 0.235 | 99.91% → 92.01% | 99.94% |

- 写真の大きさ: 一致（3 組とも同じ）
- 盤が欠けていない: 一致（盤の中の画素は JPEG の書き直し分だけの差）。並べた画像でも盤は全部残っている
- 盤の周りが前より広く残っている: 一致（黒でない範囲が四隅の外へ広がった。例: blue-red-top は x 399→331、y 133→77）
- 四隅の外が黒い: 一致（1.1 倍の四角の外は 99.9% 以上が黒。残りは JPEG のノイズと見られる）

目で見た気づき（どれも実害は未確認）:
- green-felt-side-hand: 手は前から写っていた（-hand の組）。左下・下に盤の外の木の縁が少し広がって写る
- blue-red-top: 右上の縁に電子時計のような物と、右上の角に白い小さな物が写る。人の顔や肌は見当たらない
- wood-side: 左下に指のような肌色が前から写っている（前の写真にもある）。左の縁に白い帯が写る

## 2. GitHub Actions（`gh pr checks 535 --watch`、終了コード 0）

- ruff: pass（14s）
- accuracy: pass（3m46s）
- pytest（test）: pass（1m31s）

## 変更されたファイル

`git diff origin/main --stat`（30 件）: CLAUDE.md、TODO.md、analyzer/test_collected.py、archives/agents/TODO-179/（implementer-report.md、repaint.py、reviewer-report.md）、docs/raspi.md、recognizer/README.md、recognizer/accuracy_baseline.json、recognizer/import_collected.py、samples/collected-* の 20 組。依頼の範囲と合っている。

作業ツリーに未コミットの変更が 1 件ある: `archives/agents/TODO-179/reviewer-report.md`（M）。

## 確かめなかったこと

- 残り 17 組の写真（頼まれていない）
- 全サンプルの精度・テスト全体（CI の結果に任せた）
