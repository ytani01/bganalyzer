# TODO-002. PWA と API を自宅の Raspberry Pi で公開する

**担当:** ai1

## 決めたこと

- 公開先は **自宅の Raspberry Pi（64bit OS）+ Tailscale Funnel**（2026-10-12、ai1）。
  最初は Cloudflare Tunnel で準備したが、ドメイン代がかかるので、無料でドメインの要らない Tailscale Funnel にした。
- URL は `https://<Piの名前>.<tailnet名>.ts.net/bg/`。同じ Pi で別のアプリも別のパスで公開できるよう、`/bg/` の下に置く。

## やったこと（PR #15）

- `Dockerfile` を2段にし、x86_64 以外では gnubg を StonesAndDice/gnubg-pypi の固定コミットからビルドする
  （PyPI の gnubg には arm64 の wheel もソース配布もない）
- `compose.yaml` でアプリを常駐させる。HTTPS は Pi に入れた Tailscale が受けて 8000 番に転送する
- PWA は API を相対パスで呼び、末尾の `/` がない URL では付け直す（Tailscale はパスを取り除いて転送するため）
- GitHub Actions の `docker` で x86_64 と arm64 のビルド・起動・解析を確かめる
- 手順は [docs/raspi.md](../../docs/raspi.md)

## 確かめたこと

- 2026-10-12、ai1 が docs/raspi.md の手順で Pi に入れ、スマホから https で使えることを確かめた
