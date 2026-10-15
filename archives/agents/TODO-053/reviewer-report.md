# TODO-053 レビュー（reviewer）

対象: 作業ツリーの `git diff`（ブランチ claude/todo-053-cube-centre）。実測はしていない（verifier の担当）。

要修正: なし

## 検討

### 1. 正解が white/black で読みが centre のとき、WRONG でなく not found になる
- `recognizer/evaluate.py:56`
- 読みの centre も None にするので、正解が white/black のとき、読みが centre なら `cube is None` になり、
  `evaluate.py:70`・`check_accuracy.py:41` では `WRONG` でなく `not found` になる（変える前は `WRONG`）。
  キューブの持ち主を外して真ん中と読むのは解析の結果が変わる読み違いなので、本来は `WRONG` に当たる。
- 影響（コードを読んで確かめた）: `check_accuracy.py` の RANK は `WRONG < not found < ok`。いまの基準で正解が
  white/black の screen2・tv-vegas-open は `ok` なので、centre と読むようになっても ok → not found で落ちる。
  見逃すのは「not found のサンプルが centre と読むようになる」ときだけで、`samples/` には該当が無い
  （external の galaxy-cube2-near は正解 white・読み None だが、CI では測らない）。実害は未確認。境界線上なので報告だけ。

### 2. 表示の「read None, truth None」で、真ん中に見つかったのか見つからなかったのかが分からなくなる
- `recognizer/evaluate.py:56`（表示は `:73`）
- run() の戻り値そのものを書き換えているので、正解 centre・読み centre は「cube ok (read None, truth None)」と出る
  （変える前は「read centre, truth centre」）。正解なし・読み centre も同じ表示になる。
- `recognizer/README.md:381-393` の「当たり具合」の表は「centre（当たり）」と「見つからない」を分けて書いており、
  次に測り直すとき evaluate.py の出力からはこの区別が取れない。比べる所だけで centre を None にそろえ、表示は元の値を
  出す、といった形にするかは管理者の判断。

### 3. evaluate.py だけの変更で recognizer の版を上げている
- `recognizer/board.py:47`（0.20.1 → 0.20.2）、`recognizer/cpu_reference.json:4`
- CLAUDE.md の「バージョン」は「そのディレクトリのコードを変える PR で、その方を上げる」なので、字面では沿っている。
  一方 `board.py:45` のコメントは版の対象を「board.py, position.py, corners.py and dice.py」とし、読み取り以外の
  道具だけを変えた先例では上げていない（`69605a9` は check_accuracy.py だけで据え置き、`5717be9` も据え置き）。
  読み取りは変わらないのに `/version` と PWA の表示が変わり、cpu_reference.json の meta の書き直しも要る
  （`trace_cpu.py:98` が版の違いを見るため。差分は meta の 1 行だけで、値は変わっていない）。
  どちらでも規約違反ではない。境界線上なので報告だけ。

### 4. commons-rollup-oblique の正解 centre と README の記述が合っていない（この差分の前から）
- `samples/commons-rollup-oblique.truth.json`（`"cube": {"at": "centre"}`）と `recognizer/README.md:389`
  （「右のフィールドに立てたキューブ」）
- フィールドの中なら、読めれば `field` → on_roll の相手（white、`evaluate.py:51-54`）になり、正解の centre とは合わない。
  今回の変更で「見つからない」が ok に数えられ、README:81 に「ok になった」と書かれたので目立つようになった。
  どちらが正しいか（写真のキューブの位置）は確かめていない。未確認。

## 問題なしの観点
- 比較の意味: 読み centre・正解なしが ok になる、正解 centre・読みなしが ok になる。field → white/black の変換（`:51-54`）の後で
  そろえるので、field が centre に化けることはない。value は前の行で落としているので比べない。いずれも意図どおり。
- 呼び出し元: `rg -n 'evaluate.run|cube_want' recognizer` の 3 か所（evaluate.py の __main__、check_accuracy.py:35、
  collected.py:55）とも `cube == cube_want` と `cube is None` しか見ておらず、centre を前提にした所は無い。
  `collected.py:44` の `valid()` は正解の centre を受け付けたままでよい（run() の中でそろえる）。
- accuracy_baseline.json: 変わったのは commons-lg-cube-dice と commons-rollup-oblique の cube（not found → ok）だけで、
  どちらも正解 centre。README:81 の記述と合う。
- recognizer/README.md:379 の追記: 「正解が centre なら CI では ok」は、表の「見つからない」4 件のうち正解 white の
  galaxy-cube2-near を正しく外している。README:378 の「なければキューブなし」も今の挙動と合う。
- 精度の確認の手順（baseline と cpu_reference を同じ PR で更新、README の「精度」に版ごとの行を足す）: 沿っている。
- コメント（`:55`）: なぜそろえるかを書いている。
- 範囲: TODO.md のチェック 2 つと上の変更だけ。指示に無い変更は無い。
- テスト: evaluate.py には単体テストが無く、CI の accuracy が比較の結果を見ている。1 行の変更で、足すほどではない。
- 文書: `rg -n 'not found|見つからない'` で docs/・README.md・analyzer/README.md・CLAUDE.md に古くなる記述は無い。

## 作り込みすぎ
作り込みすぎ: なし（1 行の変更。Lean already. Ship.）
