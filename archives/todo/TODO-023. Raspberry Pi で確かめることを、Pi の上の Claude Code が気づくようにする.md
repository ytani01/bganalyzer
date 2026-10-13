# TODO-023. Raspberry Pi で確かめることを、Pi の上の Claude Code が気づくようにする

**担当:** ai1

Raspberry Pi 上で確認が必要なものは、Pi の上の Claude Code が気づくようにする（ユーザーの依頼）。

**2026-10-13 に完了:** [docs/PI_CHECKS.md](../../docs/PI_CHECKS.md) を作り、これまでの PR で Pi では確かめていなかったこと
（3手読みの時間、ダイスの読み取りを含む写真の読み取りの時間、今の main が Pi で動くこと）を PI-001〜003 として入れた。
CLAUDE.md に、Pi の上の Claude Code は git pull のあとにこれを読んで確かめ結果を書くこと、
マージ後に Pi で確かめる必要がある変更はその PR の中で項目を足すことを書いた。
