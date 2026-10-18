# TODO-136 reviewer の報告

対象: worktree `bganalyzer-todo136` の未コミットの差分（`git diff` と新規の `recognizer/train_corners.py`）。

## 要修正

### 1. `recognizer/README.md:278` 「すべて整数と…x86_64 と Raspberry Pi で四隅は同じになる」が古くなった
- 今は `locate` が `cv2.dnn` の float 推論で四隅の手がかりを出し、`guess` の `score`（corners.py:383-387）が
  `np.linalg.norm` の float で罰を引く。CPU で手がかりが少しずれれば、選ぶ候補や探し直しの有無が変わりうる。
- CLAUDE.md「精度の確認」で float は使ってよいことになっている（TODO-074）ので、コードではなく文書の直し。
  「TODO-136 からはモデルの推論が float なので、機械で四隅がわずかに変わりうる」の類いに書き換える。

### 2. `docs/corners.md:21-38`（全体の流れの図）が新しい分岐を描いていない
- recognizer/README.md:233 が「図で追った説明」として指している文書。図は「点数が 0.15 未満 → 見つからない」で終わるが、
  今は (a) 先に YOLO で四隅を当てて遠い候補の点数を下げ、(b) 見つからなければモデルの外接矩形 +15% を crop として探し直す
  （corners.py:532-533、555-558）。差分に含まれていない。
- 図に「`fixed`・`crop`・横からが無ければ YOLO の四隅」「見つからない → YOLO の周りで探し直す」を足す必要がある。

## 検討

### 3. 四隅の並べ方が学習データの中で揃っておらず、`guess` の候補とも揃わない（実害は未確認）
- `samples/` の 6 枚（collected-2hhe5o・4b88u3・5wxq9t・dplmij・mghnwm・xqv7k9）は、正解の TL..BL が画像の位置の順でなく
  盤の向きの順（90° 前後回っている）。train_corners.py の `order` で並べ直すと `[3,0,1,2]` などになる（実測）。
  一方 `add_coco`（train_corners.py:113）は `order` で画像の位置の順に並べる。学習ラベルに 2 つの流儀が混ざっている。
- 実測: この 6 枚に `locate` を当てると、5 枚は正解と同じ（盤の向きの）順で返る（回し直しで近づくのは dplmij だけ）。
  `guess` の候補は画像の位置の順なので、`score` の `norm(q - hint, axis=1).max()`（corners.py:386）は対応しない隅どうしを比べ、
  正しい盤にも長辺の 20〜30% 分の罰が付く。
- この 6 枚は check_corners の前後とも 22〜77% か「-」で、報告の数字には効いていない。困るのは、縦長に写った正面の写真で
  モデルが回った順を返した場合（起きるかは未確認）。罰を順によらない比べ方（4 通りの回しの最小）にするか、学習ラベルを
  `order` で揃えるか、の判断が要る。

### 4. `train_corners.py:95-98` `order` は 45° 前後に回った四角形で同じ点を 2 回選ぶ
- 和と差の argmin/argmax なので、ひし形 `[(0,-1),(1,0),(0,1),(-1,0)]` で `[0,0,1,2]` を返す（実測）。
  `write` は重複を弾かないので、そのラベルは 2 つの隅が同じ点になる。Roboflow のデータに該当がどれだけあるかは未確認。

### 5. `corners.py:494-512` モデルが無い・読めないとき `find_corners` が例外で落ちる
- `MODEL` を存在しないパスにすると `cv2.error`（Can't read ONNX file）が `find_corners` から出る（実測）。`_net` は None のまま残るので、
  以後のどの呼び出しも同じく落ちる。/find-corners は前は動いていた写真でもエラーになる。
- `corners_model.onnx` は今は未追跡（`??`、11 MB）。`.gitignore` には掛かっていない（`git check-ignore` で無し）ので、コミットに
  入れ忘れなければ起きない。モデルが読めないときに今までの探し方へ戻すかは判断。

### 6. 罰の分岐（探し直しにならない場合）を壊しても落ちるテストが無い（未確認）
- test_api.py の collected-sj1vrx は、実測で探し直しの経路（1 回目 None → crop で再帰）を通っている。手がかりの罰だけで
  当たる経路と、`locate` が `MODEL_CONF` 未満で None を返す経路は、どのテストも狙っていない。`HINT_WEIGHT = 0` にして
  落ちるテストがあるかは流していない（手元でテスト全体は流さない決まりのため）。

### 7. 文書の一覧に新しいファイルが無い
- `recognizer/README.md:727` 付近のファイル一覧に `train_corners.py` と `corners_model.onnx` が無い。
- `README.md:83` の corners.py の役割が「盤の縁の直線と、2 段 12 列の三角形の並びから」のままで、YOLO の手がかりに触れていない。

### 8. README と TODO.md は YOLO を使わない条件を「`fixed`・`crop` が無いとき」とだけ書いている
- `recognizer/README.md:247`。コード（corners.py:532）は `search`（横から撮った写真）でも使わない。TODO.md の「途中で変えたこと」には
  `side` も書いてあるので、README だけ足りない。

## 好みの範囲

### 9. `samples/CREDITS.md` に、モデルが元のデータを変えて（Fork・前処理なし版・COCO）使ったことが書かれていない
- CC BY 4.0 は変更の有無の表示を求める。recognizer/README.md:251-253 には書いてあるので、CREDITS から README を指すだけで足りる。

## 問題が無かった項目

- `find_corners` の分岐: hint は `crop`・`search`・`fixed` のどれも無いときだけ。探し直しは `crop` を付けて呼ぶので hint が None になり、再帰は 1 段で止まる。
  探し直しで progress の段階がもう一度送られるが、scan.js は段階ごとに上書きする作り（`seen[cur.stage]`）で、find_corners_any の横からの探索でも既に起きている。
- `_swap` と `guess` の点数の比べ方: `_score` の呼び出し 4 か所すべてが `score` に置き換わり、`_swap` も同じ `score` を受ける。MIN_SCORE は罰を引いた後の点数と比べ、
  罰で届かなければ探し直しへ進む（docstring・README の「見つからなければ」と一致）。side.py の `_score` は別物で、罰は入らない。
- `locate` のレターボックス（114 で埋める、中央寄せ、`swapRB=True`）と座標の戻し方（`- [left, top]` してから `/ r`）は ultralytics の前処理と合う。
  sj1vrx などで手がかりが正解から長辺の 3% 程度に来る（実測）。`readNetFromONNX` と `forward` はロックの中。
- `add_coco`: 多角形の凸包を 4 点に近似できたものだけ使う。上の 4 以外は問題なし。
- バージョン: recognizer 0.26.1 → 0.27.0（機能の変更）で CLAUDE.md の決まりどおり。analyzer はテストだけなので上げないで合う。

## 作り込みすぎ

- `corners.py:532`: shrink: `not any(p is not None for p in fixed or [])`。`all(p is None for p in fixed or [])`、同じ 1 行で否定が 1 つ減る。

net: -0 lines possible.（ほかは削れるものなし）
