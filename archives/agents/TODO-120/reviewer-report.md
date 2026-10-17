# TODO-120 レビュー（reviewer、2026-10-17）

対象: `git diff`（fb43b62 以降）と未追跡の `analyzer/test_side.py`。コードは直していない。
壊すと落ちるかを試した変更は、そのたびに元へ戻した（md5 で確かめた）。

要修正: 0 件。検討: 5 件。好みの範囲: 1 件。

## 検討

### 1. 集めた写真（`POST /samples`）に「横から」が残らない

- 場所: `analyzer/static/app.js` の `sendSample` / `sampleOf`（`sample.js` の `truth`）、`analyzer/samples.py`
- 何が起きるか: 横からのモードで解析した写真も、今までと同じ truth（`corners_TL_TR_BR_BL`・`home` など）で
  `collected/` に保存される。`side` は入らない。あとから見ても、横から撮った写真か、右からか左からかが分からない。
  `recognizer/collected.py` は普通のモードで測るので、横からの写真の結果は低く出て、集めた写真の測定の数字も下がる（実害は未確認）
- なぜ問題か: TODO-120 の節に「いったん今の試作でアプリに出し、使いながら写真を集める」とある。集める目的に直結する。
  依頼（brief2.md）の範囲外なので、入れるか別の項目にするかは管理者の判断

### 2. 左からの読み取りの `geometry`（H の半回転）がテストで守られていない

- 場所: `recognizer/side.py:309`（`H = exact.mul3(H, [[-1, 0, w], [0, -1, h], [0, 0, 1]])`）、`analyzer/test_side.py` の `test_reading_from_the_right_and_the_left`
- 何が起きるか: この行を `pass` に替えても `test_side.py` は 8 件すべて通った（実測）。
  この行が無いと、左から撮った写真で、アプリが重ねる盤・駒・数の位置が半回転してずれ、ダイスとキューブも違う所を探す。
  ポイントの数は `moved` と `lay` だけで決まるので、テストの「12 ずれた並び」は変わらない
- いまの実装は正しい: photo5 を回したものを `side="left"` で読み、`info["geometry"]["corners"]` が渡した四隅と一致した
  （`[[379.1, 1379.7], [394.6, 617.9], [1070.1, 684.3], [1318.1, 1373.0]]` が両方で同じ）
- 直し方の目安: 右と同じく、左でも `geometry["corners"]` が渡した四隅に重なることを確かめる 2 行

### 3. 「Claude に選ばせる」が横からのモードを知らない

- 場所: `analyzer/static/app.js` の `claudeCorners`、`analyzer/claude_corners.py:27` の `PROMPT`
- 何が起きるか: プロンプトは「写真の下にいる人から見た」左上・右上・右下・左下を求める。横からのモードでは、四隅の順は手前の人から見たもの
  （右からなら写真の右上が TL）なので、Claude の四隅をそのまま `side` 付きで読むと 90° ずれた向きで読む（実害は未確認。Claude を設定したサーバーだけ）
- 選択肢: 横からのモードではボタンを隠す／順を並べ替える／このまま（文書に書く）

### 4. 写真の履歴を開き直したとき、四隅とモードが食い違いうる

- 場所: `analyzer/static/app.js` の `historyRecord`（`keepCorners` は残すが `sideMode`・`sideFrom` は残さない）と `startPhoto`
- 何が起きるか: モードは端末に 1 つだけで、写真ごとには残らない。横からで読んだ写真を、モードをオフにしてから履歴で開き直すと、
  手前の人から見た順で保存された四隅のまま、普通のモードで読む（逆も同じ）。開き直したときは四隅を探し直さないので、気付きにくい（実害は未確認）
- 担当が決めた「切り替えで四隅を捨てる」とは別の経路

### 5. 担当が決めた 4 点

