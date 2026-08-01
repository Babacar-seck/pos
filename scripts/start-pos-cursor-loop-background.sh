#!/usr/bin/env bash
# Start agents2/pos-cursor-loop.sh detached with nohup.
#
# Usage (repo root):
#   ./scripts/start-pos-cursor-loop-background.sh
#   ./scripts/start-pos-cursor-loop-background.sh --restart   # kill existing pid first
#
# Stop:
#   kill "$(cat tmp/pos-cursor-loop.pid)" && rm -f tmp/pos-cursor-loop.pid
#
# Optional env (passed through): AGENT_LOOP_SLEEP_MINUTES, AGENT_PROMOTE,
# AGENT_PROMOTE_INTERVAL_HOURS, AGENT_GIT_SYNC, OLLAMA_MODEL, etc.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

mkdir -p "$REPO_ROOT/tmp"
PID_FILE="${POS_CURSOR_LOOP_PID_FILE:-$REPO_ROOT/tmp/pos-cursor-loop.pid}"
LOG="${POS_CURSOR_LOOP_LOG:-$REPO_ROOT/tmp/pos-cursor-loop.log}"
RESTART=0
for arg in "$@"; do
  case "$arg" in
    --restart | -r) RESTART=1 ;;
    -h | --help)
      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
  esac
done

if [ -f "$PID_FILE" ]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "${OLD_PID:-}" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    if [ "$RESTART" = "1" ]; then
      echo "Stopping existing pos-cursor-loop pid=${OLD_PID}" >&2
      kill "$OLD_PID" 2>/dev/null || true
      # Give the sleep/cycle a moment to exit; escalate if needed.
      for _ in 1 2 3 4 5; do
        kill -0 "$OLD_PID" 2>/dev/null || break
        sleep 1
      done
      if kill -0 "$OLD_PID" 2>/dev/null; then
        kill -9 "$OLD_PID" 2>/dev/null || true
      fi
      rm -f "$PID_FILE"
    else
      echo "pos-cursor-loop already running (pid ${OLD_PID}). Use --restart or: kill ${OLD_PID} && rm -f ${PID_FILE}" >&2
      exit 1
    fi
  else
    rm -f "$PID_FILE"
  fi
fi

{
  echo ""
  echo "===== loop start $(date) ====="
} >>"$LOG"

nohup "$REPO_ROOT/agents2/pos-cursor-loop.sh" >>"$LOG" 2>&1 &
echo $! >"$PID_FILE"

echo "Started pos-cursor-loop pid=$(cat "$PID_FILE")"
echo "Log: $LOG  (tail -f \"$LOG\")"
echo "Stop: kill \"\$(cat \"$PID_FILE\")\" && rm -f \"$PID_FILE\""
