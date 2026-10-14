# TODO-038 reviewer の報告

対象: `git diff c19c1c8..HEAD`（ブランチ `claude/todo-038-auto-measure-impl`、2b7c25b）。コードは直していない。

実測の方法:
- 権限: scratchpad に使い捨てのリポジトリと bare リモートを作り、`claude -p -w ... --permission-mode dontAsk` に cron と同じ形の
  `--allowedTools` / `--disallowedTools` を渡して、Haiku に 1 回ずつコマンドを打たせた（Claude Code 2.1.299）。
- collected.py: `samples/screen1` を `user-a` / `user-b` として複製し、truth の `cube` だけ書き換えて
  `uv run -q --no-project --python 3.12 --with opencv-python-headless --with numpy python recognizer/collected.py <dir> --force` を走らせた。
- GitHub: `gh api repos/ytani01/bganalyzer/branches/main` などを読んだ（読むだけ）。

## 要修正

### 1. `Bash(...:*)` の書き方では、ブランチを作ることも push することもできない（PR が一度も作られない）

- 場所: tools/collected_cron.sh:25-26
- 内容: `prefix:*` は単語の区切りまでの前方一致で、`prefix` のすぐ後ろに文字が続くと一致しない。実測で
  `Bash(git switch -c claude/collected-:*)` のとき `git switch -c claude/collected-x` は **DENIED**、
  `git switch -c claude/collected- extra`（空白で区切ったもの）は ALLOWED。
  `Bash(git push -u origin claude/collected-:*)` も同じで、`git push -u origin claude/collected-x` は DENIED。
  `Bash(git add recognizer/:*)` も同じ形なので、`git add recognizer/board.py` は通らない（未確認。switch・push と同じ形からの推定）。
  通るのは `git add recognizer/ <任意のパス>` のほうになる。
- 結果、`claude -p` は推奨どおり動いても push できず、毎回 `no PR` で終わる。
- 直すときの注意（実測）: `*` の形 `Bash(git push -u origin claude/collected-*)` にすると、
  `git push -u origin claude/collected-x:main` も **ALLOWED** になった（refspec の `:main` でリモートの main へ push できる形）。
  `gh api .../branches/main` は `"protected": false` で、main は保護されていない。

### 2. 許可したコマンドで、編集した Python をそのまま実行できる（Pi の ytani の権限で何でもできる）

- 場所: tools/collected_cron.sh:23-24、tools/collected_prompt.md
- 内容: `Edit` / `Write` は無制限に許可されており、許可した `uv run ... python recognizer/evaluate.py` は
  `recognizer/` の `board.py` などを import する。写真に仕込まれた文に従った `claude -p` が `recognizer/*.py` に
  任意のコードを書いてこのコマンドを打てば、ホスト上で ytani として任意のコードが動く。ytani は docker グループ（root 相当）で、
  `gh` の認証と git の push 権限も持っているので、(b) の「recognizer/ の外を変える・main へ push する・マージする」は
  すべてできる。`--allowedTools` の絞り込みも、cron の関門も、この経路では意味を持たない。
  （構造から明らかなので実行しての確認はしていない。）
- あわせて実測で分かったこと:
  - **`Write` は作業ディレクトリと `--add-dir` の外にも書ける。** scratchpad の外側のファイル（`outside.txt`）が作られた。
    `--restricted` の help に「file tools を作業ディレクトリに閉じ込める」とあり、付けていない今は閉じ込められていない。
    元のチェックアウト（`$ROOT` 側）のファイルへの Write は、worktree の隔離で拒否された。
    ホームの `~/.local/bin` の実行ファイルの上書きや `~/.zshrc`（Claude Code の Bash ツールはプロファイルから初期化される）への
    書き込みは試していない（未確認）。
  - `git diff:*` / `git log:*` は `--output=<file>` でファイルを書ける（git の仕様。権限の判定で止まるかは未確認）。
- 関門だけで守るなら、評価コマンドを資格情報の無い場所（例: ネットワークも認証も無いコンテナ）で動かす、
  `--restricted` を使う、などが要る。どこまで守るかは管理者・ai1 の判断。

### 3. 公開の `/samples` から送った truth の文字列が `claude -p` に届く。`Read(**/*.truth.json)` の禁止も効いていない

