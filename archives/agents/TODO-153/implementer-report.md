# TODO-153 implementer の報告

ブランチ `claude/crawford-cube-sync`、コミット d3658a2（push・PR はまだ）。

## 変更点

- `analyzer/static/app.js:657` `setCube`: 変えた後のキューブが片側で、クロフォードが入っていれば `setMatch({ crawford: false })` で外す（端末の `match` の保存も一緒に直る）
- `analyzer/static/app.js:665` `setMatch`: 直した後の match がクロフォードで、キューブが片側なら、キューブを `at: "centre"` に戻す（値と `offered` はそのまま。「中央」を選んだときと同じ）。`cubeFromPhoto` も false にする
- `analyzer/app.py:33`・`analyzer/static/app.js:14`: 0.86.0
- `analyzer/test_pwa.py:571` 新しいテスト。app.js から `setCube`〜`setMatch` を切り出し、仮の `state`／`update` で Node で動かす。クロフォードを入れる・キューブを片側にする・食い違わない操作（スコアだけ変える、中央のまま値だけ変える）の 4 通り
- `TODO.md` の 1 つ目のチェックを入れた

## 検証

- `node --check analyzer/static/app.js` 成功
- `uv run pytest analyzer/test_pwa.py -q` 32 passed（終了コード 0。警告 1 件は前からある Starlette の DeprecationWarning）
- 壊すと落ちるか: `toCentre` を常に false にした版、`setCube` の `setMatch` 呼び出しを消した版で、それぞれ新しいテストが落ちることを確かめて戻した

## 調べたこと 1: 保存された設定に食い違いがあるとき

`storedMatch()`（app.js:32）だけでは食い違わない。起動時のキューブは中央（app.js:72）。食い違いが入る経路は次の 3 つ。

| 経路 | 場所 | 今の扱い |
|---|---|---|
| 写真を開き直す（前回の写真・履歴）。キューブは写真ごと（`kept.cube`）、match は端末ごとなので、クロフォードを入れる前に片側にした写真を開くと食い違う | app.js:699 `startPhoto` | 「解析する」が灰色になり、`CRAWFORD_CUBE` を表示（app.js:175, 298） |
| 写真の読み取りでキューブが片側に読めた（キューブが中央で、クロフォードが入っているとき） | app.js:1010 | サーバーが `analysis_error` を返し、`alert(CRAWFORD_CUBE)`（app.js:1029）。盤面の画面でも上と同じ表示 |
| 手番の変更でダブルされたキューブを反対側へ移す | app.js:645 `setOnRoll` | 片側のまま動くだけなので、すでに食い違っていれば続く（新しくは起こさない） |

案:
- A（推奨）: そのまま `CRAWFORD_CUBE` で知らせる。どちらが「後の操作」か決められない（写真のキューブと端末のクロフォードは別々に決まる）ので、勝手に片方を変えない。直すときの 1 タップ（キューブを動かす／クロフォードを触る）は今回の同期で食い違いを解く
- B: 開いたとき・読み取ったときに、キューブを中央へ戻す（クロフォードを優先）。写真のキューブの読みが黙って消える
- C: 読み取ったときはキューブを「後」とみなしてクロフォードを外す。端末に残る match の設定が写真の読みで変わる

## 調べたこと 2: `CRAWFORD_CUBE` を残すか消すか

出る場所は `analyzeErrors`（app.js:175、「解析する」を灰色にする理由）と、読み取り後の `alert`（app.js:1029）の 2 つ。手の操作からは届かなくなったが、上の表の写真の開き直しと読み取りの経路からはまだ届く。

推奨: 残す。消すと、その 2 経路で「解析する」が理由なしに灰色になるか、サーバーの英語の `analysis_error` が出る。B か C を選んでも、開き直しの経路をすべて直さないかぎり残すのが安全。文言（「キューブを「中央」にするか、…クロフォードを外してください」）は今の操作でもそのまま当てはまる。

## 追記: main の決定を受けた変更（コミット 65b6bf2）

決定: 写真の開き直しと読み取りでは写真の方を後の操作とみなしてクロフォードを外す。値だけ変えても外すのは今のまま。`CRAWFORD_CUBE` は届く経路が残れば残す。

