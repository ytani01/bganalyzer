# TODO-091 確認報告

## 検証の結果

| 項目 | 結果 |
|---|---|
| ローカル `/version`（`curl --max-time 5 http://127.0.0.1:8000/version`、終了コード 0） | 一致。`analyzer` は `0.54.1` |
| PWA のヘッダー `#hdr-version`（Playwright、`/usr/bin/chromium`） | 一致。下の文字列で始まる |
| `git diff` の範囲 | 一致。下の 3 ファイル、5 行追加・5 行削除 |

ポートは `systemctl --user cat bganalyzer` の `ExecStart` で `--port 8000` を確かめた。override.conf は `BG_CLAUDE` だけを足す。

## 測った値

`/version` の応答（そのまま）:

```
{"analyzer":"0.54.1","recognizer":"0.23.0","commit":"162f3d3","samples":true,"claude":true}
```

`#hdr-version` の読み出し（`textContent` が `·` を含むまで待ってから読んだ。`·` は版の取得後にだけ入る）:

```
{"text": "a0.54.1 · r0.23.0 · 162f3d3", "cls": "hdr-version", "classes": ["hdr-version"]}
```

- `a0.54.1 · r` で始まる: 一致（先頭は `a0.54.1 · r0.23.0 · 162f3d3`）
- `v0.54` を含まない: 一致
- `old` クラスが付いていない: 一致（classes は `hdr-version` だけ）

## git diff

`git status --short`: `M TODO.md`、`M analyzer/app.py`、`M analyzer/static/app.js`。指示にないファイルは変わっていない。

- `TODO.md`: 1 行（`- [ ] …` を `- [x] …` に）。指示どおり
- `analyzer/app.py`: 1 行（`__version__` を `0.54.0` → `0.54.1`）。指示どおり
- `analyzer/static/app.js`: 3 組（`APP_VERSION` を `0.54.1` に。`#hdr-version` の 2 か所を `a${APP_VERSION}` に）。指示どおり

`git diff --stat`: 3 files changed, 5 insertions(+), 5 deletions(-)。

## 補足・確かめられなかったこと

- 手順の既定の Playwright のブラウザ（`~/.cache/ms-playwright`）が無かったため、`tools/*.py` と同じ `/usr/bin/chromium` を指定して起動した。
- 読んだのは開いた直後の 1 回。他の画面や操作は見ていない。
- 「ローカルの bganalyzer.service は再起動済み」の確認は、`/version` が `0.54.1` を返すことで済ませた。プロセスの起動時刻は見ていない。
- 判断が要る点: なし。
