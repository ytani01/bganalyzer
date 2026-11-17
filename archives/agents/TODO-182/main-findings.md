# TODO-182 調べたこと（main、2026-11-17）

- d708806 は points・read.points・fixed_points を書き換えたが、bottom_colour は 0 のまま。
- 正解の四隅・side=right・home=right・bottom_colour=0 で recognize すると
  [3,0,0,0,0,-5,0,-3,0,0,0,4,-5,0,0,3,1,0,5,0,0,0,0,-2]。暗い駒（色 0）は 1・12・17・19 にある。
  直した正解の points（手前の駒が 6・8・13・24）は、これの白黒を入れ替えたものに当たり、手前の駒は明るい駒（bottom_colour=1）。
- evaluate.py は白黒の両方を試すので points の一致は 20/24 で、基準と同じ。
- import_collected.py の clean() は正解の各値をそのまま写すだけで、向きや色を変えない。
- PR #537 は pytest が落ちたまま 2026-11-16T21:16:43Z に ytani01 のアカウントでマージされた。
  import_collected.py の merge() はチェックが落ちると PR を開いたまま残すので、自動の処理がマージしたのではない。
