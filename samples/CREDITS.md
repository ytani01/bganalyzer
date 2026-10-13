# サンプル写真の出典

`commons-*.jpg` は Wikimedia Commons の写真です。どれも CC BY / CC BY-SA で、人の顔や個人情報は写っていません。
Commons が配る縮小版（長辺 1920px、元が小さいものは 960px）をそのまま使っていて、ほかの加工はしていません。
CC BY-SA の写真（とその縮小版）は同じ CC BY-SA で配布します。正解の `*.truth.json` は目で読みました。

| ファイル | 元の写真 | 作者 | ライセンス |
|---|---|---|---|
| `commons-case-midgame.jpg` | [Backgammon (293614687).jpg](https://commons.wikimedia.org/wiki/File:Backgammon_(293614687).jpg) | Takuro Iwabuchi | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) |
| `commons-dark-homeleft.jpg` | [Backgammon (49543113023).jpg](https://commons.wikimedia.org/wiki/File:Backgammon_(49543113023).jpg) | Martina Grosty | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) |
| `commons-leather-cups.jpg` | [Backgammon board.jpg](https://commons.wikimedia.org/wiki/File:Backgammon_board.jpg) | Ptkfgs | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) |
| `commons-tavli-black.jpg` | [Tavli Board without slots (traditional) 1960s.jpg](https://commons.wikimedia.org/wiki/File:Tavli_Board_without_slots_(traditional)_1960s.jpg) | Nikos Kitsakis | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `commons-tavli-blue.jpg` | [Tavli Board without slots (traditional) C.jpg](https://commons.wikimedia.org/wiki/File:Tavli_Board_without_slots_(traditional)_C.jpg) | Nikos Kitsakis | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `commons-tavli-burl.jpg` | [Tavli Board without slots (traditional).jpg](https://commons.wikimedia.org/wiki/File:Tavli_Board_without_slots_(traditional).jpg) | Nikos Kitsakis | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `commons-tavli-grey.jpg` | [Tavli Board with slots B.jpg](https://commons.wikimedia.org/wiki/File:Tavli_Board_with_slots_B.jpg) | Nikos Kitsakis | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `commons-tavli-red-brown.jpg` | [Tavli Board with slots.jpg](https://commons.wikimedia.org/wiki/File:Tavli_Board_with_slots.jpg) | Nikos Kitsakis | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `commons-tavli-red-diamond.jpg` | [Tavli Board without slots (traditional) B.jpg](https://commons.wikimedia.org/wiki/File:Tavli_Board_without_slots_(traditional)_B.jpg) | Niko Kitsakis | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `commons-tavli-red-white.jpg` | [Tavli Board with slots C.jpg](https://commons.wikimedia.org/wiki/File:Tavli_Board_with_slots_C.jpg) | Nikos Kitsakis | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `commons-travel-case.jpg` | [Backgammon Layout.jpg](https://commons.wikimedia.org/wiki/File:Backgammon_Layout.jpg) | TaurusEmerald | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

photo2〜4 は ai1 が撮った写真、screen1・screen2 はアプリの画面とツイートの画像（盤以外は塗りつぶし）です。

`external/` には、リポジトリに入れられない画像（著作権のある盤面図）の出典 URL と正解だけを置いています。
画像は `recognizer/evaluate.py` が URL から取ってきて `external/` に保存します（Git には入りません）。
