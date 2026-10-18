# TODO-142 レビュー（reviewer）

対象: `git diff main...HEAD -M`（280b3e2）。実行したのは `uv run pytest analyzer/test_collected.py`（9 passed）だけ。

## 要修正

1. **samples/CREDITS.md:33** / 機械的な置換で範囲の書き方が壊れた。
   `photo2〜4 はユーザーが撮った写真` が `photo-blue-red-top〜4 はユーザーが撮った写真` になっている。
   / 「〜4」が指すものが無くなり意味が通らない（main の行と見比べて確認）。
   photo-blue-red-top・photo-green-felt-top・photo-carved-brown-top のように並べる必要がある。
   photo5・photo6（photo-black-blue-oblique・photo-orange-black-oblique）が元々この行に無いのは変更前からで、今回の範囲外。

2. **analyzer/test_collected.py:112-115（test_import_skips_what_samples_has）** / 重複判定を名前から `"id"` に移したのに、
   それを確かめるテストが無い。テストは `collected-bbb.truth.json` に `{"id": "bbb"}` を書いており、ファイル名と id が同じ。
   / 読んで確認: `pick` の `added` を元の `(samples / f"collected-{sample_id(n)}.truth.json").exists()` に戻しても、
   このテストは同じ結果になり落ちない。戻ると、改名した 36 組（ファイル名に id が無い）が「まだ無い」と判定され、
   塗った写真は元の写真と sha が違うので `seen` でも弾けず、次の取り込みで同じ組が最大 10 組ずつ入り直す。
   名前と id が違うファイル（例: `collected-some-name.truth.json` に `{"id": "bbb"}`）で確かめるテストが要る。

3. **CLAUDE.md:34-38（変えないもの）** / 「写真は…外へ送ることもしない。例外は次の 2 つだけ」が、今回の変更で事実と合わなくなった。
   `BG_IMPORT` と `BG_CLAUDE` を設定した開発機では、取り込む組の塗った写真を `claude -p` に渡す（Anthropic に送られる）。
   / `recognizer/import_collected.py:87-109` の `describe`。TODO.md の TODO-142 には「同日ユーザーが決めた」とあるので、
   作りではなく文書の食い違い。docs/raspi.md:213 には書いてあるが、CLAUDE.md の例外の一覧と、
   CLAUDE.md:46-48 の import_collected の項には無い。

## 検討

4. **recognizer/import_collected.py:116-122（free）と改名の付け方** / 番号の付け方が 2 通りある。
   今回の改名では重なる組を `-1` から振った（galaxy-screen-1〜6、tan-black-side-1〜3、tv-vegas-1・2）。
   `free` は 1 つ目を番号なし、2 つ目から `-2` にする（tan-far があれば次は tan-far-2）。
   / 動作はどちらでも壊れないが、同じ盤の組の名前の付き方がそろわない。決めた結果なら `free` の docstring か docs に書いておくとよい。

5. **recognizer/import_collected.py:28・107-109（NAME）** / 末尾の番号を受け付ける。PROMPT で「No number at the end」と
   頼んでいるが、`Names given before` に `galaxy-screen-1` などを並べるので、Claude がそれを写して `galaxy-screen-1` と
   返すことがありうる。NAME はそれを通し、`free` で `galaxy-screen-1-2` になる。実害は未確認（実際の claude で試していない）。
   パスの安全性は問題なし（下の「問題なし」）。

6. **recognizer/import_collected.py:100-105** / 終わり方の扱いが `analyzer/claude_corners.py` と違う。
   `claude_corners.py:63-69` は「claude が終わっても子プロセスが stdout を持ったまま残ることがある」として
   `start_new_session=True` と `killpg` で片付けている。`describe` は `subprocess.run(timeout=120)` だけ。
   ハングはしない（`subprocess.run` は POSIX ではタイムアウト後に子を kill して `wait()` するだけで、パイプの EOF を待たない）。
   ただし孫が stdout を持っていると、答えが出ていても 120 秒待って None（`collected-<id>`）になり、孫は残る。
   `MAX = 10` なので最悪 1 回の取り込みで 20 分。`--tools ""` で孫が出るかは実害は未確認。

7. **recognizer/import_collected.py:105** / `returncode` と結果の `is_error` を見ていない。エラーの結果の文が
   小文字・ハイフンだけの 1 語（例: `none`、`error`）なら、それがそのまま名前になる。実害は未確認（実際のエラー文はたいてい大文字や空白を含み NAME で落ちる）。

