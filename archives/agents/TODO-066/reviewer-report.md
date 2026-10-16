# TODO-066 reviewer の報告

対象: `git diff`（未コミット）と `archives/agents/TODO-066/`。測定に使ったスクリプトは
`/tmp/claude-649/-home-ytani-work-bganalyzer/dcc187aa-2bdd-4f7e-8207-e133f5cdfc3d/scratchpad/`（edge.py・ciopp.py・fav.py・photo.py。リポジトリには置いていない）。

## 要修正

### 1. `analyzer/analysis.py:136` マッチでは「有利」の側が勝率 50% 未満になる（実装者の判断点 1 と同じ件）

- 問題: `favourite` はエクイティの符号で決めている。マッチではエクイティがマッチの勝率から出るので、見出しが自己矛盾する。
  実測（初期配置・手前の番・7 ポイント 3-5、plies 0）:
  `7 ポイントマッチ 手前 3 対 奥 5。奥が有利: 勝率 47.9%（ギャモン 13.0%）…。手前はダブルすべき、奥はテイク`
- 根拠: fav.py の出力。マネーでも理屈の上では起きるが、マッチでは初期配置のようなありふれた局面で起きる。
  読み上げ（`result.js` の `standingToSpeech`）は勝率 53% 未満なら「ほぼ互角」なので矛盾しないが、画面の `<h2>`（`r.summary`）には出る
- 直し方（`favourite` を勝率で決める／マッチだけ文言を変える）の選択は管理者の判断。`favourite` は README の「エクイティが高い側」とも対になっている

## 検討

### 2. `analyzer/app.py:291`（`_photo_result`）クロフォードのまま写真に片側のキューブが写ると、読み取りごと 422 になる

- 問題: PWA は手でキューブを置いていなければ `cube_value` を送らず、サーバーが写真のキューブ（片側なら 2 以上・持ち主あり）を使う。
  そこにクロフォードが付くと `analyze()` が `ValueError` を出し、`_run` の 422 が `/analyze-photo` 全体の応答になる。
  読み取った盤面（`recognized`）も返らず、PWA は「読み取りに失敗しました」で止まる
- 根拠: photo.py で実測（`cube: {"at": "white", "value": 2}` を返す recognize、7 ポイント 6-3・クロフォード）→
  `422 {"detail":"no doubling in the Crawford game: the cube stays at 1 in the middle"}`。
  盤面の誤り（`pos.validate()`）のときは `analysis: None` で盤面を返して直させる作りなので、それと揃っていない
- ヘッダーの値は端末に残るので、前の対局のクロフォードを付けたまま次の写真を読む、は起こりやすい。
  キューブの読み違い（中央を片側と読む）でも同じになる。どう扱うか（盤面は返して analysis だけ失敗にする等）は管理者の判断

### 3. PWA の盤面の画面: クロフォードでもキューブを置け、`/analyze` が英語の 422 を出す

- 問題: `index.html:213` 付近のキューブの欄はクロフォードでもそのまま使える。置いて「解析する」と
  `alert("解析に失敗しました: no doubling in the Crawford game: …")` になる（`app.js` の `analyze()` の catch）
- 根拠: コードを読んだだけ（PWA は操作していない。未確認）。サーバーの検証（`analysis.py:86`）は依頼どおり
- 境界線上の判断（UI で止めるか、今のままでよいか）は報告だけ

### 4. `analyzer/test_api.py` マッチで `_complete_moves` の相手側の cube info（`ci_opp`）を守るテストが無い

- 問題: `ci_opp` のスコアを入れ替え忘れても、今のテストはどれも落ちない（上がりの手の補完のテスト `test_api_moves_bearing_off_are_whole` はマネーだけ）
- 根拠: ciopp.py で `engine._engine` を直接呼び、`_cube_infos` を差し替えて実測（`e24HABDZAAAAAA`、3-1、plies 2）:
  - 7 ポイント・手番側 5・相手 3: 正しい実装は 1 位 `3/off 1/off` (1.709)・4 位 `3/2* 3/off` (1.171)。
    `ci_opp` を入れ替えないと **1 位 `3/2* 3/off` (1.709)・4 位 `3/off 1/off`** と手の名前が入れ替わる
  - 3-5 と 3 ポイント 0-1 では、入れ替えなし・マネーのどちらでも同じ結果（このスコアでは捕まらない）
  - `ci_opp` をマネーにした誤りは、試した 3 つのスコアのどれでも結果が変わらない（捕まえる局面は見つけていない。未確認）
- 足すなら `{"position_id": "e24HABDZAAAAAA", "dice": [3, 1], "match_length": 7, "score_white": 5, "score_black": 3}`
  で `moves[0] == "3/off 1/off"`（`on_roll` は既定の white。実装はいまこれで通る）

