#!/bin/sh
# Run daily from cron on the Pi (docs/raspi.md): measure collected/ again (recognizer/collected.py).
# When it measured, Claude Code tries to fix the misreads and opens a PR (tools/collected_prompt.md).
# This script merges that PR only if it changes nothing outside recognizer/ and CI passes, then updates the Pi.
#   tools/collected_cron.sh            # what cron runs
#   tools/collected_cron.sh --force    # measure even without 10 new pairs
set -eu
cd "$(dirname "$0")/.."
ROOT=$(pwd)
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
log() { echo "$(date '+%F %T') $*"; }

out=$(docker compose exec -T app python recognizer/collected.py /data/samples "$@")
log "$out"
[ "$out" = measured ] || exit 0

clean_main() { [ "$(git branch --show-current)" = main ] && [ -z "$(git status --porcelain --untracked-files=no)" ]; }
clean_main || { log "the Pi's checkout is not a clean main: stopped"; exit 1; }
git pull -q   # Claude's worktree starts from here
name="collected-$(date +%Y%m%d-%H%M)"
reply=$(sed "s|COLLECTED|$ROOT/collected|g" tools/collected_prompt.md | claude -p -w "$name" \
  --model opus --max-budget-usd 5 --add-dir "$ROOT/collected" --permission-mode dontAsk \
  --allowedTools Read Glob Edit Write \
    "Bash(uv run -q --no-project --python 3.12 --with opencv-python-headless --with numpy python recognizer/evaluate.py:*)" \
    "Bash(git status:*)" "Bash(git diff:*)" "Bash(git log:*)" "Bash(git switch -c claude/collected-:*)" \
    "Bash(git add recognizer/:*)" "Bash(git commit:*)" "Bash(git push -u origin claude/collected-:*)" "Bash(gh pr create:*)" \
  --disallowedTools "Read(**/*.truth.json)") || { log "claude failed"; exit 1; }
pr=$(echo "$reply" | tail -n 1 | sed -n 's/^PR: \([0-9][0-9]*\)$/\1/p')
git worktree remove -f -f ".claude/worktrees/$name" 2>/dev/null && git branch -q -D "worktree-$name" || true
[ -n "$pr" ] || { log "no PR"; exit 0; }

# the gate: Claude decided, this checks
outside=$(gh pr view "$pr" --json files --jq '.files[].path' | grep -v '^recognizer/' || true)
[ -z "$outside" ] || { log "PR #$pr changes files outside recognizer/, not merged: $outside"; exit 1; }
case "$(gh pr view "$pr" --json headRefName --jq .headRefName)" in claude/collected-*) ;; *) log "PR #$pr is not Claude's: not merged"; exit 1 ;; esac
for _ in $(seq 60); do gh pr checks "$pr" 2>/dev/null | grep -q pytest && break; sleep 10; done   # until CI starts
gh pr checks "$pr" | grep -q pytest || { log "PR #$pr: CI did not start, not merged"; exit 1; }
gh pr checks "$pr" --watch --interval 30 >/dev/null || { log "PR #$pr: CI failed, not merged"; exit 1; }
gh pr merge "$pr" --merge
log "PR #$pr merged"

clean_main || { log "the Pi's checkout is not a clean main: not updated"; exit 1; }
git pull -q
docker compose up -d --build
for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
  v=$(curl -s --max-time 5 http://127.0.0.1:8000/version || true)
  case "$v" in *"$(git rev-parse --short HEAD)"*) log "updated: $v"; exec docker compose exec -T app python recognizer/collected.py /data/samples --force ;; esac
  sleep 10
done
log "the app did not come back with $(git rev-parse --short HEAD)"
exit 1
