# TODO-120 の実装の依頼（implementer、2 回目）

## 目的

試作の `recognizer/side.py`（`implementer-report.md`）を**今の手法のまま**アプリに出す。手法の改善はしない（写真を集めてから別に行う。ユーザーが決めた）。

## やること

1. **recognizer**: `side.py` をアプリから使える形に整える
   - 四隅: `find_corners_side(img, side, progress=None, fixed=None, crop=None)` を `corners.find_corners` と同じ返し方・途中経過（progress の段階）で。
     `fixed`・`crop` は、横からの手法で自然に扱える範囲でよい（扱えないなら無視して、その旨をコメントと報告に書く）
   - 読み取り: `board.recognize` に横からの読み取りを足すか、`side.py` に同じ返し方の関数を作るかは任せる。ダイス・キューブ・バー・上がりは今の読み取りの部品をそのまま使ってよい。
     返す形（info の geometry など、アプリが描くもの）は普通のモードと同じにする
   - **普通のモードの結果を変えない**（`side` を渡さないときは今までどおり）
   - recognizer の版を上げる（機能の追加: 0.23.x → 0.24.0）。`recognizer/README.md` に横からのモードの節（向きの決め方、手法の要点、6 枚の当たり具合、苦手なもの）
2. **analyzer**: API の四隅の検出（`/corners` まわり）と解析に `side`（`right` / `left`、無ければ普通）を足す。`analyzer/README.md` の API の説明も
3. **PWA**: 四隅の画面に「横から撮った」の切り替えを置く。押してオンにしたときだけ「手前の人から見て右から／左から」を聞き、端末（localStorage）に覚えておく。次からは聞かない（左右を選び直す手段は残す）。
   オンにすると、そのモードで四隅を検出し直す。解析にも `side` を渡す。モードの状態は端末に覚えておき、次の写真もそのモードで始める。
   analyzer の版を上げる（`analyzer/app.py` の `__version__` と `analyzer/static/app.js` の `APP_VERSION`。0.67.x → 0.68.0）
4. **テスト**: 横からのモードの四隅と読み取りが、サンプル 1 枚で動くこと（`samples/` に横からの写真が無いので、`samples/photo5.jpg` を回して撮ったままの向きにしたもので試すのがよい。`archives/agents/TODO-120/raw.py` と同じ回し方）。
   API が `side` を受けて渡すこと。PWA の切り替えのテストは、今の `analyzer/test_*.py` の PWA のテストのやり方に合わせる。テストは「壊すと落ちる」ものにする
5. 文書: `README.md` の使い方、`docs/corners.md` に横からのモードの短い節（図は要らない）

## 決まっていること

TODO.md の TODO-120 の節。向き: 右から撮った写真は写真の右上が TL、右下が TR、左下が BR、左上が BL。左から撮った写真は左下が TL、左上が TR、右上が BR、右下が BL。

## やらないこと

- 手法の改善、6 枚以外での精度の測定、テスト全体を手元で流すこと（`uv run pytest analyzer/test_<名前>.py` で 1 ファイルずつ）
- コミット（main が行う）
- `rg` にはパスを必ず渡す。重いコマンドは `timeout` と `< /dev/null`

## 報告

`archives/agents/TODO-120/implementer-report-2.md` に、変えたファイル、API と PWA の変更点、テストの結果（流したファイルと結果）、普通のモードを変えていない根拠、残る懸念。
返事は「終わったか・報告ファイルのパス・判断が要る点」だけ。
