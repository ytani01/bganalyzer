# TODO-067 の分担

- 調査と報告（`docs/corner-methods.md`）は main。試しの実装はしない項目なので implementer・verifier は入れていない
- reviewer（Opus 5.5 / high）が、報告の主張と根拠（測った値・コード・TODO-061・078・104 の記録）の食い違いを見た（`reviewer-report.md`）。要修正 6 件と検討の多くを報告に反映した
- `check_corners-main.txt` は `samples/` 67 枚、`check_corners-collected-raw.txt` は開発機の `collected/` の生の写真 41 枚（塗りつぶす前）を、どちらも recognizer 0.24.0 の `check_corners.py` で測った値
