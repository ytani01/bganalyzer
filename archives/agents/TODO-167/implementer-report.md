# TODO-167 implementer の報告

## 実測（実装の前）

- gnubg の Python 拡張に `gnubg.eq_to_mwc(equity, cubeinfo)`（別名 `eq2mwc`）がある。マッチの `cube_info` を渡すと MWC（0〜1）が返る
- 7 ポイントマッチ・3-5 で、`_cube_hint` の読んだキューブフルのエクイティをこれで変換した値と、gnubg 自身の hint を `set output mwc on` で出した値を比べた。
  キューブ 1: 29.67 / 40.05 / 28.19（gnubg: 29.67% / 40.05% / 28.19%）、キューブ 2（2-4）: 37.18 / 50.00 / 36.55（gnubg: 37.19% / 50.00% / 36.55%）。
  差は、hint の表示から読んだエクイティが小数 3 桁に丸めてあることによる 0.01% だけ
- 候補手の `score` と、キューブレスの評価の `equity`（EMG）も、手番の側の `cube_info` で変換すると後手で 50% 未満になる（向きが合っている）

## 変更

- `analyzer/engine.py:31-37` docstring。`:84-86` マッチでは hint に `mwc` を足す（キューブの前の値の `ci` で変換）。
  `:95-99` マッチでは候補手に `mwc` を足し、戻り値の 5 つ目にキューブレスの MWC（マネーは None）
- `analyzer/analysis.py:130-133` 5 つ目を受け、候補手の `mwc` を % に。`:145-149` `equity` のコメントに EMG と書き、結果に `mwc`（{white, black} の %、マネーは None）。
  `:160-164` `mwc_pct`（% で小数 2 桁、gnubg の表示と同じ）。`:177-178` `cube.mwc`（マネーは None）。終局は `mwc=None`（`:114`）
- `analyzer/static/result.js:28-41` `signed`（常に符号、丸めてから付けるので -0.000 にならない）と `moveValue`（1 位は値、2 位以下は差。マッチは MWC %、マネーはエクイティ）。
  `:64` 候補手。`:75-77` 勝率の表: マネーは「キューブレス エクイティ」、マッチは「キューブレス MWC」と「キューブレス EMG」。符号を付けた。
  `:80` 注記「勝率とエクイティはキューブなし」→「勝率はキューブなし」（表の行に語を入れたため。「2手読み」の部分は TODO-166 のため触っていない）。
  `:105-108` キューブの表: 見出しを「キューブフル エクイティ」/「キューブフル MWC」、マッチは MWC % で出す
- 版: `analyzer/app.py:33` と `analyzer/static/app.js:14` を 0.90.1 → 0.91.0
- テスト: `analyzer/test_api.py:901-` `test_match_winning_chances`、`analyzer/test_pwa.py:717-` `test_moves_as_differences_and_match_winning_chances`
- `TODO.md` の TODO-167 の 3 つにチェック

## 検証

- `uv run pytest analyzer/test_api.py`: 50 passed、1 failed（`test_version_reports_both_parts_and_commit`。worktree の `.git` がファイルのため、既知）
- `uv run pytest analyzer/test_pwa.py`: 35 passed
- 壊すと落ちるか: 次の 5 つの変更をそれぞれ入れて流し、すべて落ちた（戻してある）
  - `signed` の `+` を消す / マネーの差を差でなく値にする / マッチの差を差でなく値にする（test_pwa）
  - 候補手の MWC を相手側の `ci_opp` で変換する / キューブの MWC を `ci_opp` で変換する（test_api）

## 判断が要る点・残る懸念

- MWC は小数 2 桁（gnubg と同じ）、差も `-1.42%` のように 2 桁。勝率の表の勝率は今のまま小数 1 桁
- 候補手 1 位の数字は、マネーでは「エクイティ」とだけ書いている（キューブレスの値）。キューブレスと付けるかは reviewer に見てほしい
- キューブの MWC は、hint から読んだ小数 3 桁のエクイティを変換するので、gnubg の表示と最大 0.01% ずれることがある
- 範囲外（文書なので触っていない）: `analyzer/README.md:180-193` の API の説明に `mwc`（結果・候補手・キューブ）が無い。`:94` の結果の画面の説明も「エクイティ」のまま

## レビューの指摘への対応（2 巡目）

ユーザーが決めた 3 点を直した。

1. 候補手がキューブなしであること: 注記を「最善手と勝率はキューブなし」に戻した（`analyzer/static/result.js:80`。ラベルには付けない）。
   `analyzer/README.md:94` に同じことを書いた。テスト: `analyzer/test_pwa.py:737`
2. キューブ 2 以上の MWC の変換: `analyzer/test_api.py` の `test_match_winning_chances_with_a_bigger_cube` を足した。
   7 ポイント 2-4 で手前がキューブ 2 を持つ。パスなら 4-4 になるので、局面によらず `double_pass` が 50% になる
   （1 で変換すると 3-4、4 で変換すると 6-4 になって外れる）
3. ダブルされた局面の勝率の表: `analyzer/analysis.py:126-130` で、gnubg に渡すキューブを今の値（ダブルした後）にした。
   キューブの判断の MWC は、ダブル前のキューブで `cube_info` を作り直して変換する（`analyzer/engine.py:84-89`）。
   キューブレスの `equity`（EMG）も今のキューブで数えることになる。ダイスがあるときはダブルされた局面にならないので、候補手は変わらない。
   `analyzer/README.md:192` に書いた。テストは 2 と同じ関数で、ダブルされた局面の `mwc`・`equity` が、キューブ 2 を持っているだけの局面と同じこと、
   キューブの判断の MWC がキューブ 1 の局面と同じことを見る

検証:
- `uv run pytest analyzer/test_pwa.py`: 35 passed
- `uv run pytest analyzer/test_api.py`: 51 passed、1 failed（`test_version_reports_both_parts_and_commit`。worktree の `.git` がファイルのため、既知）
- 壊すと落ちるか（3 通りとも落ちた。戻してある）: gnubg に渡すキューブをダブル前の値に戻す、キューブの判断を今のキューブの `ci` で変換する、
  キューブの判断を常にキューブ 1 で変換する
