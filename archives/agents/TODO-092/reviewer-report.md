# TODO-092 reviewer の報告

対象: ブランチ `claude/todo-092` の未コミットの差分（`TODO.md`、`analyzer/app.py`、`analyzer/static/app.js`、
`analyzer/static/board-view.js`、`analyzer/static/style.css`）。コードを読んで確かめた。テストは流していない。

要修正: 0 件。

## 検討

### 1. `analyzer/README.md:70-72` / 盤面図の説明に U 字形の矢印が無い

盤面図に何が出るか（ダイスの絵はどこにどの色で、キューブはどの行のどちらの端に）を README が書いているが、
今回足した手番の進み方の U 字形の矢印には触れていない。ユーザーに見える変更なので、ダイスの絵の説明の近くに
1 文あってよい（「盤の真ん中に、次に振る人の進む向きを U 字形の矢印で出す。写真の表示には出さない」程度）。
`analyzer/README.md:83`「最善手は盤面図に矢印で出る」は結果の画面の節なので、直す画面から矢印が消えた今も合っている。
ただ、盤面図に「矢印」が 2 種類になったので、U 字形の方を書くときは呼び分けると読み違えにくい。

## 好みの範囲

### 2. `analyzer/static/board-view.js:72` / `!photo` の判定が次の行と重なる

`if (!photo && scene.onRoll) drawWay(...)` の直後が `if (photo) return;`。drawWay を return の後ろへ移せば
`if (scene.onRoll) drawWay(svg, scene.onRoll, home);` で済む。間に入る drawBorneOff は盤の外の行に描くので、
重なり順（駒の上・ダイスの下）は変わらない。

## 問題が無かったもの

- 矢印の向き（4 通り）: `BgBoard.pointAt` と照らして合っている。home right では points[23] が上の行の右端、
  points[0] が下の行の右端。home left では上の行の左端、下の行の左端。white は上の行をホームの側から反対の端へ進み、
  下の行をホームへ戻る（y0=上、y1=下）。black はその逆。始点 `xHome`、曲がる側 `xTurn`、矢じり（`xHome` で
  進む向き `dir` を向く）がすべて駒の進む順に合う。
- arc の sweep: SVG（y 下向き）で sweep=1 が時計回り。home right・white は 上→左→下 で反時計回り（0）、
  home right・black は 下→左→上 で時計回り（1）、home left・white は 上→右→下 で時計回り（1）、
  home left・black は 下→右→上 で反時計回り（0）。式 `(y0 < y1) === right ? 0 : 1` はこの 4 通りと一致する。
  端点の間がちょうど直径なので large-arc は効かない。
- 左右の対称: 両端は盤の端から 82 の内側（home right で xHome=554、曲がりの外側 102。home left はその鏡写し）。
- app.js: `{ ...scene, move: null }` は浅いコピーで、`scene.move` は drawMove でしか読まれない。直す画面の
  タップ（`select` はそのまま渡している）、選択の枠、写真を並べる表示（photo-svg には元の scene を渡す）、
  結果の画面（result-svg は元の scene）に影響は無い。`part` の依存に `moveToShow(s)` が残るのは result-svg のため必要。
- タップ: U は hit の矩形より後に描かれるが、`.way` に `pointer-events: none`（継承される）で下のポイントに届く。
  `.way` という class は他に使われていない。
- onRoll が無いとき: `scene.onRoll` が偽なら描かない（state の初期値は "white"）。ダイスは後に描くので U の上、
  キューブと上がった駒は盤の外の行なので重ならない。最善手の矢印も後に描くので U の上。
- 版: `__version__` と `APP_VERSION` が 0.55.0 で揃っている（`analyzer/test_api.py:160` が見ている）。機能の追加なので
  マイナーを上げるのは CLAUDE.md の「バージョン」どおり。
- コメント: drawWay の説明は「なぜ駒の上・ダイスの下か」「どこから回るか」を書いていて、TODO 番号もある。
- テスト: 盤の描画（board-view.js）には今もテストが無く、見た目は確認の担当が画面で見る分担なので、足りないとは見ない。
- 範囲: 指示に無い変更は無い。TODO.md のチェックと「決めたこと」の書き換えは規約どおり。
- 作り込みすぎ: なし（上の 2 を除く。縁取りを path と polygon で 2 重に描くのは見た目の決定なので評価しない）。