- `analyzer/static/app.js:698` `startPhoto`: 開いた写真のキューブが片側で、クロフォードが入っていれば `setMatch({ crawford: false })`
- `analyzer/static/app.js:1021` 読み取り: 写真からキューブが片側に読めて、クロフォードが入っていれば外す（`crawfordOff`）。サーバーはこのとき解析せずに `analysis_error` を返すので、alert を「キューブが片側に読めたので、クロフォードを外しました。「解析する」を押すと解析します。」に替えた（app.js:1037）。それ以外の `analysis_error` は今までどおり「解析できませんでした: …」
- **`CRAWFORD_CUBE` は消した**（`crawfordCube`・`CRAWFORD_CUBE`・`analyzeErrors` での使用・「解析する」の part の依存から `s.match.crawford`／`s.cube.at`）。理由: キューブ（`state.cube`）が片側になる経路は `setCube`、`startPhoto`、読み取り、`setOnRoll` だけで、クロフォードが入る経路は `setMatch` だけ。前の 3 つと `setMatch` で食い違いを解くようにした。`setOnRoll` はもともと片側のキューブを反対側へ移すだけなので、食い違いを新しく作らない。起動時のキューブは中央なので、`storedMatch` からも食い違いは生まれない。そのため app.js の中から食い違いに届く経路は残らない（テストの道具が `BgApp.update` で直接入れる場合は除く）
- `analyzer/test_pwa.py:368` `CRAWFORD_CUBE` の文字列を見ていた assert を、「`CRAWFORD_CUBE` が無いこと」と「`setMatch({ crawford: false })` の 3 箇所」を見る assert に替えた（`startPhoto`・読み取りの経路は、文字列があるかどうかしか見ていない）
- 検証: `node --check analyzer/static/app.js` 成功、`uv run pytest analyzer/test_pwa.py -q` 32 passed（終了コード 0）

## 残る懸念

- 読み取りのときの alert の文言は新しく足した（main の指示には無かった）。alert を出さずに黙って外す案もある。その場合は、ヘッダーの「（クロフォード）」が消えるのだけが手がかりになる
- 読み取りでクロフォードを外したあと、自動では解析し直さない。今までと同じく利用者が「解析する」を押す
- `analyzer/README.md:261` のサーバーの説明（クロフォードなのにキューブが片側なら `analysis_error`）はサーバー側の話なので、そのまま正しい
- `setCube` は、すでに食い違った状態でキューブの値や「ダブルされたところ」を変えたときも（片側のままなので）クロフォードを外す。「キューブを触った方が後」と読めば指示どおりだが、気になるなら `patch.at` が来たときだけに絞れる

## 追記 2（コミット 1d6fe6f）

- ユーザーの決定で、読み取りでクロフォードを外すときの alert を取り除き、黙って外すようにした（`analyzer/static/app.js:1036`。それ以外の `analysis_error` は今までどおり alert）。`uv run pytest analyzer/test_pwa.py -q` 32 passed

## 追記 3: レビューの指摘への対応（コミット 3380091）

- 要修正 1: `analyzer/README.md:79`（灰色にする条件からクロフォードを外した）、`:88`（キューブとクロフォードが後の操作に合わせて変わることを書いた）、`analyzer/static/index.html:253`（コメントから「クロフォードのキューブ」を外した）
- 検討 3: `analyzer/static/app.js:1036` クロフォードを外したときに黙るのは、`analysis_error` に `Crawford` が入っているときだけにした（サーバーの文言 `no doubling in the Crawford game: …`、`analyzer/analysis.py:95`）。ほかの理由は今までどおり alert を出す。サーバーの文言に頼っている点が残る
- 検討 4: `analyzer/static/app.js:1032` `setMatch({ crawford: false })` を、盤面を `update` した後に移した。`await` の途中で例外が出たり取り消されたりしても、クロフォードだけが外れることはない
- 要修正 2: `analyzer/test_pwa.py:572` `_crawford_js` を足した。app.js から `setCube`・`setMatch`・`startPhoto`・`recognize` を切り出し、仮の `state`・`$`・`BgApi` などを置いて Node で動かす。`test_crawford_and_a_cube_on_one_side_follow_the_later_choice`（:607）は 11 通りを試す。追加したケースは、片側のまま値だけ変える、写真を開き直す（キューブが片側／新しい写真）、読み取り（Crawford のエラー／別の理由のエラー／キューブが読めない）、盤面を入れる前に読み取りが例外で終わる。`:368` の文字列の assert は `CRAWFORD_CUBE` が無いことだけを残した
- 壊すと落ちるか（`uv run pytest analyzer/test_pwa.py -q -k crawford_and`。app.js を 1 か所ずつ変えて流し、元に戻した）:

| 壊し方 | 結果 |
|---|---|
| 1 読み取り後の alert で、黙る条件を外す（`!crawfordError` → `!false`） | 1 failed（終了コード 1） |
| 2 `startPhoto` の条件を反転 | 1 failed（終了コード 1） |
| 3 読み取りの `crawfordOff` の条件を反転 | 1 failed（終了コード 1） |
| 4 `setCube` に `patch.at &&` を足す | 1 failed（終了コード 1） |
| 5 検討 3: ほかの理由でも黙る（`crawfordError = crawfordOff`） | 1 failed（終了コード 1） |
| 6 検討 4: `setMatch` を `await` の前へ戻す | 1 failed（終了コード 1） |

- 検証: `node --check analyzer/static/app.js` 成功、`uv run pytest analyzer/test_pwa.py -q` 32 passed（終了コード 0）
- 残る懸念: `_crawford_js` は、切り出しの区切りとして関数の並び（`setResult`・`loadPhoto`・`analyze` が後に続くこと）に頼っている。並びが変わると、テストは誤って通るのではなく落ちる
