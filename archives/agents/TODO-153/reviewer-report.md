# TODO-153 reviewer 報告

範囲: `git diff origin/main...HEAD`（TODO.md、analyzer/app.py、analyzer/static/app.js、analyzer/test_pwa.py）。
`uv run pytest analyzer/test_pwa.py -q` は 32 passed。実害は未確認のものは「未確認」と書いた。

要修正 2 件、検討 3 件、好みの範囲 1 件。

## 要修正

### 1. 文書に古い記述が残っている（3 か所）
- `README.md:79` 「クロフォードのゲームでキューブが中央でないときは、「解析する」をグレーアウトし、その上に理由を出す」
  - 今の app.js の `analyzeErrors` は駒の数・盤の空だけ見る（`app.js:169-171`）ので、この条件では灰色にならない
- `README.md:88` 「キューブを片側に置いているあいだは「解析する」を押せない」
  - 同じ理由で古い。実際は「キューブを片側にするとクロフォードが外れる／クロフォードを入れるとキューブが中央に戻る」
- `analyzer/static/index.html:253` コメント「解析できない理由（駒が多い・駒が無い・クロフォードのキューブ）」
  - クロフォードのキューブは理由に出なくなった
- 根拠: `rg "クロフォード" README.md analyzer/static/index.html`。CLAUDE.md の「文書との整合」観点。
- 古くない（サーバーの話）: `README.md:164`・`:194`・`:200`・`:261`（`analysis_error` を返す仕様はサーバーに残っている）

### 2. テストが壊しても落ちない箇所がある（実測）
作業ツリーのコピーで app.js を 4 通りに壊して `analyzer/test_pwa.py` を流した。**4 通りとも 32 passed（落ちない）**。

| 壊し方 | 場所 | 結果 |
|---|---|---|
| 読み取り後の alert の `&& !crawfordOff` を外す（黙って外す仕様が消える） | `app.js:1036` | 落ちない |
| `startPhoto` の条件を `state.cube.at === "centre" && ...` に反転 | `app.js:698` | 落ちない（文字列 `state.match.crawford) setMatch({ crawford: false });` の個数だけ見ているため） |
| 読み取りの `crawfordOff` の条件を `patch.cube.at === "centre" && ...` に反転 | `app.js:1021` | 落ちない（`if (crawfordOff) setMatch(...)` の文字列があるだけで通る） |
| `setCube` の条件に `patch.at &&` を足す（片側のまま値だけ変えたときに外さなくなる。ユーザー仕様の「片側のまま値を変えたときも」が消える） | `app.js:655` | 落ちない。新しい Node のテストは中央のまま `{value: 4}` を試すだけで、片側のまま値を変えるケースが無い |

- 根拠: 実測（コピーに `sed` で変えて pytest。報告の末尾に手順）。CLAUDE.md の「テストは壊すと落ちるか」
- Node で動かして確かめているのは `setCube`／`setMatch` だけ。`startPhoto` と `recognize` の分岐（ユーザー仕様の 2 つ目の項目、alert なし）は文字列があるかどうかしか見ていない

## 検討

### 3. 読み取りの `alert` の抑え方が広い（未確認）
- `app.js:1036` `if (data.analysis_error && !crawfordOff) alert(...)`
- `crawfordOff` が真のとき、`analysis_error` は「クロフォードなのにキューブが片側」とは限らない。`analysis.py` は他のエラー（駒の数など）を先に返しうる。その場合も alert が出ない。
- 「解析する」は灰色になり理由が出るので実害は小さそう。実際に別の理由が重なる読み取りを流して確かめてはいない（未確認）

### 4. 読み取りで `setMatch` を呼ぶ位置が `await` の前（未確認）
- `app.js:1021-1022` で `setMatch({ crawford: false })`（`keep` で端末の設定も書き換わる）を呼び、そのあとに `await mine.scan.reveal(...)` / `done()` がある。
- ここで例外が出た・取り消された場合、盤面は反映されないのにクロフォードだけ外れた状態が残りうる。そうなるかは確かめていない（未確認）

