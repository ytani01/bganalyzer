# TODO-114 ローカル確認

結果: **マージされなかった**。PR #348 は checks failed でオープンのまま。

- 取り込みの実行（1 回のみ）: 終了コード 0。出力は `measured` のみ。
- import.log 末尾 2 行:
  - `2026-10-17 20:14 https://github.com/ytani01/bganalyzer/pull/348: collected-xuz0xb collected-ydz20m collected-dplmij collected-5vutmr collected-wkky1g collected-gka56t collected-we6czo collected-t4ngdy collected-6aj3py collected-m5ekpe`
  - `2026-10-17 20:17 https://github.com/ytani01/bganalyzer/pull/348: checks failed, left open`
- worktree は main のみ。`claude/collected-import-*` のローカルブランチなし（後始末済み）。リモートのブランチ: claude/collected-import-20261017-201245（OPEN）。
- PR のチェック: accuracy は pass。**test の pytest は fail**。

## 食い違い 1: test が落ちた（実害は未確認）
`gh run view 39027970624 --log-failed` より:

    analyzer/test_api.py:147: AssertionError
    E  AssertionError: collected-gka56t.truth.json
    E  assert (46.65400518585282 > 40) == ('collected-gka56t.truth.json' in {'collected-4b88u3.truth.json', ... 'photo5.truth.json', ...})
    FAILED analyzer/test_api.py::test_steep_photo_is_flagged
    ============ 1 failed, 105 passed, 3 warnings in 121.99s ============

gka56t は傾き 46.65° で OBLIQUE_WARN_DEG(40) を超えるが、テストの steep 集合に無い。
取り込みが steep 集合を更新しないため、斜めの写真が入ると落ちると思われる（推定。切り分けはしていない）。

## 食い違い 2: .png が 1 枚入った（実害は未確認）
`samples/collected-6aj3py.png`（アプリの画面）。依頼の「jpg と truth.json」に png は無い。
import_collected.py は suffix に .jpg/.png の両方を扱う実装。意図どおりかは判断できない。

## 合っていたもの
- PR の差分の一覧: samples/collected-*（10 組、jpg 9 + png 1 と truth.json）・recognizer/accuracy_baseline.json・recognizer/README.md のみ（`gh pr view --json files`。PR は未マージなので `gh pr diff` ではなくこれで確認）。
- 10 枚を Read で目視: 盤の外は黒く塗りつぶされ、盤の欠けはなし。
