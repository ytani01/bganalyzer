# TODO-103 確認報告（verifier）

対象: コミット 7e3284b（ブランチ claude/todo-103-unlimited）。「マネーゲーム」を「アンリミテッド」に置き換えた変更。コードは変更していない。

## 手順 1: 残りの「マネーゲーム」

`rg -n "マネーゲーム" -g '!archives/**'`（終了コード 0）

```
TODO.md:103:## TODO-103. 「マネーゲーム」を「アンリミテッド」に代える
TODO.md:109:「マネーゲーム」という語を、すべて「アンリミテッド」に代える（2026-10-17 ユーザーが決めた）。対象は
TODO.md:110:`rg -n "マネーゲーム" -g '!archives/**'` で出る箇所（画面の文言の `analyzer/static/app.js`・`result.js`、テストの `analyzer/test_pwa.py`、
```

判定: 一致。出たのは TODO-103 の節（103〜110 行）だけ。食い違いなし。

## 手順 2: コミット 7e3284b の差分

変更ファイルは 7 つ、14 行追加・14 行削除。

| ファイル | 内容 | 判定 |
|---|---|---|
| TODO.md | TODO-025 の「決めたこと」行の置き換え。TODO-103 の置き換え項目を `[x]` に | 一致（TODO-025 の行は、TODO-103 の対象に「この TODO.md」と書かれている範囲） |
| analyzer/README.md | 置き換え 8 行（「マネーゲーム」→「アンリミテッド」） | 一致 |
| analyzer/app.py | `__version__` 0.62.0 → 0.62.1 | 一致 |
| analyzer/static/app.js | `APP_VERSION` 0.62.0 → 0.62.1、選択肢の文言 | 一致（版は app.py と同じ 0.62.1） |
| analyzer/static/result.js | 結果の注記の文言 | 一致 |
| analyzer/test_pwa.py | テストの期待文字列 | 一致 |
| docs/HANDOVER.md | キューブ判断の説明 1 行 | 一致 |

置き換え以外の変更は見つからなかった。語句を入れ替えただけで、他の文は変わっていない。

文の読みやすさ（食い違いではなく、読み手の判断）:
- `analyzer/README.md` の「マッチでは、gnubg がマッチの勝率から出すアンリミテッドと同じ尺度のエクイティ」は、日本語として通る。「マネーゲーム」の位置に「アンリミテッド」が入っているだけ。
- `match_length` の説明の「0（既定）はアンリミテッド」も通る。

## 手順 3: テストの実行

`uv run pytest analyzer/test_pwa.py -k test_match_in_the_result_words`（終了コード 0）

```
collected 25 items / 24 deselected / 1 selected
analyzer/test_pwa.py .                                                   [100%]
================= 1 passed, 24 deselected, 1 warning in 0.58s ==================
```

判定: 通った。`warning` は httpx の非推奨表示で、今回の変更とは関係ない。

## 確かめられなかったこと

- 手順 3 は `test_match_in_the_result_words` 1 件だけ。`analyzer/static/app.js` の選択肢と `analyzer/static/result.js` の注記（`cubeNote` 以外の文言）は、このテストが見ていない範囲もある。画面の表示は確かめていない（TODO-103 のローカル確認の項目の範囲）。
- テストを壊して落ちるかは見ていない（指示は 3 手順だけ）。
- 版の上げ方（analyzer のみを上げる）が CLAUDE.md の規則に合うかは、差分の見た目では確かめたが、規則そのものとの照合は行っていない。上げるのは `analyzer/app.py` と `analyzer/static/app.js` の 2 か所で、両方 0.62.1。

## 判断の要る点

なし。食い違いは見つからなかった。