- 斜めの警告を出さない（`board.py:211`）: 問題なし。photo5 を回したものは傾き 42.2° で、出していれば警告が出る。テストもこれで落ちる（実測）
- side では `keep_corners` が効かない: 問題なし。横からの読み取りはもともと四隅を合わせ直さないので、常に `keep_corners` 相当。analyzer/README に書いてある
- 切り替えで手置きの四隅を捨てる（`cornersAfresh`）: 検討。四隅の番号は普通のモードでも「手前から見て 1. 左上…」で置くので、
  利用者が手で置いた四隅はモードの前後で意味が変わらない。捨てると置き直しになる。自動で見つけた四隅（写真の下を手前とした順）は捨てるのが正しい。
  `cornersMoved` のときだけ残す、という分け方もある（実害は未確認）
- 点数が低くても四隅を返す（`_guess` に `MIN_SCORE` が無い）: 試作のままで、依頼の範囲では問題なし。
  `null` になるのは候補が 1 つも無いときだけなので、PWA は「見つからない」を出さず、外れた四隅を「見つかった」として出す。
  analyzer/README の `/find-corners` の説明（「corners は null」）には、横からでは null になりにくいことは書いていない

### 6. 初めてオンにして左右を選ばないまま読むと、普通のモードで読む

- 場所: `analyzer/static/app.js` の `sideSent`（`state.sideMode && state.sideFrom`）
- 何が起きるか: チェックは入っているが `side` は送らない。四隅も探し直していないので、普通の四隅と普通の読み取りで揃ってはいる。
  問いかけ（`#side-ask`）は出ているので、気付ける（実害は未確認。ブラウザでは試していない）

## 好みの範囲

- `analyzer/app.py` の `_side`（8 行）: FastAPI の `Literal["right", "left", ""] | None` で 422 まで任せられる。ただし `home` も手で確かめているので、今のままでも既存の書き方に揃っている

## 問題の無かった観点

- `side` を渡さないとき（recognizer）: `recognize` の後半を `_finish` へ移しただけで、行の中身は同じ。渡す `corners` は従来どおり snap 後のもの、`quality` も同じ。変わるのは `save_debug` の書く順だけ。`find_corners(search=None)` は従来の `guess`
- `side` を渡さないとき（API）: 空・無しは `None` で、`find_corners`・`recognize` を従来の引数で呼ぶ。違いは `/find-corners` が毎回 `side` モジュールを import することだけ
- `side` を渡さないとき（PWA）: `sideMode` の既定は off、`sideSent()` が null なら何も足さない。セグメントの再描画に `sideFrom` が加わっただけ
- 四隅の向き: `side._order`・`find_corners_side` の `order`（`[2, 3, 0, 1]`、自分自身が逆）・`fixed` の並べ替え・`corners` 段の並べ替え・`read_side` の半回転が一貫。PWA は順を変えずに送り返すだけで、番号の表示（`CORNER_NAMES`「手前から見て」）とも合う。scan.js の `candidates` は順に依らない
- PWA の切り替え・左右を聞く条件・localStorage（`stored`/`keep` は try/catch で、使えなくても既定値で動く）・左右の選び直し・2 か所で `side` を送る: 依頼どおり
- 壊すと落ちるか（実測、`uv run pytest analyzer/test_side.py`）: 元のまま 8 passed。斜めの警告を side でも出す → 1 failed。`corners` 段を並べ替えない → 1 failed。H の半回転を消す → 落ちない（上の 2）。担当が試した 4 件と合わせ、2 を除けば効いている。PWA のテストは文字列の一致で、既存の test_pwa.py と同じやり方
- 版: recognizer 0.23.2 → 0.24.0、analyzer 0.67.0 → 0.68.0 と `APP_VERSION` が一致（test_api.py:162 が確かめる）。機能の追加なので minor で正しい
- 文書: README・recognizer/README・analyzer/README・docs/corners.md の向き・段の順・`side` の値・`keep_corners`・警告の扱いはコードと合っている。旧版や消えた `read_side` の古い説明の残りは無い（`rg`）
- 範囲: 依頼に無い変更は無い（measure_side.py は読み取りの入口を変えた分の追従）

## 作り込みすぎ

作り込みすぎ: なし（`_side` は上の「好みの範囲」。`_finish` の切り出しと `search=` の引数は、横からのモードが普通のモードの部品を使い回すのに要る最小限）
