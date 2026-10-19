# TODO-147 レビュー（reviewer）

対象: `git diff 1aa69e8 1e0da59`（recognizer/check_accuracy.py、recognizer/import_collected.py、analyzer/test_collected.py）

## 要修正

なし

## 検討

### 1. recognizer/import_collected.py:180 / `text=True` で、子の出力が UTF-8 として壊れていると CalledProcessError が UnicodeDecodeError に置き換わる

- 何が問題か: `text=True` は `communicate()` の中で `errors="strict"` でデコードする。子が SIGTERM/SIGKILL で止められて
  マルチバイト文字の途中で切れた stderr を返すと、`subprocess.run` が `UnicodeDecodeError` を投げ、`CalledProcessError` と
  stderr の末尾が両方とも失われる（import.log には `failed: UnicodeDecodeError(...)` だけが残る）。成功したときでも stdout が壊れていれば
  取り込みが落ちる（前の bytes のままなら落ちなかった）。
- 根拠（実測、Python 3.12.15）: `subprocess.run([python, "-c", "...sys.stderr.buffer.write(b'ok\\n\\xe3\\x81'); sys.exit(1)"], capture_output=True, text=True)`
  で `UnicodeDecodeError: 'utf-8' codec can't decode bytes in position 3-4: unexpected end of data`。
- 実害は未確認: check_accuracy.py の print は ASCII だけ（110〜127 行）で、worktree のパスも ASCII。非 ASCII が出るのは
  ライブラリの警告やトレースバックに日本語が混じったときに限られる。`errors="replace"` を足せば消える。
- git の lambda（159 行）はもとから `text=True` なので、この差分で新しく入った挙動ではあるが、同じ性質のものはもとからある。

### 2. 範囲 / 親が止められたときに測定の子（ProcessPoolExecutor のワーカー）が残る件は手当てされていない

- TODO-147 の本文に「親が止められると、測定の子プロセスが残ってメモリを使い続けた」とあるが、チェックリストの項目には無い。
  `subprocess.run` は SystemExit（SIGTERM のハンドラ、165 行）を受けると `check_accuracy.py` を `kill()` するが、その先のワーカーまでは止めない。
- `--jobs=2` で残るのは最大 2 つ（約 0.8 GiB）に減るので実害は小さくなる見込み。実害は未確認（残るかどうかは実測していない）。
  見送るなら、その理由を TODO-147 に一言残すとよい。

### 3. テスト / `--jobs=2` を渡していることと `text=True` は、テストで守られていない

- 新しいテスト（analyzer/test_collected.py:217）は `_run` を差し替えて `run()` のログだけを見るので、
  import_collected.py:179 から `--jobs=2` を消しても、`text=True` を消しても（実際の stderr が bytes になり、ログが `b'...'` の行になる）落ちない。
  check_accuracy.py:104 の `--jobs=` の解釈もテストが無い。
- 一方、stderr の末尾を残す部分は強い: 30 行から末尾 20 行を取ることを `line 29` あり・`line 10` あり・`line 9\n` なしで見ており、
  ログを出さない・`[-21:]`・`[-19:]` のどれに変えても落ちる（読んで確かめた。差し替えての実行はしていない）。テストは手元で 1 passed。
- 本番の効き目はローカルの `--force` 1 回で見る計画なので、足すかは判断次第。

## 好みの範囲

- 1e0da59 のコミットメッセージの末尾が `（TODO-147)` で、閉じ括弧が半角（ほかのコミットは全角）。

## 問題の無い点

- `--jobs` を付けないとき: `next(..., None)` で `measure_all(None)` → `ProcessPoolExecutor(None)` で CPU 数だけ並行（実測で None を確認）。CI（accuracy.yml）・手動は今のまま。
- `--jobs=0` / 非数は `ValueError` で落ちるが、渡すのは import_collected.py の固定の `2` だけなので問題ない。`--jobs 2`（空白区切り）は黙って無視されるが、同上。
- `text=True` で既存の挙動は変わらない: 戻り値の stdout/stderr を使うのは今回足した `run()` のログだけ。
- `except BaseException` で stderr が無い例外: SystemExit・KeyboardInterrupt・`stderr=None` の CalledProcessError（-15）でも `failed: ...` 1 行だけになり壊れない（実測）。bytes の stderr（TimeoutExpired など）でも落ちず `b'...'` の行になるだけ（実測。この経路で check=True のものは無い）。
- `e!r` は CalledProcessError の stderr を含まないので、ログに二重には出ない。
- 版: check_accuracy.py は測る道具、import_collected.py の変更は読み取りの結果を変えないので recognizer の版を上げないのは CLAUDE.md・TODO-142/146 の前例どおり。
- 文書: check_accuracy.py の docstring に `--jobs=N` を足してある。docs/raspi.md の `import.log` の記述（219 行）と食い違いは無い。
- コメントは「なぜ」（開発機のメモリ、サービスの再起動）を書いている。範囲外の変更は無い。

## 作り込みすぎ

作り込みすぎ: なし（`--jobs=` は既存の `"--update" in sys.argv` と同じ流儀の 1 行、`measure_all(jobs)` は既にあった引数を使っている）。
