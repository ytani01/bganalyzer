# TODO-176 verifier-report

確認の対象: 盤の側（board-svg）が main と変わらないこと、写真の側（photo-svg）に image 以外の要素が無いこと。

## 条件

- main 側: origin/main（29c9ad5、analyzer 0.93.0）の一時 worktree をポート 8012 で起動
- ブランチ側: claude/photo-side-only（353a28b、analyzer 0.94.0）、ポート 8011
- Playwright（新しい Chromium、390x844、保存はオフ）。`samples/collected-galaxy-screen-1.jpg` を読み込み、
  truth の四隅・home・bottom_colour で「読み取る」→ 盤面の画面 → `#match-length` を 5 ポイントに設定
- 計測スクリプト: `/tmp/claude-649/-home-ytani-work-bganalyzer/fb72c0ee-9705-4252-832f-2c7589b4df40/scratchpad/measure.py`（各 1 回）

## 測った値

| | main board-svg | ブランチ board-svg | main photo-svg | ブランチ photo-svg |
|---|---|---|---|---|
| viewBox | `12 -55 683 524` | `12 -55 683 524` | `12 -55 683 524` | `20 24 616 392` |
| 子要素の数 | 143 | 143 | 32 | **1** |
| タグごと | rect 56, text 25, g 8, polygon 24, circle 30 | 同じ | rect 4, text 25, g 2, image 1 | **image 1** |
| innerHTML の長さ | 14803 | 14803 | 229461 | 227560 |

- board-svg: viewBox・子要素の数・タグごとの数・innerHTML の長さが main と一致（一致した）
- ブランチの photo-svg の子要素の一覧: `image[href]` の 1 つだけ。image 以外の要素は無い
- photo-wrap は両方とも表示されていた（hidden=false）。マッチの長さの値は両方 "5"

## 変更されたファイル（origin/main との差分）

`TODO.md`、`analyzer/app.py`、`analyzer/static/app.js`、`analyzer/static/board-view.js`、`analyzer/static/style.css`、`analyzer/static/sw.js`。
未追跡: `archives/agents/TODO-176/`。指示の範囲かどうかは、依頼に変更ファイルの指定が無かったので判断していない。

## 確かめなかったこと

- board-svg の中身の文字単位の比較は、innerHTML の長さと子要素のタグ別の数まで（長さが同じで中身が違う可能性は、実害は未確認だが排除していない）
- 写真の側の見た目（利用者が確認済みとのこと）
- 8011 と 8012 のサーバー、一時 worktree は片付け済み
