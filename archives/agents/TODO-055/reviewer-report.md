# TODO-055 reviewer の報告

対象: `git diff adfedd7..HEAD`（ブランチ claude/gnubg-arm64-wheel）。

## 要修正

### 1. `README.md:130-131` ― arm64 では `uv sync` が失敗するという記述が残っている

- 何が: 「Raspberry Pi などの arm64 の Linux では、gnubg の Python パッケージが配布されていないので
  `uv sync` が失敗します。そちらでは Docker（`docker compose up -d --build`）で動かします。」のまま。
- なぜ: この差分の目的がまさに aarch64 で `uv sync` を通すこと。同じ README の 144 行・169 行は
  直してあり、130 行台だけ古い。依頼の `rg` のパターン（no-sync / ソースからビルド）には掛からない
  言い回しなので漏れた。`rg -n -i -e "gnubg.*(arm|aarch)" -e "(arm|aarch).*gnubg"` で見つかる。

### 2. `docs/HANDOVER.md:98-99` ― 「arm64 では Dockerfile が gnubg-pypi の固定したコミットからビルドする」が残っている

- 何が: 「gnubg の PyPI パッケージには arm64 の wheel もソース配布もないので、arm64 では Dockerfile が
  StonesAndDice/gnubg-pypi の固定したコミットからビルドする。gnubg の版を上げるときはそのコミットも合わせる。」
- なぜ: Dockerfile からビルドは消えた。版を上げる手順も、今は `.github/workflows/gnubg-wheel.yml` の `REV` と
  タグ、`pyproject.toml` の URL、`uv lock` になっている。HANDOVER.md は別アカウントの Claude が読む
  引き継ぎ文書（CLAUDE.md「共同開発」）なので、古いままだと相手が誤った前提で動く。

## 検討

### 3. `pyproject.toml:13` と `:31` ― x86_64 は `>=1.1.0a16`、aarch64 は 1.1.0a16 固定で、版が分かれうる

- 何が: x86_64 側は `gnubg>=1.1.0a16`（PyPI）、aarch64 側は URL で 1.1.0a16 固定。
- なぜ: PyPI に新しい gnubg が出て `uv lock --upgrade` すると、x86_64 だけ上がり aarch64 は据え置きになる
  （uv.lock では別の `[[package]]` として並ぶ構造。`uv export --frozen` で marker が分かれているのを確認）。
  CI の x86_64 と本番の Pi で解析エンジンの版が違う状態が黙って起きる。
  `gnubg==1.1.0a16` に固定すれば、上げるときに両方を同時に直すことになる。実害は未確認（現時点では両方 1.1.0a16）。

### 4. `.github/workflows/gnubg-wheel.yml:6` ― 版を上げる手順に `uv lock` が無い

- 何が: 「REV を変え、tag を push してから pyproject.toml の URL を直す」で止まっている。
- なぜ: URL を直しただけでは `uv.lock` が古く、`uv sync --frozen`（Docker・CI）は古い URL のまま入れる。
  「`uv lock` して両方をコミット」まで書くと手順が閉じる（CLAUDE.md「変えないもの」の pyproject.toml と uv.lock を一緒にコミット）。

### 5. `pyproject.toml:29` ― 「PyPI の gnubg は x86_64 の wheel だけ」は不正確

- 何が: uv.lock の PyPI 側には `macosx_14_0_arm64`・`win_amd64` の wheel もある。正しくは「Linux 向けは x86_64 だけ」。
- なぜ: README.md:129 は「Apple Silicon の Mac なら uv で動く」と書いており、コメントと食い違って見える。
  macOS の `platform_machine` は `arm64`（`aarch64` ではない）ので、marker の動作自体は正しい。

## 問題の無かった点（1 行ずつ）

- marker: `uv export --frozen --no-dev` で `gnubg==1.1.0a16 ; platform_machine != 'aarch64'`（PyPI）と URL wheel `; platform_machine == 'aarch64'` に分かれる。x86_64 は PyPI のまま。
- uv.lock の revision 5: `uvx --from 'uv==0.11.*'`（0.11.33）で `uv sync --frozen --no-dev --dry-run` が通り、URL の wheel を入れる計画が出た。読める。差分は resolution-markers と gnubg の 2 項目だけ。
- Python 3.13 の aarch64: `uv sync --frozen --dry-run --python 3.13` は「cp312 の wheel しかない」と明示的なエラーで止まる。変更前も PyPI に aarch64 の wheel が無く失敗していたので悪化ではない。`.python-version` は 3.12。
- 共有ライブラリ: `.so` の NEEDED は libglib-2.0 / libgobject-2.0 / libreadline.so.8 / libgmp.so.10 / libstdc++ / libm / libgcc_s / libc、GLIBC は最大 2.34。実行用イメージの libglib2.0-0（gobject を含む）・libreadline8・libgmp10 で足りる。libstdc++6・libgcc-s1 は apt の依存で slim にも入っている。libsqlite3 は要らない。
- ubuntu-24.04-arm（glibc 2.39）で libreadline8t64・libgmp10・libglib2.0-0t64 が入っているかは未確認（CI の arm64 の test で分かる）。
- wheel のタグは `linux_aarch64`（manylinux ではない）。Pi・Docker とも bookworm なので問題なし。Release `gnubg-1.1.0a16` は draft でも prerelease でもなく、wheel 1 つ。
- `rg -n -e "no-sync" -e "no-install-package" -e "ソースからビルド" --glob '!archives/**'`: 残りは TODO.md の背景と PI-038 の確かめ方だけで、どちらも意図どおり。
- ブランチ保護は無い（`gh api .../protection` が 404）ので、test を matrix にしてジョブ名が変わっても必須チェックは詰まらない。
- バージョン: analyzer/ と recognizer/ のコードは変わっていないので、上げないのが CLAUDE.md どおり。
- docs/PI_CHECKS.md: PI-038 の位置（PI-037 の上）、「残っている項目」「次の番号」の更新は決まりどおり。
- 範囲: 指示に無い変更は無い。

## 作り込みすぎ

作り込みすぎ: なし（Dockerfile は 20 行減り、gnubg-wheel.yml は 1 ジョブ 2 ステップ）。

## リポジトリ外（参考）

- 利用者の memory `~/.claude/projects/-home-ytani-work-bganalyzer/memory/pi-test-env.md` は「Pi では uv sync が gnubg で失敗する、`--no-sync` で動かす」のまま。マージ後は古くなる。