### 5. `analyzer/README.md:40-66`（PWA の使い方）にヘッダーのマッチの欄が無い

- 問題: 依頼は「API の説明」だけだったので実装者は API の節だけ直した。PWA の使い方の節は各画面の操作を一つずつ書いているが、
  ヘッダーのマッチ・スコア・クロフォード、端末に残ること、結果の画面で直すと解析し直すこと、が無い。
  `:66` の読み上げの説明（「最初に…続けてキューブの判断と形勢」）にも、最後にマッチのスコアを読むことが無い
- 根拠: `rg -n 'マッチ|スコア' analyzer/README.md` は API の節（128〜161、193 行）にしか当たらない

### 6. `analyzer/analysis.py:154` `Optional double, take` が「まだダブルしない」になる（実装者の判断点 2）

- gnubg の下調べ（README.md）でマッチでは出ることがあると分かっている。`startswith(("double", "redouble"))` に当たらず
  `double: false`・`too_good: false` →「手前はまだダブルしない（ダブルされたら奥はテイク）」。どちらとも言える局面を「しない」と言い切る。
  今回の測定ではこの文は出なかった（未確認）。どう読ませるかは管理者の判断

## 好みの範囲

- `analyzer/static/style.css:89-93` マッチの規則が `header .bar2 { }` と `header .bar2[hidden]` の間に入り、bar2 の対が割れている
- `TODO.md` の TODO-066 のチェックボックスがまだ空（実装できた時点で入れる決まり。管理者の作業）

## 問題なし（1 行ずつ）

- スコアの向き: `cube_info(…, move=0, …, (手番側, 相手))` と `set turn 0` → `set score 手番側 相手` は揃っている。白黒を入れ替えた局面で同じ答え（テスト）と、逆順で 4 本落ちる（実装者の確認）
- キューブの持ち主: `lies`（0 = 手番側、1 = 相手）と `ci_opp` の反転は正しい。ただしキューブなしの評価では持ち主は効かない（実測: 手前持ち・奥持ちとも 0.351）
- `doubled` のとき評価・hint はダブル前（`ask`）のキューブで、持ち主はダブルした側（0）。正しい
- gnubg の状態: 評価・最善手・補完は cube info を全部書くようになり、セッションに頼らない。マッチ → マネーは `new session`、マネー → マッチは毎回 `new match`。マッチの後のマネーが前と同じ（実測 edge.py の最後の 2 行、テスト）
- 検証の分岐: 長さ 0〜64、マネーでスコア・クロフォード不可、スコア 0〜N−1、クロフォードは片方だけ N−1、クロフォードはキューブ 1。テストの `bad` が各分岐を 1 つずつ当てている
- クロフォードの流れ: hint が `You cannot double.` → `_parse_cube_hint` が None → `cube: None`・`moves: None`。クロフォードの後のリード側・死んだキューブ・1 ポイントマッチも None（実測）。トレイル側はダブルの判断が出る
- PWA: 部品は `<header>` に 1 つだけで 4 画面とも出る（`#busy` は z-index 20 でヘッダー 5 の上を覆うので、解析中には触れない）。localStorage は `keep`／try-catch と同じ形。`inputsKey` に `s.match` が入り、盤面の画面で直すと結果が古い扱い。結果の画面（`step === "outcome"`）で直すと `analyze()`、`resultStale()` が真なので本当に解析し直す。`/analyze-photo` にも `matchRequest` を渡している
- テストの強さ: スコア逆順・マネーの cube info・`new session`・`set crawford` の 4 つを壊すと落ちる（実装者の確認）。PWA の 2 つ目のテストは文字列の一致だが、このファイルの既存のテスト（`rollWho` など）と同じ書き方
- 版: `__version__` と `APP_VERSION` とも 0.48.0。recognizer は変えていない
- `docs/PI_CHECKS.md` の PI-048: 決まりどおり（担当・次の番号・残っている項目）

## 作り込みすぎ

- `analysis.py:86`: delete: `or doubled`。`doubled` は `cube_value >= 2` を前の検証（`:72-73`）で求めているので、`cube_value != 1` だけで足りる
- `analysis.py:118` と `engine.py:69`: yagni: 評価に渡すキューブの持ち主。キューブなしの評価では効かない（上の実測）。数だけ渡せば `lies` の持ち主の式と `ci_opp` の反転が消える。将来キューブありの評価にするなら要る（残すかは好みの範囲）
- `cube.js:47`: shrink: `matchRequest` の `fixMatch` の二度がけ。`state.match` は `storedMatch`・`setMatch` で既に整えてある。フィールドの付け替えだけでよい（ただしテストは `matchRequest(null)` を呼んでいる）
- `cube.js:35`: shrink: `[0, ...Array.from({ length: 25 }, (_, k) => k + 1)]` → `Array.from({ length: 26 }, (_, k) => k)`

net: -4 lines possible.
