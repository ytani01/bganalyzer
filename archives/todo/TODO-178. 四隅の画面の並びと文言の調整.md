# TODO-178. 四隅の画面の並びと文言の調整

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet / medium）+ verifier（Haiku / medium）。並びと文言だけで挙動は変わらないのでレビュー担当は付けない（TODO-177 と同じ） |
| 実施 | Opus 5.5 / effort 未確認 | implementer（Sonnet 5.5）+ verifier（Haiku 5.5） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|--------|--------|----------------|------------|------|
| implementer + main | Opus 5.5 | 未確認 | 12 | 1,570 | 31,729 | 362,136 | 53% |
| implementer + main | Sonnet 5.5 | 未確認 | 18 | 3,198 | 32,968 | 312,665 | 47% |
| 合計 |  |  | 30 | 4,768 | 64,697 | 674,801 | 計 744,296 |

- `token-usage.py` は担当ごとに分けられず、このセッション（implementer の分）だけがモデル別の 2 行で出た。verifier と main の分はこの集計に入っていない
- effort は、この回に担当を起動した記録から確かめられなかったので「未確認」と書く

## きっかけ

四隅の画面（`analyzer/static/index.html` の `#corners`）について、2026-10-20 にユーザーが頼んだ 4 点（チェックボックスの行を写真のすぐ下へ、Anthropic に送る注意書きを削除、「画像を編集」を回転ボタンの左端へ、「やり直す」を「四隅をクリア」へ）。

## やったこと

- `analyzer/static/index.html`: チェックボックスの行（四隅を固定する・横から撮った）と `#side-from-row` を新しい `#corner-opts` に包み、写真と `#turn-tools` の間へ移した。`#edit-start` を `#turn-tools` の左端に。`#corner-reset` の文言を「四隅をクリア」に。`#claude-note` を削除
- `analyzer/static/app.js`: `#claude-note` の出し入れを消した。画像の編集中は `#corner-tools` と一緒に `#corner-opts` も隠す（チェックボックスを `#corner-tools` の外へ出したため）
- analyzer を 0.94.3 に上げた（`analyzer/app.py`、`app.js` の `APP_VERSION`）。`analyzer/README.md` の並びと文言を合わせた

## 確かめたこと

- CI の pytest・ruff が通った。`test_side.py`・`test_pwa.py`・`test_photo_view.py` と ruff を手元でも流した
- verifier（`archives/agents/TODO-178/verifier-report.md`）が 390×844 で `getBoundingClientRect` を測り、6 項目すべて一致（写真 < 行 < 回転の順、横から撮ったをオンにすると `#side-from-row` が行の下に出る、`#claude-note` が DOM に無い、`#edit-start` が先頭、文言、版、画像の編集中は `#corner-opts` が隠れ「やめる」で戻る）
- ローカル（2026-10-20、`git pull` と `systemctl --user restart bganalyzer` のあと、Playwright で 390×844）: `/version` が analyzer 0.94.3、ヘッダーが `a0.94.3 · r0.29.3 · 081c914`。縦の位置が写真 127 < `#corner-opts` 404 < `#turn-tools` 456 < `#corner-tools` 508、`#claude-note` なし、`#turn-tools` の先頭が `edit-start`、`#corner-reset` が「四隅をクリア」

## 確かめていないこと

- 画像の編集の「確定」のあとの挙動（「やめる」で戻ることだけ確認）
- 横から撮ったをオンにしたときの初回の質問（端末に覚える仕組み）

## 分担の振り返り

- implementer: 4 点と版上げ、README の追従を実装。チェックボックスを `#corner-tools` の外へ出すと編集中も残ることに気づき、`#corner-opts` を隠す 1 行を足した。ここは依頼に無かった判断で、報告に書いて main に渡した
- verifier: 6 項目を実測で一致と確かめた。直しは出ず、確認は 1 周で済んだ
- 見込みと食い違った点: レビュー担当は付けない見込みで、実際も付けなかった。食い違いなし
- 次に同じ規模（並びと文言）をやるなら、同じ組（implementer + verifier）でよい。依頼には、**要素を親の外へ移すときは、親を隠す処理（編集中など）に付いていくか**を、最初から書いておくと implementer の判断を待たずに済む
