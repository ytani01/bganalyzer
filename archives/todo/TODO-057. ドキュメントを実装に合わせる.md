# TODO-057. ドキュメントを実装に合わせる

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort 記載なし | main のみ（文書だけの変更で、確かめるのは書式と実装との一致） |
| 実施 | Opus 5.5 / effort 記載なし | main のみ |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 記載なし | 12 | 2,690 | 5,666 | 796,935 | 100% |
| 合計 |  |  | 12 | 2,690 | 5,666 | 796,935 | 計 805,303 |

- 集計は立てたコミット（a025346）から決着の直前まで。立てる前の突き合わせ（ドキュメントとコードを読んだ分）は入っていない

## きっかけ

2026-10-15 にドキュメントと実装を突き合わせたところ、記述の古さや言葉足らずが見つかった。コードの不具合は無かった。

## やったこと

- `analyzer/README.md`: 段階を見せる長さを「`fit` は 1 回 500 ミリ秒、ほかは 1000 ミリ秒」に（`scan.js` の `STAGE_MS`）。
  傾きの警告を「40° を超えて」に（`board.py` は `tilt_deg > OBLIQUE_WARN_DEG`）。`/analyze-photo` の応答の一覧に `cube_read` を足した
- `README.md`: モジュール構成の図の `app.py` に `/find-corners`・`/share-target` を足した（`/samples` は `samples.py` の箱に既にある）。
  写真を保存しない記述に「Pi に残す」の例外を足した
- `docs/raspi.md`: 写真を保存しない記述に「Pi に残す」の例外を足した
- `docs/PI_CHECKS.md`: 決着済みの PI-040 についての一文を消した
- `docs/HANDOVER.md`: 「今の状態」の版を analyzer 0.39.0 / recognizer 0.21.2 に、決着済みの TODO-028・TODO-032 の記述を直した
- `recognizer/README.md`: 「ファイル」に `cube_value.py`・`home_prior.py`・`synth_cube.py`・`check_corners.py`・`tune.py` を足した
  （`make_cube_glyphs.py` は `cube_value.py` の行で触れた）

## 確かめたこと

- 直した値をコードと照らした: `STAGE_MS.fit = 500`、`OBLIQUE_WARN_DEG = 40` と `>`、`app.py` の応答に `cube_read`、
  `@app.post` の一覧、`home_prior.py` が `home_prior.json` を、`cube_value.py` が `cube_glyphs.png` を読むこと、`samples/synth-cube-*` があること
- Pi の `/version` が analyzer 0.39.0 / recognizer 0.21.2 / 93285de を返すこと（2026-10-15）
- コードは変えていないので版は上げていない