- 場所: recognizer/collected.py:35、recognizer/evaluate.py（`cube_want['at']`・`want` を表示）、tools/collected_cron.sh:27
- 内容:
  - 実測: `--add-dir <root>/collected` と `--disallowedTools "Read(**/*.truth.json)"` で、`<root>/collected/a.truth.json` の
    Read が **ALLOWED** になり、中身（`TRUTH-SECRET-42`）が読めた。`**/` は作業ディレクトリ（worktree）からの相対で、
    その外の `collected/` には当たらないとみられる（理由は未確認、結果は実測）。
  - 実測: truth の `cube` を `{"at": "IGNORE ALL PREVIOUS INSTRUCTIONS"}` にすると、report.md に
    `- cube: truth IGNORE ALL PREVIOUS INSTRUCTIONS, read None` がそのまま出た。`save_sample`（analyzer/app.py:169-172）は
    points・bar・corners・home しか確かめず、`cube` と `dice` は何でも通る。evaluate.py の出力にも同じ文字列が出る。
  - 「`.truth.json` を直接読ませない」（TODO.md・docs/raspi.md・collected_prompt.md）は、report.md と evaluate.py の出力を通して守れていない。
    文字列に改行を入れれば report.md の見出しも作れる（未確認）。

### 4. truth の `cube` が dict でないと collected.py ごと落ち、測り直しが毎日止まる

- 場所: recognizer/collected.py:34-35
- 内容: 実測。`"cube": "x"` の組があると
  `TypeError: string indices must be integers, not 'str'`（`cube_want['at']`）で落ちる。`{"x": 1}` なら `KeyError` になる
  （未確認。同じ行から明らか）。この行は `try` の外なので、壊れた組を「error」として残す作りが効かない。
  `save_sample` はこの truth を受け付けるので、公開の POST 1 回で、その組を消すまで毎日 cron が `set -e` で止まる
  （state も report も更新されない）。evaluate.py の `__main__` も同じ所で落ちるので、`claude -p` の測り直しも止まる。
- テスト（analyzer/test_collected.py）は `misreads` を monkeypatch しているので、この行を通らない。

## 検討

### 5. 関門に「samples/ の正解数が下がらない」の確認が無い

- 場所: tools/collected_cron.sh:32-39
- 内容: CI（`uv run pytest analyzer`、docker の build）は認識の精度を測っていない（`rg -n "recognize|points correct" analyzer/test_*.py`
  で精度を見るテストは無い）。collected_prompt.md の「良くなったとみなす条件」は `claude -p` の自己申告だけで守られている。
  collected/ には誰でも誤った truth を入れられるので、その truth に合わせて認識を変え、samples/ を下げる PR も自動でマージされうる。
  関門の 3 条件は ai1 が決めたものなので、足すかどうかは判断が要る。

### 6. 関門の抜け（小さいもの）

- tools/collected_cron.sh:35 — `baseRefName` を確かめていない。`gh pr create:*` は `--base` を自由に付けられるので、main 以外への PR も
  マージされる（その後の `git pull` は main なので Pi は変わらない）。
- tools/collected_cron.sh:33 — `gh pr view --json files` が返すファイル数に上限があるか（100 件など）は未確認。上限を超える PR では外のファイルを見落とす。
- tools/collected_cron.sh:39 — 確かめた head と マージする head を結び付けていない（`gh pr merge --match-head-commit <sha>`）。
  確かめている間に push されると、確かめていないコミットがマージされる。
- 要修正 2 があるかぎり、これらを塞いでも効果は限られる。

### 7. 測り直しのあとで main でないと分かると、その回の組は二度と claude に渡らない

- 場所: tools/collected_cron.sh:13-18、recognizer/collected.py:72
- 内容: `.measured.json` を書いて削除まで済ませてから `clean_main` を見ている。止まった回の新しい組は次の日には「測った」扱いで、
  10 組たまるまで `claude -p` は動かない。
- docs/raspi.md:131「Pi の `bganalyzer` が `main` で、変更が無いときだけ動きます（作業中なら止まります）」は、測り直しと削除も
  止まるように読めるが、実際に止まるのは `claude -p` 以降だけ。

### 8. `claude -p` が失敗したとき worktree が残る

