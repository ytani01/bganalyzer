# TODO

**残っている項目: TODO-025、TODO-030、TODO-079、TODO-121、TODO-178、TODO-179、TODO-180。** これまでに 173 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**次の番号は `TODO-181`。**
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

## TODO-178. 四隅の画面の並びと文言の調整

| | main | 担当 |
|---|---|---|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet / medium）+ verifier（Haiku / medium）。並びと文言だけで挙動は変わらないのでレビュー担当は付けない（TODO-177 と同じ） |

四隅の画面（`analyzer/static/index.html` の `#corners`）について、2026-10-20 にユーザーが頼んだ 4 点。

- [ ] チェックボックスの行（四隅を固定する・横から撮った）を、回転のボタン（`#turn-tools`）よりも上、写真のすぐ下へ移す（ユーザーが決めた）。横から撮ったの「撮った位置」の行（`#side-from-row`）はチェックボックスの行に付いていく
- [ ] 「写真が Anthropic に送られます」の文（`#claude-note`）を削除する（ユーザーが決めた）。それを出し入れしている JS も消す
- [ ] 「画像を編集」ボタン（`#edit-start`）を `#turn-tools` の左端に移す
- [ ] 「やり直す」ボタン（`#corner-reset`）の文言を「四隅をクリア」にする
- [ ] analyzer の版を直しとして上げる（`analyzer/static/app.js` の `APP_VERSION` も揃える。TODO-177 と前後するので、実装時の main の版から上げる）
- [ ] ローカル: マージ後にローカルホストで更新し、4 点が見えるかを確かめる

**無駄を省く工夫:** TODO-177 と同じ。並びと文言だけの変更なので、確認は live_view（`BG_CDP=http://127.0.0.1:9222`）で見える画面を 1 回確かめるだけにし、テスト全体は CI に任せる

## TODO-179. 背景の塗りつぶし処理で、盤の周りを広めに残す

| | main | 担当 |
|---|---|---|
| 見込み | Sonnet 5.5 / effort medium | implementer（Opus / medium）+ reviewer（Opus / medium）→ verifier（Sonnet / medium）。塗る範囲が変わる分岐の変更なので reviewer を付ける。reviewer を先、verifier を後 |

読み違いの組を `samples/` に入れるときの背景の塗りつぶし処理（`recognizer/import_collected.py` の `paint`）は、今は四隅のちょうど外を黒くする。
元の写真と大きく変わり、精度の改善に役立たないことが多い（2026-10-20 ユーザーの指摘）。

- [ ] 四隅を盤の中心から外へ、盤の大きさの 10% 広げた四角の外を黒くする（ユーザーが決めた）。写真の外にはみ出す分は写真の端で止める
- [ ] すでに `samples/` にある `collected-*` のうち、`collected/` に元の写真が残っている組は、新しい幅で塗り直して入れ替える（ユーザーが決めた）。元が無い組はそのまま
- [ ] 入れ替えたら `check_accuracy.py --update` で基準を書き直し、`recognizer/README.md` の精度の表も直す
- [ ] CLAUDE.md の「変えないもの」の `samples/` の記述（盤の外を黒く塗る）を、盤の周りが広く残ることに合わせて直す。広く残る分、手や周りの物が公開の写真に写りやすくなる点も書く
- [ ] 版: `import_collected.py` は測る道具ではなくアプリの外の取り込みなので、recognizer の版を上げるかは実装時に CLAUDE.md の「バージョン」で判断する
- [ ] ローカル: マージ後にローカルホストで確かめるものがあれば足す（実装時に判断）

**何を決めるか:** `collected/` の元の写真が Pi にだけあり開発機に無い場合、どこで塗り直すか。**選択肢:** 元の写真を開発機へ持ってくる／Pi で塗り直す。**いつ聞くか:** 実装の前（まず `collected/` が開発機にあるかを見る）。

**無駄を省く工夫:** 確かめるのは 2〜3 組の塗り直しの画像を目で見ることと、CI の `accuracy`。全サンプルを手元で測り直さない

## TODO-180. worktree の変更を PR なしで main に取り込む

