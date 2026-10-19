# TODO

**残っている項目: TODO-025、TODO-030、TODO-079、TODO-121、TODO-171、TODO-172、TODO-173、TODO-174。** これまでに 166 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**次の番号は `TODO-175`。**
項目には、何をするか・決めたこと・無駄を省く工夫だけを書く。経緯や測定値は README・archives に置く（2026-10-16 に縮めた。前の文面は git の履歴にある）。

---

## TODO-025. キューブ判断（ダブル／テイク／パス）

決めたこと: アンリミテッド（ジャコビー・ルールあり、ビーバーなし）。ダイスがあればチェッカーの手、キューブが片側でダイスが無ければ「その側がダブルされた」。
解析・PWA（analyzer 0.17.0）、キューブの場所（recognizer 0.6.1）、数字（0.21.0、`samples/synth-cube-*` で確かめた）は済み。

- [ ] 本物のキューブ（4・8・16 など）を片側に置いた写真が手に入ったら `samples/` に入れて確かめる（ユーザーの写真待ち。ネットには無かった。PI-032）

**無駄を省く工夫:** 写真が届いたら、その写真だけを `evaluate.py` で測る（全サンプルは CI）

## TODO-030. ユーザーの盤の写真と直した盤面で、認識の精度を上げる

決めたこと: `collected/` から `samples/` へは Pi の Claude が人の顔・第三者のものを隠して PR を作り、チェックが通ればマージする。
書き出し（analyzer 0.24.0）・「Pi に残す」（0.25.0）・`recognizer/tune.py` は済み。

- [ ] 写真を集める（ユーザー）
- [ ] たまった組を `samples/` に入れ、`evaluate.py` で測って読み違いを直す（README の「精度」を更新）

- [ ] 50〜100 枚たまったら、ポイントごとの駒の数を当てる小さなモデルを試す（TODO-081 から戻した。`--slots`・`--section` は採らないと決めた）

**無駄を省く工夫:** `tune.py` は写真がまとまってから 1 回だけ流す。`samples/` に入れた組は CI の accuracy に任せる

## TODO-079. photo-black-blue-oblique のサイコロ（緑の透明なもの）が読めない

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（測定・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

`samples/photo-black-blue-oblique.jpg`（TODO-076）の 6・2 のサイコロを読めない。小さく透明な緑のサイコロで、バーの近くの駒の脇にある。

- [ ] どこで崩れるかを切り分ける
- [ ] 直すかどうかを決める（このサイコロだけの事情なら対応しないで閉じてもよい）

**無駄を省く工夫:** 切り分けは photo-black-blue-oblique だけで行う

## TODO-121. 横から撮った写真のモードの精度を上げる

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（切り分け・判断）+ implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

TODO-120 で、横から撮った写真のモード（`recognizer/side.py`）を試作の精度のままアプリに出した（2026-10-17 ユーザーが決めた）。
6 枚で、見つけた四隅で読むと 86/144、正解の四隅なら 105/144。四隅の点数（`corners._structure` を借りている）で、三角形の根元を切った四角形や縁に隠れた形が正解に勝つ。
駒は今の円の検出のままで、縁に隠れた駒、駒の上面のずれ、バーに隠れるポイントで外れる。

- [ ] 横から撮った写真が 20 枚ほどたまるのを待つ（ユーザー。「横から撮った」で保存すれば正解に `side` が残り、読み違いのある組は自動で samples/ に入る）
- [ ] たまった写真で、四隅の点数の付け方と駒の数え方の案を試し、ユーザーに選んでもらう
- [ ] 選んだ案を実装する（recognizer の版を上げる）

**何を決めるか:** 四隅の点数の付け方と駒の数え方。**選択肢:** 写真がたまってから試して出す。**いつ聞くか:** 試したあと。

**無駄を省く工夫:** 測るのは横からのサンプルだけ（`evaluate.py`・`check_corners.py` は正解の `side` を見る）。TODO-120 の試しの道具（`archives/agents/TODO-120/measure_side.py`）を使い回す

## TODO-171. 手前の色と home を石の並びから推測する

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium）。reviewer を先に回す |

4 通りの向き（色 × home）のうち両者のピップ数の合計が最も少ないものが、TODO-170 の後なら 140 組すべてで正解と一致する見込み。今は手前の色を取り違えると PIP が 262/325 のような値になる（2026-10-20 ユーザーの報告）。推測するのは色と home の両方（ユーザーが決めた）。

- [ ] 着手時に、どこに組み込むか（recognizer の読み取りの後か、PWA か）を調べて決める
- [ ] 実装する（recognizer か analyzer のバージョンを上げる）
- [ ] ローカル: 色を逆に置いた写真で、手前が正しく選ばれるか（TODO-170 の後に着手する）

