# TODO-111. 読み上げを端末に依存しない方式にする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（聞き比べ・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（聞き比べ・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

TOKENS_TABLE

- reviewer と verifier は定義（`~/.claude/agents/`）のモデル・effort のまま（reviewer は opus / high、verifier は haiku / medium）
- TODO-112〜114 と並行して進めたので、範囲（立ててから決着まで）にはそちらの分も入っている

## きっかけ

今の読み上げはブラウザの音声合成で、声は端末しだいだった（開発機の Chromium は声が無く鳴らない。TODO-110）。ユーザーが、できるだけ端末に依存しない方式にしたいと言った（2026-10-17）。

## やったこと

- 候補（サーバーで Open JTalk、Google 翻訳の読み上げ、Google Cloud TTS、ブラウザの中で合成）を出し、ユーザーが Open JTalk と Google 翻訳を聞き比べることにした。
  Open JTalk はシステムに入れずに `pyopenjtalk-plus` で作れた。最初は長い文で作ったが、ユーザーの言うとおり短い文 3 つで聞き比べ、ユーザーが Google 翻訳の声を選んだ
- `analyzer/speech.py`: `GET /speech?text=`（200 文字まで）。サーバーが Google 翻訳の読み上げ（`translate_tts`、公式でない API）に頼み、`audio/mpeg` を返す。失敗は 502（理由はログに残す）。設定なしでいつも動く（ユーザーが決めた）
- `analyzer/static/app.js`: 読み上げの文を「。」で区切り、1 文ずつ `<audio>` で鳴らす。失敗したら残りの文をブラウザの音声合成で読む。`stopSpeaking` で止める。「読み上げ」のボタンはブラウザの音声合成が無くても出す
- `analyzer/static/sw.js`: `/speech` は Service Worker を通さない（文ごとの音声がたまり、オフラインで別の文の音声を返すため）
- `tools/pi_ui_check.py`・`tools/ui_snapshot.py`: 音を鳴らさず、頼んだ文を記録する。確認は最後の文が終わるまで待つ
- `CLAUDE.md`（読み上げの文を Google に送ること）、`README.md`、`analyzer/README.md`、`docs/raspi.md`。analyzer 0.63.0
- 文の組み立て（`BgResult.speechText`）は変えていない

## 確かめたこと

- reviewer: 確認の道具が最初の 1 文しか見ていない、`ui_snapshot.py` が本物の音を鳴らす、README の構成図と表に `speech.py` が無い、を見つけた。直した。`/speech` が誰でも使える件はユーザーが「いつも動かす」と決めた（`archives/agents/TODO-111/reviewer-report.md`）
- verifier: live_view のブラウザで、`/speech` が文の数だけ 200・audio/mpeg を返して約 8.7 秒で戻る、`/speech` を 502 にすると全部の文がブラウザの音声合成に回る（`archives/agents/TODO-111/verifier-report.md`）
- PR #330 の GitHub Actions の `test` が通った
- ローカル: マージ後（analyzer 0.64.0 の時点）に live_view のブラウザで解析して「読み上げ」を押すと、`/speech` が 2 回とも 200・audio/mpeg で、約 8.6 秒鳴った

## 残ること

- Google 翻訳の読み上げは公式の API ではないので、止まったらブラウザの音声合成に戻る。声が無い端末（開発機の Chromium など）では、そのとき何も鳴らず、知らせも出ない（reviewer の指摘。前からの動き）
- 読み上げの途中で「戻る」を押しても止まらない（前からの動き）

## 分担の振り返り

- reviewer は確認の道具の待ち方の抜けを、Playwright で 3 回試して示した。確認の道具そのものの不具合で、verifier では拾えない種類だった
- verifier は食い違いを見つけなかった
- 見込みと食い違わなかった。聞き比べで長い文を使ったのは無駄だった（ユーザーに短い文にと言われた）。次に声を比べるときは、最初から短い文 2〜3 個にする