8. **analyzer/test_collected.py:138-159（test_import_names_the_pair_as_claude_says）のテストの強さ**（読んで判断）
   - 落ちるもの: バッククォートの除去、`free` の番号の繰り上げ（-2 → -3）、NAME で大文字・空白・カンマの答えを弾くこと、
     名前の一覧（`blue-felt-top`）が PROMPT に入ること（偽の claude の assert が落ちると出力が無くなり、期待の名前にならない）、画像が先頭にあること。
   - 落ちないもの:
     - `free` の `or taken(name + "-1")` を消しても通る（`-1` の付いた組をテストで作っていない）。
     - NAME を `[a-z0-9./-]+` のように緩めても通る（弾く例が大文字・空白の 1 つだけで、`../x` や `a/b` の例が無い）。パス操作の安全性は NAME だけが守っているので、ここは例を足す価値がある。
     - `except` の組を狭めても通る（`BG_CLAUDE` が存在しないパス・タイムアウト・出力が JSON でない、の例が無い）。失敗時に `collected-<id>` に落ちることは「答えに名前が無い」場合しか確かめていない。
     - `.removeprefix("collected-")` を消しても通る。

9. **docs/raspi.md:215** / 「`samples/` に同じ名前か同じ写真があるもの…は除きます」の「同じ名前」が古い。
   判定は正解ファイルの `"id"` に変わった（`import_collected.py:50`）。「同じ id」などに直すとよい。

10. **TODO.md:69（範囲）と実際** / 範囲に挙げた tv-vegas-open・commons-*・external が改名されていない
    （synth-cube-* は元の写真の名前に合わせて変わった）。今の名前で特徴が分かるので据え置いたのなら、その旨を TODO の節に書いておくと、
    決着のときに範囲と結果が食い違わない。判断が要る点。

## 好みの範囲

11. **recognizer/synth_cube.py:29・31** / キーが長くなったのに続きの行の字下げが `"photo2": [` に合わせたまま。

12. **samples/*.truth.json（全体）** / 1 行の JSON の中身（`image`、collected は `id` も）を改名と同じコミットで変えたので、
    `*.truth.json` は改名ではなく削除と追加になっている（`git diff -M --name-status` で R ではなく D/A）。
    `git log --follow` で正解ファイルの履歴を辿れない。避けるなら改名だけのコミットを先に分ける。

## 作り込みすぎ

- `recognizer/import_collected.py:118-122`: shrink: `free` の while ループ。
  `return next(f"{name}-{k}" for k in itertools.count(2) if not taken(f"{name}-{k}"))` の 1 行（-3 行）。好みの範囲。
- `describe` は `analyzer/claude_corners.py` の `_message` と起動の引数をほぼ写しているが、recognizer から analyzer を import すると
  依存の向きが逆になるので、まとめないのは妥当。
- net: -3 lines possible.

## 問題なし（1 行ずつ）

- 既存の collected-* の正解 36 件すべてに `"id"` がある（依頼の `rg -L` は ripgrep では `--follow` の意味で、空でない出力になる。
  `rg --files-without-match '"id"' samples/collected-*.truth.json` で 0 件を確かめた）。id に重複なし。
- 各 collected の新しい正解の `id` は、改名前のファイル名の id と 36 件すべて一致。
- すべての `samples/*.truth.json` で `image` の値がファイル名と一致し、その画像が存在する。
- 正解の中身は `image`（collected は `id` も、synth-cube は `note` も）以外は main と同じ（4 件を見比べた）。
- `accuracy_baseline.json`: キーと samples の組が一致し、改名した組の値は main の旧名の値と同じ、改名していない組も同じ。
- 旧名の残り（依頼の `rg` と、id だけの `rg -e '\b(2aunci|…)\b'`）: TODO.md:68-69（意図して残したもの）だけ。
- synth_cube.py: `SPOTS` のキー → `synth-cube-{base}-{value}` と `note` の作り方が、ファイル名と note の値に合っている。順序も同じなので乱数の並びも変わらない。
- describe の失敗時: OSError（パスが無い・実行できない）、TimeoutExpired、JSON の壊れた行・デコードの失敗（ValueError）、
  result が無い・空の答え（LookupError）、result が文字列でない（AttributeError）は None になり `collected-<id>` に落ちる（読んで確認）。
  SIGTERM の `sys.exit` は `subprocess.run` が子を kill してから上げる。
- NAME のパスの安全性: `fullmatch` で `[a-z0-9-]` だけ、先頭がハイフンにならず、`/`・`.` を含まないので `samples/` の外へは出ない。
- `clean(t)` は `id` を拾わないので、送られた正解の `id` で上書きされない。
- 取り込みは `analyzer/samples.py:85` の子プロセスで動くので、`describe` の待ちで API は止まらない。
- バージョン: recognizer の測る道具・サンプルだけの変更で、`__version__` を上げていないのは CLAUDE.md の「バージョン」どおり。