### 5. TODO.md の「調べてから決めること」が決まったまま残っている
- `TODO.md:72`: 「保存された設定の食い違いの扱いと、`CRAWFORD_CUBE` を残すか消すか」が未決のまま書かれている
- 決まったこと（写真・読み取りを後とみなして黙って外す、`CRAWFORD_CUBE` は消した）は TODO.md に書かれていない。決着のとき archives に入るので、そのとき直すなら不要

## 好みの範囲

### 6. `startPhoto` の `update` のあとの `setMatch`
- `app.js:697-698` は `update` のあとに別の `update`（`setMatch` 内）が走り、途中の 1 回は食い違った状態で描画される。害は無いはず（食い違いのエラー表示をやめたので）。1 回の `update` にまとめる手もあるが、`keep` が要るので今のままでもよい

## 問題の無い点（1 行）
- 分岐（ユーザー仕様 1〜4）
  - バージョン（`CLAUDE.md` の「バージョン」）: `app.py` と `APP_VERSION` はともに 0.86.0 で揃っている
  - 「後の操作に合わせる」: `setCube`（片側なら外す。値だけ変えても外す）と `setMatch`（クロフォードを入れたら中央へ。`cubeFromPhoto` も false）はユーザー仕様どおり。順序は `setCube` が先に `setMatch({crawford:false})` を呼び、その中の `toCentre` は偽になるので二重には動かない
  - 写真の開き直し: `startPhoto` で外す。alert なし
  - 読み取り: `crawfordOff` で外す。alert なし
- `CRAWFORD_CUBE` を消してよいか
  - `state.cube` を片側にする経路（`setCube`・`startPhoto`・読み取り・`setOnRoll`）と、`state.match.crawford` を真にする経路（`setMatch` だけ。`storedMatch` は起動時で、起動時のキューブは中央）を `rg "cube:|cube\b.*update|match" app.js` で全部読み、食い違いが残る経路は見つからなかった
  - `setOnRoll` は片側のキューブを反対側へ動かすだけで、中央から片側にはしない
  - `setDie` は `offered` を直すだけ
  - 食い違いが残るのは `BgApp.update` を直接呼ぶ道具・テストだけ（`tools/` に `crawford` を使うものは無い）
- 食い違わない操作の振る舞い
  - `analyzeErrors` と「解析する」の `part` の依存（`s.match.crawford`・`s.cube.at` を外した）は、駒の数・盤の空のエラーには影響しない
  - 実測: 新しい Node のテストの「クロフォードでないときにスコアだけ変える」（`other_match`）と「中央のまま値だけ変える」（`other_cube`）が通る
- コメントは「なぜ」を書いている。範囲外の変更は無い

## 作り込みすぎ
- `app.js:169-171` `analyzeErrors` は今は `BgBoard.errors` を呼ぶだけの薄い関数（5 か所から使われている）。消せるが、呼び出しを 5 か所変えることになるので、そのままでよい（好みの範囲）
- それ以外は、消せるものなし

## 付録: 壊し方の実測手順
作業ツリーの `analyzer/` を `/tmp/claude-649/-home-ytani-work-bganalyzer/a3d02edb-801a-4f15-9d58-10706c233937/scratchpad/m/analyzer/` にコピーし、`sed` で app.js の該当行だけ変えて `pytest analyzer/test_pwa.py -x`。変えた行は `diff` で確かめた。作業ツリーのファイルには触れていない。

---

# 再レビュー（`git diff 1d6fe6f..HEAD`、コミット 3380091）

`uv run pytest analyzer/test_pwa.py -q` は 32 passed。要修正 2 件は直っている。検討 3・4 も直っている。判断が要る点が 1 つだけ残る。

## 前回の指摘が直っているか

