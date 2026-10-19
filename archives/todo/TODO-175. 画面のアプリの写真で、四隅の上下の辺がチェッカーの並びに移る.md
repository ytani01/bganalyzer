# TODO-175. 画面のアプリの写真で、四隅の上下の辺がチェッカーの並びに移る

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | implementer（Opus 5.5 / high）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium）。コードが変わるので reviewer を入れ、先に回す |
| 実施 | Opus 5.5 / effort high | implementer（Opus 5.5 / high、案の試しと実装の間も同じ担当）+ reviewer（Opus 5.5 / high、2 回）+ verifier（Sonnet 5.5 / medium）。reviewer を先に回した |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main と担当（分けられない） | Opus 5.5・Sonnet 5.5 | 上の表のとおり | 404 | 91,573 | 530,434 | 12,083,655 | 100% |
| 合計 |  |  | 404 | 91,573 | 530,434 | 12,083,655 | 計 12,706,066 |

- `token-usage.py TODO-175 --since '2026-10-20 07:12:00'` の値（TODO-173 のマージのあとから、決着の前まで）。原因を調べた 07:00〜07:12 の分は含まない。teammate のログが担当ごとに分かれず、すべて main の行に出た
- モデル別では Sonnet 5.5 が 58%、Opus 5.5 が 42%（main と verifier が Sonnet 5.5 の分を含む）

## きっかけ

`collected/user-1792442165190-hedmzy.jpg`（Backgammon Galaxy の画面の写真）で、四隅の上の辺（ポイント 13 側）が、ポイント 13〜21 のチェッカーの上の端を結ぶ斜めの線になった。
正しい上の辺は、上下の辺の候補（`_h_lines` の 6 本）に入らない。ポイント番号の行の外枠の強い線が、近い線を抑制範囲（±12）で吸っていた。
盤の外を走る辺を内側へ移す `_swap` の規則は、条件（`_inner` 0.75 以上）を満たす唯一の線、チェッカーの上の端の線に移した。

## やったこと

- チェックの 3 つ目は「`check_corners` で全サンプルを比べた（verifier の報告）。accuracy は正解の四隅で読むので四隅の変更を測らない」に書き直して決着させた
- 直し方の案を 4 枚（hedmzy・collected-galaxy-screen-1・screen-app-green-far・collected-champions-screen）で試した（`archives/agents/TODO-175/implementer-report.md`）
  - 案 A（候補の抑制を傾きごとにする）: 直らない。正しい上の辺は最強の線と傾きがほぼ同じで 7px しか離れていない。傾きの違う辺が吸われていたのではなかった
  - 案 B（`_swap` で傾きが大きく変わる線には移さない）: 傾きの差の上限が 4 以上なら何も変わらず、2 なら悪化した
  - 案 C（利用者が選んだ。2026-10-20）: 盤の外を走る辺を内側へ移すときだけ、点数順でなく今の線に近い順に試し、内側と見なす基準 `INNER_IN` を 0.75 → 0.6 にする。両方が要る
- `recognizer/corners.py` の `_swap` に案 C を入れた（recognizer 0.29.3）
  - 全サンプルの比較で commons-tavli-red-brown の四隅のずれが悪くなった（1.1% → 2.7%）。原因は `INNER_IN` 0.6 と近い順の組み合わせで、盤の外から出発した上の辺が、今の線より外側の線（`_inner` 0.667）へ先に動いていた。**内側（向かい側の辺の方向）へ動く線にだけ移す**条件を足して直した
  - 近い順にすると、点数で選ぶ差し替えも「点数の上位 2 本」でなく「近い 2 本」を見る。内側へ移したあと、点数の高い遠い線（チェッカーの上の端）へ戻らないために意図した変更で、コメントに理由を書いた
- hedmzy を `samples/collected-galaxy-screen-9` に入れた（利用者の指示で盤の外は塗らない元の写真。四隅の座標が変わらない）。基準と README の精度の表に足した
- `analyzer/test_corners.py`: この写真で左上の四隅のずれが 35px 未満（main では 51px で落ちる）。main の `corners.py` に戻すと落ちることを確かめた
- `recognizer/README.md` の手順 6 に、60%（0.29.2 までは 75%）、近い順、内側へ動く線にだけ移すことを書いた

## 確かめたこと

- hedmzy の左上の四隅のずれが 51px → 19px（`archives/agents/TODO-175/measure.py`）。点数の誤りは正解の四隅でも検出の四隅でも 1 点で変わらない（四隅の見た目の直し）
- reviewer が 2 回読んだ。1 回目は要修正 2 件（テストが塗った写真では main と区別できない、版は 0.30.0 でなく 0.29.3）、検討 3 件。2 回目（red-brown の直しのあと）は要修正なし
- verifier が `check_corners.py` で画面の写真 13 枚を main と比べた（`archives/agents/TODO-175/verifier-report.md`）: collected-galaxy-screen-9 だけが 2.5% → 0.9% に良くなり、ほかの 12 枚（red-brown を含む）は同じ。CI の accuracy は正解の四隅で読むので、四隅の変更は測らない

## 分担の振り返り

- **implementer**: 案を 4 枚で試し（A・B が効かないと数値で示した）、C を見つけた。実装したあと、塗った写真では main と区別できないテストを書いた。reviewer に指摘されて直した。red-brown の悪化は verifier の全サンプルの比較で初めて見つかった（試しの 4 枚には入っていなかった）
- **reviewer**: 要修正 2 件を見つけた。テストの無効と版の付け方。検討で「点数で選ぶ差し替えの見方も変わる」を見つけ、意図した変更だと分かった。red-brown の悪化は読んだだけでは見つけられなかった（実害は未確認と添えていた）
- **verifier**: red-brown の悪化を見つけた。これがこの項目で唯一の、実測でしか見つからなかった欠陥
- 見込みと食い違った点: 試す写真を画面のアプリの写真 3 枚に絞った。`INNER_IN` を下げる案なので、**盤の上下の辺が本物の盤の枠を走る写真（red-brown のような）を 1 枚入れるべきだった**
- 次に同じ規模なら: 基準や許容を緩める案は、試しの写真に「緩めても変わってはいけない写真」を 1〜2 枚入れる。そうすれば verifier の前に悪化が見つかる。reviewer と verifier の順は今のまま（reviewer を先）でよい