**何を決めるか:** 組み込む場所。**選択肢:** recognizer の読み取りの後／PWA。**いつ聞くか:** 着手時に調べたあと。

**無駄を省く工夫:** 確かめるのは 140 組の一致を計算するだけ（写真を読み直さない）。精度は CI の accuracy に任せる

## TODO-172. 四隅の検出処理をリファクタリングして速くする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | implementer（Opus 5.5 / high）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium）。コードが変わるので reviewer を入れ、先に回す |

四隅の検出（`recognizer/corners.py` と、そこから呼ばれる処理）を、アルゴリズムを変えずにリファクタリングし、処理を速くする（2026-10-20 ユーザーが決めた）。

- [ ] 着手時に、`check_corners.py` で時間のかかっている所を測ってから、直す所を決める
- [ ] 実装する（recognizer の版を上げる。結果が変わらない直しなので patch）
- [ ] 全サンプル（`samples/` の 87 組）で、書き換えの前後の四隅の座標が完全に同じであることを確かめる。全サンプルを流すのはこの 1 回だけで、時間も同じ実行で測る
- [ ] 速くなったかは開発機だけで測る（Pi では測らない）

**無駄を省く工夫:** 精度は CI の accuracy に任せる。Pi では測らない。ローカルの確認は要らない（アプリの見た目も結果も変わらないため）

## TODO-173. 四隅の検出の後の盤面の読み取りをリファクタリングして速くする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | implementer（Opus 5.5 / high）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium）。コードが変わるので reviewer を入れ、先に回す |

四隅が決まった後の読み取り（石・バー・サイコロ・キューブなど。`recognizer/board.py` から呼ばれる処理）を、アルゴリズムを変えずにリファクタリングし、処理を速くする（2026-10-20 ユーザーが決めた）。四隅の検出（TODO-172 の範囲）は含めない。**TODO-172 と同じファイルを触る可能性があるので、TODO-172 と同時に着手しない。**

- [ ] 着手時に、読み取りの部分の時間を測れる道具を選び（`check_corners.py` ではない）、時間のかかっている所を測ってから、直す所を決める
- [ ] 実装する（recognizer の版を上げる。結果が変わらない直しなので patch）
- [ ] 全サンプルで、四隅を正解（`*.truth.json`）に固定して読んだ盤面の結果（points・bar・サイコロ・キューブ・home など、読み取りの出力すべて）が、書き換えの前後で完全に同じであることを確かめる。測る道具は `recognizer/evaluate.py` など既存のものから着手時に選ぶ。全サンプルを流すのはこの 1 回だけで、時間も同じ実行で測る
- [ ] 速くなったかは開発機だけで測る（Pi では測らない）

**無駄を省く工夫:** 精度は CI の accuracy に任せる。Pi では測らない。ローカルの確認は要らない（アプリの見た目も結果も変わらないため）


## TODO-174. worktree の中ではコミット ID が読めず、バージョンのテストが落ちる

| | main | 担当 |
|---|---|---|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet 5.5）+ reviewer（Opus 5.5 / medium）+ verifier（Sonnet 5.5）。分岐が変わるので reviewer を入れ、先に回す |

`analyzer/app.py` の `git_commit()` は `.git` をディレクトリとして読む。worktree では `.git` が `gitdir: …` と書いたファイルなので None を返し、`analyzer/test_api.py` の `test_version_reports_both_parts_and_commit` が落ちる（TODO-171 の実装中に見つかった）。アプリの `/version` も worktree で起動するとコミット ID が出ない。

直し方: `git_commit()` が `.git` のファイルの `gitdir:` をたどるようにする。ref は worktree の gitdir になければ、`commondir` の先（本体の .git）の loose ref と packed-refs から読む。git コマンドには頼らない（Pi に git が無くても動くようにしている今の方針を保つ）。

- [x] 実装する（analyzer の版を patch で上げ、`APP_VERSION`（`analyzer/static/app.js`）も揃える）
- [x] worktree の場合のテストを足す（一時ディレクトリに `.git` のファイルと gitdir・commondir を作る）
- [x] worktree の中で、そのテストと `test_version_reports_both_parts_and_commit` が通る

**無駄を省く工夫:** テストは `analyzer/test_api.py` の version まわりだけ流す（全体は CI に任せる）。ローカルの確認は要らない（トップの作業ツリーは worktree ではないため）


## 完了済み

決着した項目は `archives/todo/` にある（1 項目 1 ファイル）。
一覧は [archives/index.md](archives/index.md)（新しい順）。やらないと決めたものは
ファイル名に（対応しない）が付いていて、理由も書いてある。蒸し返す前に読むこと。
