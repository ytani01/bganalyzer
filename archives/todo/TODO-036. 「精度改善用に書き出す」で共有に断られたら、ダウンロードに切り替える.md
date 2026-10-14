# TODO-036. 「精度改善用に書き出す」で共有に断られたら、ダウンロードに切り替える

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5 / medium） |
| 実施 | Opus 5.5 / effort low | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | low | 28 | 6,196 | 10,506 | 1,111,901 | 82% |
| reviewer | Opus 5.5 | high | 14 | 66 | 45,465 | 199,857 | 18% |
| 合計 |  |  | 42 | 6,262 | 55,971 | 1,311,758 | 計 1,374,033 |

- verifier は定義のモデルが haiku。壊したアプリをビルドし直して FAIL を確かめる実測があるので Sonnet 5.5 に上書きした
- verifier は終点のコミット（2dfbfe4）のあとに動いたので、上の表に入っていない（完了の通知では 26,471 トークン）

## きっかけ

PI-014（2026-10-14）で、Android の Chrome で「精度改善用に書き出す」を押すと「書き出せませんでした: Permission denied」になった。
Chrome は共有できるファイルの種類が決まっていて `.json` は入らないため、`navigator.share` が `NotAllowedError` で断ると見ている
（`canShare` は通る）。`AbortError` 以外をそのまま投げていたので、ダウンロードにも切り替わらなかった。
`tools/pi_ui_check.py` の `export` は共有の機能を消して試すので捕まえられなかった。

## やったこと

- `analyzer/static/app.js`: 共有が `AbortError`（利用者が閉じた）以外で失敗したら、2 つのファイルをダウンロードする
- `tools/pi_ui_check.py`: 共有が `NotAllowedError` で断る場合の確認 `export-denied` を足した
- analyzer を 0.25.3 に上げた（`APP_VERSION`、sw.js のキャッシュ名 v32）
- docs/PI_CHECKS.md: 表に `export-denied` を足し、PI-018 を足した

## 確かめたこと

- verifier: `pi_ui_check.py export export-denied` が両方 OK。app.js を直す前に戻すと `export-denied` だけ FAIL（alert「書き出せませんでした: Permission denied」）、終了コード 1（[verifier-report.md](../agents/TODO-036/verifier-report.md)）
- main: Pi の bganalyzer イメージにリポジトリを入れて pytest。1 failed, 39 passed, 6 skipped。落ちたのはイメージに git が無いための既知の `test_version_reports_both_parts_and_commit` だけ
- reviewer: 直す指摘なし（[reviewer-report.md](../agents/TODO-036/reviewer-report.md)）

## 残ること

- 共有に断られたあとのダウンロードは、操作による許可（transient activation）が切れた状態で行われる。Android の Chrome で 2 つ目が止められるおそれがある（実害は未確認）。偽の share はすぐ断るので `export-denied` では捕まらない。PI-018 のスマホでの確認で見る
- 共有にもダウンロードにも失敗したときは、画面に何も出ない

## 分担の振り返り

- reviewer は、偽の share では user activation の切れを再現できないことを見つけた。これを受けて PI-018 のスマホの確認に「1 つだけ落ちたら書く」を足した。verifier は、直す前に戻すと `export-denied` が落ちることを実測した。pytest は samples/ の無いイメージで走らせたので 8 件落ちたと報告し、main がリポジトリを入れて走らせ直した
- 見込みとの差: main の effort は low で足りた。verifier の Sonnet 5 は、今の既定の Sonnet 5.5 になった
- 次に同じ規模なら: 同じ組み方にする。verifier の依頼には、pytest の走らせ方（メモリの pi-test-env にある、リポジトリを入れるコマンド）をそのまま書く