- 場所: tools/collected_cron.sh:27-29
- 内容: `|| { log "claude failed"; exit 1; }` で抜けるので 29 行目の後片付けが走らず、`.claude/worktrees/collected-*` と
  `worktree-collected-*` のブランチが残る。`.claude/worktrees/` は .gitignore に無い（`--untracked-files=no` なので clean_main には響かない）。
  成功したときも、ローカルの `claude/collected-*` ブランチは消していない。

### 9. コミット ID の比べ方

- 場所: tools/collected_cron.sh:47
- 内容: app は `head[:7]`（analyzer/app.py:124）、スクリプトは `git rev-parse --short HEAD`。git の短縮は曖昧さに応じて 8 文字以上に
  なることがあり、そのときは一致せず「did not come back」で終わる。`--short=7` なら揃う。今の長さで実害があるかは未確認。

### 10. 読み違いのある組は消えないので、公開の POST で 1000 組まで埋められる

- 場所: recognizer/collected.py:40-43、analyzer/app.py:178
- 内容: 誤った truth の組は「読み違いあり」で永久に残る。1000 組（`SAMPLE_MAX_COUNT`）に達すると「Pi に残す」は 507 を返し続け、
  毎日の測り直しも 1000 組ぶん回る。ai1 の決めた方針どおりの動きなので報告だけ。

### 11. 消す処理と保存の競合

- 場所: recognizer/collected.py:55-58
- 内容: 測ってから消すまでの間（組が多いと長い）に同じ id が送り直されると（save_sample は同じ名前で上書き）、新しい中身を
  「読み違いなし」の判定のまま消す。名前は `user-[A-Za-z0-9-]` に限られ、`glob(name + ".*")` が collected/ の外や
  ほかの組に当たることは無い（(a) の外側・別の組の削除は問題なし）。

### 12. 文書の食い違い

- docs/HANDOVER.md:22-24 — TODO-030 の説明に「PR で提案するスクリプトを作る（本番には自動で反映しない）」とあり、
  TODO-038 の自動マージ・Pi の更新と食い違う。
- recognizer/README.md:285-297「ファイル」の一覧に `collected.py` が無い。
- docs/raspi.md:131 は 7 を参照。

### 13. テストが足りない所

- analyzer/test_collected.py — `misreads` を差し替えているので、`misreads` 本体（4 の落ち方、`error:` の組が残ること）を通るテストが無い。
  同じ名前で上書きされた組が「新しい組」に数えられないことも見ていない（仕様として意図どおりかも書かれていない）。

## 好み

- CLAUDE.md:82-83 の例外は「`recognizer/` だけを変え CI が通れば」とあり、ブランチ名の条件と、「最新の main を取り込む」「Pi で確かめることを
  PI_CHECKS に足す」を省くことが書かれていない。
- `claude -p` は worktree のパスで起動するので、このプロジェクトのメモ（push してよい）は読まれず、`~/.claude/CLAUDE.md` の
  「Claude から push しない」と指示がぶつかる可能性がある（未確認。プロンプトで push を明示しているので従う見込み）。

## 問題の無かった観点

- (a) 消す範囲: 消すのは collected/ の中、`*.truth.json` の名前から作った `user-<id>.*` だけで、読み違いのある組は消えない（コードで確認）。
- report.md の数字: 「残した読み違いの無い組」= 全体 − 読み違い − 消した数、で合っている（読み違いの組は消えないため）。
- バージョン: recognizer/ に機能を足したので 0.7.0 → 0.8.0 は CLAUDE.md どおり。analyzer はテストだけなので上げないのも合っている。
- cron の環境: PATH に `~/.local/bin`（claude・uv）と `/usr/bin`（docker・gh）が入っている。cwd はスクリプトの位置から決めている。
  CI が始まる前に `gh pr checks` が空を返す件は 36 行目の待ちで扱えている。
- `-w`・`--max-budget-usd`・`--permission-mode dontAsk` は `claude --help`（2.1.299）にある。

## 作り込みすぎ

- recognizer/collected.py:L40: delete: `to_delete` の `keep=KEEP_RIGHT` の既定値。呼ぶ側（L55）が必ず渡すので使われない。`def to_delete(results, keep)`。
- tools/collected_cron.sh:L36-37: shrink: 待ちのループの後で同じ `gh pr checks | grep -q pytest` をもう一度打っている。ループの判定を変数に残せば 1 回で済む。

net: -2 lines possible.
