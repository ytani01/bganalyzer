# TODO-164 verifier 報告

対象: worktree impl-164（claude/cube-navy、f6b027b）。8011 で起動して Playwright（Chromium、412x915）で読み出した。
live_view（9222）は開いていなかったので、`/usr/bin/chromium` を直接起動した。スクリプトは `archives/agents/TODO-164/verify.py`。
盤面は `samples/screen-app-grey-shot` を `pi_ui_check.read_photo` で読んでから、`BgApp.update({cube})` でキューブを替えた。

## 読み出した値（計算後の style）

| 状態 | rect fill | rect stroke | 数字の fill | 矢印 (g.way) | サイコロ | 期待どおりか |
|---|---|---|---|---|---|---|
| 1 真ん中（"64"） | rgb(31,63,122) | rgb(255,255,255) | `.cube-num` rgb(255,255,255) | 1 | 2 | 合っている |
| 2 黒が持つ（"4"、奥側の置き場） | 同上 | 同上 | `.cube-num` rgb(255,255,255) | 1 | 2 | 合っている |
| 3 ダブル申し出中（白へ 2、offered: true） | 同上 | 同上 | `.cube-num` rgb(255,255,255) | **0** | **0** | 合っている |
| 4（おまけ）Crawford（5 点マッチ 4-2） | 同上 | 同上 | `.cube-crawford` 2 本とも rgb(255,255,255) | 1 | 2 | 合っている |

## スクリーンショットの目視（`~/tmp/playwright-mcp/`）

- `verify-164-1-centre.png`、`verify-164-2-held.png`、`verify-164-3-offered.png`、`verify-164-4-crawford.png`
- キューブは 4 枚とも欠けずに紺地・白縁・白字で見える。余計なものは映っていない。
- 状態 3 は矢印・サイコロが無く、キューブは盤の中（白の手番側の場）に出ている。

## 食い違い

なし。

## 補足（食い違いではない）

- 状態 3 は、onRoll が自動で black になり、盤の向きが変わって見える（番号 1〜24 の並びが反転）。TODO-164 の変更とは別で、`app.js` の既存の動き（キューブが手番を決める）と見ている。実害は未確認。
- 確かめていないこと: 実機のスマホの見え方、デザインの良し悪し（頼まれていない）。
