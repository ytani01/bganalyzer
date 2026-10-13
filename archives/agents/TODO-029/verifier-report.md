# verifier-report (TODO-029)
- docker build -t bganalyzer-verify . : 終了コード 0
- evaluate.py（コンテナ内、全 truth）: 終了コード 0。出力は pi-evaluate-0.6.2.txt
- 0.6.1 との diff: 1 行だけ（photo3）。ほかは全行同一（ポイント、バー、ホーム、ダイスも変化なし）
  - 0.6.1: `cube not found (read None, truth centre)`
  - 0.6.2: `cube ok (read centre, truth centre)`
- 期待どおり: screen2 `cube ok (read black, truth black)`、photo4 `cube ok (read None ...)`、commons-diagram-holding と commons-set-cube-dice は centre で当たり、キューブなしサンプルは read None で ok
- 0.6.1 から変わらず cube not found のまま（今回の直しの対象外か未確認、実害は未確認）: commons-rollup-oblique、screen1（どちらも truth centre）
- pytest: イメージに pytest が無かった（`No module named pytest`）。実行していない
- git status: tracked の変更なし。追加は archives/agents/TODO-029/ の報告と測定結果のみ
