# Raspberry Pi で確かめること

マージしたあと、自宅の Raspberry Pi（公開している本番）でしか確かめられないことの一覧です。
クラウドの Claude は Pi に入れないので、**Pi の上で動く Claude Code がここを読んで確かめ、結果を書き込みます。**

## Pi の上の Claude Code がやること

1. `bganalyzer` フォルダで `git pull` し、`docker compose up -d --build` でアプリを更新する（手順の詳細は [raspi.md](raspi.md) の「ふだんの運用」）。
2. `curl -s http://127.0.0.1:8000/version` が、pull した main の版とコミットになっているか確かめる。
3. 下の「未確認」の項目を上から確かめ、項目に **結果**（日付・測った値・OK か）を書き足して「済」に移す。
   スマホの画面など Pi だけでは確かめられないことは、ユーザーに頼み、そう書いておく。
4. 期待と違ったら（遅すぎる・落ちる・値が違う）、ユーザーに報告し、TODO.md に項目を足す。
5. ブランチを切って PR にし、CLAUDE.md の「共同開発」どおりにマージする（main に直接 push しない）。

## 書き方（項目を足す人へ）

マージ後に Pi で確かめる必要がある変更は、**その PR の中でここに項目を足す**。番号は通し（次は `PI-004`）。

```markdown
### PI-00N. 何を確かめるか
- **足した日・PR:** 2026-10-13、PR #42（TODO-018）
- **確かめ方:** 実行するコマンドや手順
- **期待:** どうなれば OK か
```

---

## 未確認

（なし）

---

## 済

### PI-001. 3手読みにかかる時間

- **足した日・PR:** 2026-10-13、PR #42（TODO-018、読みの深さを画面で選ぶ）
- **確かめ方:** 初期配置にダイス 3-1 を付けて、2手読みと 3手読みの時間を比べる。

  ```bash
  for p in 2 3; do
    curl -s -o /dev/null -w "plies=$p %{time_total}s\n" localhost:8000/analyze \
      -H 'content-type: application/json' -d "{\"position_id\":\"4HPwATDgc/ABMA\",\"dice\":[3,1],\"plies\":$p}"
  done
  ```

- **期待:** クラウドでは 2手読み 0.7 秒・3手読み 1.1 秒（2026-10-13 に測定）。Pi で数秒（目安 5 秒以内）なら OK。10 秒を超えるなら、画面で 3手読みを選んだときの注意書きを考える。
- **結果:** 2026-10-13、bb2162f。2手読み 0.36 秒、3手読み 0.98 秒。OK

### PI-002. 写真の読み取り（ダイスの読み取りを含む）にかかる時間

- **足した日・PR:** 2026-10-13、PR #37（TODO-015、ダイスの自動入力）
- **確かめ方:** ダイスの写ったサンプルを `/analyze-photo` に送って時間を測る。`dice_read` も見る。

  ```bash
  for s in photo3 commons-case-dice; do
    t=samples/$s.truth.json
    img=$(python3 -c "import json; print(json.load(open('$t'))['image'])")
    corners=$(python3 -c "import json; print(','.join(str(v) for p in json.load(open('$t'))['corners_TL_TR_BR_BL'] for v in p))")
    home=$(python3 -c "import json; print(json.load(open('$t'))['home'])")
    bc=$(python3 -c "import json; print(json.load(open('$t'))['bottom_colour'])")
    curl -s -o /tmp/$s.json -w "$s %{time_total}s\n" localhost:8000/analyze-photo \
      -F image=@samples/$img -F corners=$corners -F home=$home -F bottom_colour=$bc
    python3 -c "import json; print('  dice_read', json.load(open('/tmp/$s.json'))['dice_read'])"
  done
  ```

- **期待:** クラウドでは 1 枚 5〜6 秒（ダイスの読み取りで 1〜2.5 秒増えた。2026-10-13 に測定）。Pi で 20 秒以内なら OK。
  `dice_read` はクラウドでは両方 null（自信がないときは入れない作り。正解は photo3 が 4-4、commons-case-dice が 5-3）。
  Pi で null 以外が出たら、正解と合っているかも書く。
- **結果:** 2026-10-13、bb2162f（recognizer 0.5.1）。photo3 6.2 秒、commons-case-dice 5.9 秒。`dice_read` は両方 null。OK

### PI-003. 今の main（analyzer 0.14.0 / recognizer 0.5.0）が Pi で動く

- **足した日・PR:** 2026-10-13、PR #37〜#47（ダイスの読み取り・読みの深さ・ダイスの絵・手番の入れ替え・最善手の矢印・画面の整理）
- **確かめ方:** 上の「やること」の 1・2 のあと、`docker compose logs app` にエラーがないこと、
  `https://<Pi>.<tailnet>.ts.net/bg/` が開けることを確かめる。スマホでの見た目（最善手の矢印・戻るボタン・読み上げ）はユーザーに頼む。
- **期待:** `/version` が analyzer 0.14.0・recognizer 0.5.0（かそれ以降）で、ログにエラーがない。
- **結果:** 2026-10-13、bb2162f。`/version` は analyzer 0.14.0・recognizer 0.5.1・bb2162f。ログにエラーなし、`https://bg.<tailnet>.ts.net/bg/` は 200。OK（スマホでの見た目はユーザーに頼む。まだ見てもらっていない）

### PI-004. 上がった駒の表示（analyzer 0.15.0）

- **足した日・PR:** 2026-10-13、上がった駒を盤面図に出す PR
- **確かめ方:** 更新のあと `/version` を見る。スマホで、写真なし入力などで駒を減らし、盤面図のホーム側の外（トレイ）に
  上がった駒が薄い板の積み重ねと数で出るかをユーザーに見てもらう（古い app.js が残っていたら開き直す）。
- **期待:** `/version` が analyzer 0.15.0（かそれ以降）。手前の上がりはトレイの下から、奥の上がりは上から積まれる。
- **結果:** （未確認）