| | main | 担当 |
|---|---|---|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet / medium）+ reviewer（Opus / medium）→ verifier（Sonnet / medium）。文言と CI の条件が変わるので reviewer を付ける。reviewer を先、verifier を後。verifier は、この項目自身の取り込みで、ブランチを push して CI が走るか・ff-only で取り込めるかを確かめる |

worktree で編集したあと main に取り込むたびに PR を作るのをやめたい（2026-10-20 ユーザーの依頼）。
参考は `../meltype-fcitx5-dev/CLAUDE.md` の「担当（teammate）」の節（worktree のブランチを main が `git merge --ff-only` で取り込み、PR は作らない）。

決まったこと（2026-10-20 ユーザーが決めた）:

- 担当はブランチ `claude/<作業内容>` を origin に push して CI を走らせ、通ったら main を最新にして ff-only で取り込み、main を push する。落ちたものは main に入れない。ff-only にならないときは rebase して CI をやり直す
- main への push は担当が行う（bganalyzer では push・マージは許可済み）
- `recognizer/import_collected.py` が読み違いの組を `samples/` に入れる自動の PR は今のまま
- 仕掛かりの TODO-177（PR #525）は PR のまま終える

- [ ] `.github/workflows/test.yml`・`ruff.yml`・`accuracy.yml` を `claude/**` への push でも走るようにする（今の paths の絞り込みは保つ）
- [ ] CLAUDE.md の「共同開発」（PR・マージ・`gh pr merge --delete-branch`・マージ前の CI の記述）、docs/HANDOVER.md、そのほか PR を前提にした記述（`rg -n -e 'PR' -e 'gh pr' -e 'マージ' CLAUDE.md docs/ .claude/ README.md` で洗い出す。`archives/` は直さない）を新しいやり方に直す。取り込んだあとの origin の `claude/*` ブランチも消す
- [ ] 共同開発の相手（別アカウントの Claude）にも同じやり方になることを docs/HANDOVER.md に書く
- [ ] ローカル: 取り込み後に、トップの作業ツリーで `git pull` して main が最新になることを確かめる

**何を決めるか:** CI の待ち方（`gh run watch` など）を CLAUDE.md に書くか。**選択肢:** 書く／書かない。**いつ聞くか:** 実装の中で出たとき。

**無駄を省く工夫:** 文書と CI の条件だけの変更なので、確かめるのはこの項目自身の取り込み（push で CI が走る・ff-only で入る）の 1 回だけ。テスト全体は CI に任せる

## TODO-181. 駒の数の吹き出しにも、モーダルと同じ枠と影を付ける

| | main | 担当 |
|---|---|---|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet / medium）+ verifier（Haiku / medium）。見た目だけで挙動は変わらないのでレビュー担当は付けない（TODO-177 と同じ。2026-10-20 ユーザーが了承） |

長押ししたポイント・バーの色と駒の数を選ぶ吹き出し（`analyzer/static/index.html` の `#palette`）に、TODO-177 で `.sheet` に付けた太い枠・色・濃い影を同じように付ける（2026-10-20 ユーザーの依頼）。

- [ ] `analyzer/static/style.css` の `.sheet` の枠（4px の `var(--accent)`）・影（`0 8px 28px #000b`）・角丸・背景を、`.palette` と共通の規則にする（値を 2 か所に書かない）。吹き出しの位置・動き・中身（幅 232px・余白・ボタン）は保つ
- [ ] analyzer の版を直しとして上げる（0.94.1 → 0.94.2。`analyzer/app.py` と `analyzer/static/app.js` の `APP_VERSION` を揃える）
- [ ] ローカル: マージ後にローカルホストで更新し、長押しした吹き出しの枠が 4px の `--accent` で影が濃く、位置と中身が変わっていないことを確かめる

**無駄を省く工夫:** TODO-177 と同じ。確認は live_view（`BG_CDP=http://127.0.0.1:9222`）で吹き出しを 1 回開いて、枠・影・位置を読み出すだけにし、テスト全体は CI に任せる

## 完了済み

決着した項目は `archives/todo/` にある（1 項目 1 ファイル）。
一覧は [archives/index.md](archives/index.md)（新しい順）。やらないと決めたものは
ファイル名に（対応しない）が付いていて、理由も書いてある。蒸し返す前に読むこと。
