# TODO-177 implementer 報告

## 変更
- `analyzer/static/index.html`: `#count-mark` と `#reset-start` を盤面図の `.board-wrap` の中の `.match-row`（盤面図の上に重ねる行）へ移した。下の「初期配置」の行は削除
- `analyzer/static/style.css`
  - `.match-row` / `.reset-start` / `.count-mark`: 盤面図の幅（`cqw`）に合わせた大きさで、左に駒の数、右に初期配置。ポイントマッチの文字は SVG のまま中央
  - `.sheet`: 枠 4px・`var(--accent)`、影 `0 8px 28px #000b`
  - `.seg[data-name="plies"]`: 文字 12px、余白と高さ（28px）を小さく、幅は内容なり
  - 2 列表示のとき `#photo-svg` を幅 95%（中央寄せ）
- `analyzer/static/board-view.js`: `COL.score` 32 → 43（幅 `COL.w` と同じ）、`COL.tray` 101 → 90（列の合計を保つ）、`MATCH_H` 26 → 34（行の上のボタンの高さ）、持ち出しの駒の `hgt`/`step` 4/5 → 3.5/4.4（15 個でも数字がトレイに収まる）
- `analyzer/static/app.js`: `APP_VERSION` 0.94.1。結果画面では `#reset-start` を隠す（盤面図が結果画面へ移るため。前は盤面画面だけにあった）
- `analyzer/app.py`: `__version__` 0.94.1
- `TODO.md`: 6 点と版上げにチェック（ローカルの行は残した）

## 確認
- `uv run ruff check` / `uv run ruff format --check`: どちらも通った（All checks passed! / 58 files already formatted）
- chromium（`/usr/bin/chromium`、playwright）で 8001 番のサーバーに 390px 幅で接続: アンリミテッドと 11 ポイントマッチで、駒の数・マッチの文字・初期配置が重ならず、横スクロールなし（`scrollWidth` 390）。最悪の場合（クロフォード＋⚠ の長い文）で駒の数の右端 93px、マッチの文字の左端 98px、初期配置の左端 333px
- 1200px 幅でも崩れなし。モーダルは枠が太い緑で、影が濃いのを目で確認（背景は暗くしていない）
- スコアのカードは 43×43 で、トレイと重ならない
- 2 列表示（写真を並べる）の 95% は、CSS 1 行だけなので実際の写真では見ていない

## 懸念・判断が要る点
- 範囲を少し超えた変更: `MATCH_H` を 26 → 34 にした（ボタンが指で押せる高さに近づけるため）。盤面図全体の縦が 8 ほど増える
- 2-ply/3-ply は `min-height: 28px` で「全ての押すものは 44px」の既存の決まりより低い（利用者が了承）
- 持ち出しの駒の表示（トレイが 90 に縮み、駒の厚みを少し減らした）は 15 個の場合を目では見ていない

## 追記（ユーザーの判断を受けた直し）
- 駒の数・初期配置の文字は 12px 以上（`style.css` の `max(12px, …cqw)`）。マッチの表示を短くした: `board-view.js` の `drawMatch` を「11pt」「11pt クロフォード」「アンリミテッド」に、`.match-n` を 21（390px 幅で 12px 相当）に
- 実測（390px、playwright、3 種のマッチの文字 × ホームの左右、`getBoundingClientRect`。駒の数は最悪の文「⚠ 白 16/15・黒 14/15」）: 駒の数 6–123、マッチ（ホーム右）アンリミテッド 134–228・11pt 164–198・クロフォード付き 126–236、初期配置 325–384。ホーム左はマッチが右へ寄るので、より余裕がある。重なりなし、横スクロールなし（`scrollWidth` 390）。駒の数・初期配置は `getComputedStyle` で 12px
- 一番狭いのは「11pt クロフォード」と駒の数の間で 3px
- MATCH_H 34・結果画面で初期配置を隠すこと・ply ボタン 28px は、ユーザーが了承

## 追記 2（verifier の指摘: 盤が空のときの重なり）
- `app.js:271` の駒の数の警告を「⚠ 盤に駒がありません」→「⚠ 駒がありません」に短くした（`board.js` の解析ボタンの理由の文は変えていない）
- 実測（390px、ホーム右、盤の数字を全部押して空にし、マッチの文字を「11pt クロフォード ▾」にした）: 駒の数 5.8–103.9、マッチ 126.2–235.7。重なりなし（間 22px）。文字は 12px のまま
