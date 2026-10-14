# verifier 報告 2（shrink 追加後、Pi で実測）

1. check_corners.py 23 枚: README「0.11.1（Pi）」列と全 23 枚一致。最後の行 `within 3.6%: 8, further: 10, not found: 5` は「8 / 10 / 5」に一致。
2. synth.py 20 で作った 20 枚: 0.6〜1.2%（最大 synth_02 と synth_17 の 1.2%）。「20 枚とも 1.2% 以内」に合う。
3. docker pytest: 45 passed, 8 skipped, 1 warning（68 秒）。
4. rsync で写した方の shrink の INTER_LINEAR_EXACT を INTER_AREA に変更（コメントと 516 行目の 2 か所）: `-k same_on_every_cpu` が 1 failed。
   `AssertionError: commons-dark-homeleft` / `[145.7, 147.7] != [148.1, 154.3]`。落ちる。
5. 作業ツリーは変更なし（git status 空）。

食い違いなし。時間は今回測っていない。
