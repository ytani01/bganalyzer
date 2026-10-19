#!/usr/bin/env python3
"""PreToolUse（Bash）: テスト全体の pytest を手元で流させない。GitHub Actions の test が流す。

テストのファイル（test_*.py）を指定した実行だけ通す。
"""

import json
import re
import sys

cmd = (json.load(sys.stdin).get("tool_input") or {}).get("command") or ""
# pytest を起動するところだけ（行頭か ; & | ( の後の pytest / uv run pytest / python -m pytest）。
# 文字列や検索のパターンに出てくる pytest には当てない
run = re.search(
    r"(?m)(?:^|[;&|(])\s*(?:uv\s+run\s+(?:-\S+\s+)*|python3?\s+-m\s+)?pytest\b[^;&|\n]*",
    cmd,
)
if run and not re.search(r"test_\w+\.py", run.group()):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "テスト全体の pytest は手元で流さない。GitHub Actions の test の結果を見る"
                    "（gh pr checks）。1 ファイルだけなら analyzer/test_*.py を指定する（CLAUDE.md の「共同開発」）",
                }
            },
            ensure_ascii=False,
        )
    )
