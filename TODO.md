# TODO

**残っている項目: TODO-025、TODO-030、TODO-079、TODO-121、TODO-170、TODO-171。** これまでに 165 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**次の番号は `TODO-172`。**
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

## TODO-170. 向きが逆になっている正解ファイル 9 組を直す

| | main | 担当 |
|---|---|---|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet 5.5）+ verifier（Sonnet 5.5）。挙動は変わらないので reviewer は無し |

両者のピップ数の合計が少ない向きを手前とする推測を 140 組の正解で試したら 131 組が一致した。残る 9 組を点検したところ、9 組とも正解ファイルの向き（手前の色・home）が写真と逆だった（点検の報告: `archives/agents/TODO-170/truth-check-report.md`）。

- [x] 報告の表のとおりに直す（色だけ 4 組、色と home 4 組、home だけ 1 組）
  - samples/ の 4 組: collected-grey-red-top、collected-tan-black-side-1、collected-cork-green-side、photo-orange-black-oblique
  - collected/ の 5 組（リポジトリに入らない。手元で直すだけ）: user-1792130519864-ajxlol、user-1792243400742-p1vm5a、user-1792161634938-n8fzpw、user-1792179058872-xlkxee、user-1792407219093-7qrh2u
- [x] orange-black の 3 組（photo-orange-black-oblique、n8fzpw、xlkxee）は note の「白が手前」と食い違うが、点検の判断（手前は灰色、home=left）で直し、note も書き直す（2026-10-20 ユーザーが決めた）。collected-cork-green-side の note も実情に合わせる
- [x] samples/ の 4 組は accuracy の基準が変わるので、`check_accuracy.py --update` を同じ PR に入れる
- [x] 直した後の 140 組で、ピップ数の合計が少ない向きと正解が一致するかを計算して確かめる

**無駄を省く工夫:** 写真の再点検はしない（済み）。認識の精度は CI の accuracy に任せる

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


## 完了済み

決着した項目は `archives/todo/` にある（1 項目 1 ファイル）。
一覧は [archives/index.md](archives/index.md)（新しい順）。やらないと決めたものは
ファイル名に（対応しない）が付いていて、理由も書いてある。蒸し返す前に読むこと。
