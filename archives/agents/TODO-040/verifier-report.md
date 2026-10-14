# TODO-040 verifier 報告

対象: ブランチ claude/todo-040-photo-screen（5f9bf74）。コードは変更していない。
手段: `python3 -m http.server 8765 -d analyzer/static`（PID を確かめて kill 済み）＋ Playwright（`/usr/bin/chromium` 指定。
uv の playwright が要求する chromium_headless_shell-1248 は入っておらず、tools/pi_ui_check.py と同じく executable_path 指定にした）。
スクリプト: archives/agents/TODO-040/check_layout.py（各幅 1 回）。

## 実測値

| 項目 | 390x844 | 1024x768 |
|---|---|---|
| details.tips bottom / .pick top | 301.5 / 313.5（tips が上） | 308.5 / 320.5（tips が上） |
| .pick の子 | LABEL, LABEL, BUTTON#manual | 同左 |
| 3 つの y | 313.5 / 313.5 / 313.5 | 320.5 ×3 |
| 3 つの x | 16 / 138 / 260 | 168 / 400 / 632 |
| width（3 つ） | 114 ×3 | 224 ×3 |
| height（3 つ） | 120.98 ×3 | 101.48 ×3 |
| documentElement.scrollWidth / 幅 | 390 / 390 | 1024 / 1024 |
| 各ボタンの scrollWidth / clientWidth | 112 / 112 ×3（溢れなし） | 222 / 222 ×3（溢れなし） |

すべて指示どおり（y・width・height の差は 0、横スクロール無し、溢れ無し）。

## スクリーンショット（目視）

photo-390.png / photo-1024.png。絵文字（📷 🖼️ ✏️）は豆腐にならず表示。欠け・重なり・余計なものは無し。
- 食い違いではないが記録: 390 幅で「写真なしで入力」が「写真なしで入 / 力」と 1 文字だけ次の行に折り返される。溢れ（scrollWidth）は出ていない。直すかは管理者の判断（実害は未確認、見た目のみ）。
- 390 幅の画像には「1 写真 / 2 四隅…」のステップ表示が無く、1024 幅にはある（今回の変更で入ったものか既存の幅別の表示かは調べていない。判断できない）。

## #manual クリック（390 幅）

押下後、section#board は hidden でなく display:block、section#photo は hidden=true。OK。

## 差分の範囲

実装コミットの範囲は見ていない（依頼外）。作業ツリーの追加物は archives/agents/TODO-040/ のみ（check_layout.py、PNG 2 枚、この報告）。

## 確かめなかったこと

撮る・選ぶの押下、他の画面、pytest（依頼どおり）。

# 2 回目（未コミットの変更: analyzer/README.md、analyzer/static/index.html。#manual を「手で入力」＋small「写真なし・初期配置から」に変更）

check_layout.py を各幅 1 回。PNG は上書き。

| 項目 | 390x844 | 1024x768 |
|---|---|---|
| tips bottom / .pick top | 301.5 / 313.5 | 308.5 / 320.5 |
| 3 つの y | 313.5 ×3 | 320.5 ×3 |
| width ×3 | 114 ×3 | 224 ×3 |
| height ×3 | 117.08 ×3 | 101.48 ×3 |
| docSW / 幅 | 390 / 390 | 1024 / 1024 |
| 各ボタン scrollWidth / clientWidth | 112/112 ×3 | 222/222 ×3 |

画像（目視）:
- 主の文言（写真を撮る / 写真を選ぶ / 手で入力）は 390・1024 とも 1 行。折り返し無し。絵文字は豆腐無し、欠け・重なり無し。
- 報告のみ: 390 幅で small「写真なし・初期配置から」は「写真なし・初期配 / 置から」と 2 行に折り返される（1024 幅は 1 行）。溢れは無し。実害は未確認。

# 3 回目（small を「写真なし<br>初期配置から」に変更、未コミット）

check_layout.py を各幅 1 回。PNG は上書き。

| 項目 | 390x844 | 1024x768 |
|---|---|---|
| tips bottom / .pick top | 301.5 / 313.5 | 308.5 / 320.5 |
| 3 つの y | 313.5 ×3 | 320.5 ×3 |
| width ×3 | 114 ×3 | 224 ×3 |
| height ×3 | 117.08 ×3 | 117.08 ×3 |
| docSW / 幅 | 390 / 390 | 1024 / 1024 |
| 各ボタン scrollWidth / clientWidth | 112/112 ×3 | 222/222 ×3 |

画像（目視）: 390 幅の small は「写真なし / 初期配置から」の 2 行で、語の途中で折れていない。主の文言は 3 つとも 1 行。絵文字の豆腐・欠け・重なり無し。1024 幅も同じ 2 行（br による。1024 の height は前回の 101.48 から 117.08 に増え、3 つ揃っている）。
