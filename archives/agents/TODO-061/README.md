# TODO-061 の分担

- 途中経過の表示を 0.5 秒にする件: main が実装し、verifier（Sonnet 5.5）が確認した（`verifier-stage-ms-report.md`）。数値の変更だけで分岐は変わらないので reviewer は入れなかった
- 四隅の候補の点数の件: 案を試して測る作業が長く、corners.py の判断も要るので implementer（Opus 5.5）に任せた（`implementer-report.md`）。
  1 回目は全件の測り直しから始めたため、ユーザーが止めて依頼し直した。採れる案が無かったので reviewer と verifier は回していない
- `measure_corners.py` は、四隅の候補から読み取った正解数を測るスクリプト。`full-*.json` はその全件の結果、`corners-trial.diff` は最後に試した corners.py の差分
