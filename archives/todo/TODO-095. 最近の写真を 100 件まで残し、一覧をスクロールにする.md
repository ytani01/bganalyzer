# TODO-095. 最近の写真を 100 件まで残し、一覧をスクロールにする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（実装）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| 合計 |  |  |  |  |  |  | TODO-096 に含む |

- TODO-096 と同じブランチ・同じ PR（#293）で一緒に進めたので、トークンは分けられない。TODO-096 のファイルの表に両方の分をまとめて書いた

## きっかけ

ユーザーの依頼（2026-10-17）。最近の写真（端末の IndexedDB）が 10 件までしか残らなかった。

## やったこと

- `analyzer/static/history.js` の `KEEP` を 10 → 100
- `analyzer/static/style.css` の `.history-list` に `max-height: calc(10 * 78px + 9 * 8px); overflow-y: auto;`（1 行 = 64px のサムネイル + 上下 6px + 枠 2px）
- `analyzer/test_pwa.py` の `KEEP` と既定の削除の確かめを 100 件に、`analyzer/README.md` の「最近の 10 枚」を 100 枚に
- analyzer 0.59.0（TODO-096 と一緒に上げた）

## 確かめたこと

- verifier（`archives/agents/TODO-096/verifier-report.md`）: 390x844 で 12 件を入れ、`#history-list` の clientHeight 852px、scrollHeight 1024px、scrollTop は最大 172px まで動く
- ローカル: 更新後の `bganalyzer.service`（0.59.0）で `PhotoHistory.KEEP` が 100、`#history-list` の max-height 852px・overflow-y auto

## 分担の振り返り

- verifier は高さとスクロールを実測して一致を返した。食い違いは見つけなかった。仮の JPEG で試したので、実写真の見た目は見ていない
- 見込みどおり
- 次も、CSS と定数だけの変更なら main の実装 + verifier 1 回の測定で足りる。TODO-096 と同じ verifier に一緒に頼んだので、立ち上げ 1 回分を省けた。同じ PR に入る小さな項目はこう束ねる
