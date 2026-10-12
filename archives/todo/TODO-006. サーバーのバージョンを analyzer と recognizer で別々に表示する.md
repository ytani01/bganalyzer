# TODO-006. サーバーのバージョンを analyzer と recognizer で別々に表示する

**担当:** ai1

analyzer と recognizer にそれぞれバージョン番号を持たせ、API（`/version`）と PWA の画面に両方を出す。
Raspberry Pi で動いている版を確かめられるよう、git のコミット ID も添える。

**2026-10-13 に完了:** `GET /version` が analyzer・recognizer のバージョンとコミット ID を返し、PWA の画面の下に出る。
バージョンの上げ方は CLAUDE.md の「バージョン」。
