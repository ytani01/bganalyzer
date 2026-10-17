# TODO-124. 四隅の検出のアニメーションの間隔を 200ms にする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 24 | 3,287 | 38,096 | 761,769 | 100% |
| 合計 |  |  | 24 | 3,287 | 38,096 | 761,769 | 計 803,176 |

- `--since '2026-10-18 01:25:14'` で数えた。立ててから着手までに TODO-126 を挟んだため
- 終点は作業のコミット（37bd78f）で、そのあとの verifier の確認と決着の分は入っていない。verifier は Claude Code の通知で約 32,000 トークン
- verifier は定義のモデルが haiku（effort medium）。見込みどおり Sonnet 5.5 に上書きした

## きっかけ

四隅の検出は開発機で 0.69 秒なのに、アニメーションは 4 段階 × 500ms で 2 秒待たせていた。ユーザーの指示で 200ms にする（2026-10-18）。

## やったこと

- `analyzer/static/scan.js` の `STAGE_MS` の edges・uprights・candidates・corners を 500 → 200。読み取りの段階は 500 のまま
- `analyzer/test_photo_view.py` の 2 つのテスト（表の値、四隅の 4 段階が出し終わる時刻 2000 → 800ms）を新しい値に合わせた
- `analyzer/README.md` の「どの段階も 500 ミリ秒」を書き直した
- analyzer 0.70.0 → 0.70.1（PR #370）

## 確かめたこと

- `analyzer/test_photo_view.py` は変更前の値のテストでは 2 件落ち、直したあと 12 件通った。CI の `test` も通った
- ローカル（0.70.1）の live_view の窓で `samples/screen2.jpg` を 1 回読み、写真を読み込んでから四隅が決まるまで約 1.07 秒（変更前は約 2.7 秒）。4 段階とも出た（`archives/agents/TODO-124/verifier-report.md`）

## 分担の振り返り

- verifier: 時間を実測し、食い違いは無し。各段階のフレームは抜いておらず、「順に描かれた」は受信と完了の時刻からの推定と報告した
- 見込みとの食い違いは無し。見込みに無かったのは、テストが 500ms を固定で持っていたことで、main が直した
- 次に同じ規模（表の値だけの変更）なら同じ組み方でよいが、verifier は Haiku 5.5 で足りるかを試してよい（突き合わせる対象が 1 つの時刻だけのため）
