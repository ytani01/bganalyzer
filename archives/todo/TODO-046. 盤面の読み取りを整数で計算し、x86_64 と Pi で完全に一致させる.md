## TODO-046. 盤面の読み取りを整数で計算し、x86_64 と Pi で完全に一致させる

- **担当:** ai1（2026-10-15、このスレッドで実装）
- **見込み:** main Opus 5.5 / effort high + reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium。CI と Pi で全サンプルを比べる）

**問題:** 読み取り（`board.py`・`dice.py`・`cube.py`）が x86_64 と Pi で違う結果を出す（tv-vegas-open は 22 と 23）。
そのため精度の基準は x86_64 でしか更新できない。四隅の推定は TODO-028 で揃えた。

決めたこと（2026-10-14、ai1）: 整数にして精度が少し下がっても、**x86_64 と Pi の一致を優先する**。種や値を選んで精度を合わせることはしない（TODO-028 と同じ）。

- [x] どの処理で分かれるかを測る（`recognize(trace=...)` と `trace_cpu.py`、GitHub Actions の x86_64 と arm64 で比べた。最初の段（四隅からの射影変換）から分かれ、24 枚中 4 枚で読みが違った）
- [x] 分かれる処理を整数の計算に置き換える（`exact.py`。写し直しは `cv2.remap` の整数の補間、ぼかしと勾配は 8・16 ビット、射影変換・直線・k-means は CPU で変わらない計算。Hough の円は 8 ビットの入力が同じなら同じだった）
- [x] 全サンプルの読みが x86_64 と arm64 で完全に一致することを CI で確かめる（`cpu-match`。途中の値まで `cpu_reference.json` と同じ。Pi は PI-028）
- [x] Pi でも基準を更新できるようにし、CLAUDE.md・`check_accuracy.py`・recognizer/README.md の説明を直す。recognizer の版を上げる（0.14.0。SIMD を揃える `cpu_caps` と 1 ポイントの許容はやめた）

**2026-10-15 に完了:** GitHub Actions の x86_64 と arm64 で、全 24 サンプルの読み取りが途中の値まで一致した。AVX-512 のあるなしでも同じ。
精度の基準は 529 → 518（一致を優先する決めごとどおり。内訳は recognizer/README.md の「CPU で変わらない読み取り」）。
読み取りは 1 枚あたり 10〜20% 遅くなった。Pi で確かめること: PI-028。

## 分担の振り返り

- 見込みどおり大きな作業だったが、reviewer と verifier の代わりに、GitHub Actions の arm64 の実行機と、このクラウドで SIMD を SSE2 までに落とした実行を「別の CPU」として使い、
  途中の値のハッシュで分かれる段を 1 つずつ潰した。Pi そのものでの確認は PI-028 に残した