- **要修正 1（文書）: 直っている。** `analyzer/README.md:79`（灰色の条件から外れた）、`:88`（キューブとクロフォードが後の操作に合わせて変わる、写真の開き直し・読み取りでも外れる、と書き直した）、`analyzer/static/index.html:253`（コメントから外れた）。`rg "クロフォードのキューブ"` はヒット無し。
- **要修正 2（テスト）: 直っている。** 作業ツリーのコピーで app.js を 6 通りに壊して `analyzer/test_pwa.py` を流した。6 通りとも 1 failed で落ちた（元の 4 通りと、下の 2 通り）。
  - 読み取り後の alert の黙る条件を外す
  - `startPhoto` の条件を反転
  - `setCube` に `patch.at &&` を足す（片側のまま値だけ変えたとき）
  - 黙る条件を `true` にして、別の理由の `analysis_error` でも黙らせる
  - 正規表現を小文字 `/crawford/` に変える
  - `setMatch` を `await` の前に戻す（検討 4）
- **検討 3: 直っている。** `app.js:1036` の `crawfordError = crawfordOff && /Crawford/.test(data.analysis_error || "")`。別の理由（駒が 16 個）の `analysis_error` では alert が出る。テストは Node で `recognize` を動かして確かめている。
- **検討 4: 直っている。** `setMatch({ crawford: false })` を盤面の `update` のあとに移した。読み取りが途中で取り消されるとクロフォードは外れたままにならない（Node のテストの `cancelled` ケースで確認）。

## 残る点（要判断）

### 7. サーバーの文言を変えても `test_pwa.py` は落ちない（実測）
- `analyzer/test_pwa.py:609` は、サーバーの文言を写した文字列 `"no doubling in the Crawford game: ..."` を自分で持っていて、`analysis.py:95` の本物の文言は見ていない。
- 実測: コピーの `analysis.py:95` を `no doubling in this game: ...`（`Crawford` が消える）に変えた。`analyzer/test_pwa.py` は 32 passed のまま。
- ただし `analyzer/test_api.py::test_api_photo_match`（`test_api.py:597` の `"Crawford" in j["analysis_error"]`）が落ちた。文言を変えると CI の `test` は落ちるので、気づかれずに壊れるわけではない。
- 注意点: 落ちるのは別のファイルのテストで、「app.js が `Crawford` で見分けている」ことを知らせる印はどこにも無い。直す人が `test_api.py` の assert を新しい文言に合わせて直すだけだと、app.js は黙らなくなり、alert「解析できませんでした: …」が出る（実害は未確認）。`app.js:1035` のコメントか `analysis.py:95` の近くに「app.js が `Crawford` を見ている」と書く手はある。直すかは管理者が判断する。
- 参考: 変更後にも `analysis.py:92`（スコアが合わないときのクロフォードのエラー）にも `Crawford` が入っており、同じ正規表現に当たる。`fixMatch` を通すのでこの組み合わせは起きないはず（未確認）。

## 新しく出た問題
- 無し。`git diff 1d6fe6f..HEAD` の範囲に、指示に無い変更も、規約違反も見つからなかった（`TODO.md` は触っていない）。
- 作り込みすぎ: テストの `_crawford_js` は仮の `state`・`$`・`BgApi` を 20 行ほど置いて app.js を切り出す。ほかのテストに同じ形のものが無いので新しい道具になるが、`startPhoto`・`recognize` の分岐を実際に動かして確かめるのに要る分で、削れない。残る懸念（実装の報告にもある）: 切り出しの区切りが関数の並び（`setResult`・`loadPhoto`・`analyze`）に頼っていて、並びが変わると誤って通るのでなく落ちる。
- 付録の手順: 作業ツリーを `/tmp/claude-649/-home-ytani-work-bganalyzer/a3d02edb-801a-4f15-9d58-10706c233937/scratchpad/m2/` にコピーし、`samples/` は symlink。コピーの app.js と `analysis.py` だけ変えた。作業ツリーのファイルは触っていない（`git status` は報告ファイルのディレクトリだけ）。
