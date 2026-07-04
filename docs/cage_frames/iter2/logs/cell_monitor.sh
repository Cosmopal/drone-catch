#!/bin/bash
# Wrapper-agnostic per-cell timing monitor. Tracks any cage_harness.py cell:
#   wall start/end + CPU-seconds (hibernation-proof). Exits after the run is
#   idle (no cell seen for IDLE_EXIT samples) once it has seen at least one,
#   or if no cell ever appears within STARTUP_MAX samples.
CLK=$(getconf CLK_TCK)
LOG=/mnt/c/Users/Palash/Projects/robots/drone-catch/.claude/worktrees/grasp-iter2/docs/cage_frames/iter2/logs/cell_timing.log
cpu_of(){ awk -v clk=$CLK '{print ($14+$15)/clk}' /proc/$1/stat 2>/dev/null; }
last_pid=""; last_cmd=""; last_cpu=0; start_epoch=""
seen_any=0; misses=0; startup=0
IDLE_EXIT=15   # ~5 min of no cell -> run done
STARTUP_MAX=90 # ~30 min waiting for first cell -> give up
echo "=== cell_monitor(v2) started $(date '+%F %T') ===" >> "$LOG"
while :; do
  pid=$(pgrep -f "cage_harness.py --" | head -1)
  if [ -n "$pid" ]; then
    seen_any=1; misses=0
    cmd=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null | sed 's#.*cage_harness.py ##')
    if [ "$pid" != "$last_pid" ]; then
      if [ -n "$last_pid" ]; then
        end_epoch=$(date +%s); wall=$((end_epoch-start_epoch))
        printf 'CELL END   %s | %-45s | cpu=%ss wall=%ss gap=%ss\n' \
          "$(date '+%T')" "$last_cmd" "$last_cpu" "$wall" "$((wall - ${last_cpu%.*}))" >> "$LOG"
      fi
      start_epoch=$(date +%s)
      printf 'CELL START %s | %s\n' "$(date '+%T')" "$cmd" >> "$LOG"
      last_pid=$pid; last_cmd=$cmd
    fi
    last_cpu=$(cpu_of $pid)
  else
    if [ $seen_any -eq 1 ]; then
      misses=$((misses+1))
      if [ $misses -ge $IDLE_EXIT ]; then
        if [ -n "$last_pid" ]; then
          end_epoch=$(date +%s); wall=$((end_epoch-start_epoch))
          printf 'CELL END   %s | %-45s | cpu=%ss wall=%ss gap=%ss\n' \
            "$(date '+%T')" "$last_cmd" "$last_cpu" "$wall" "$((wall - ${last_cpu%.*}))" >> "$LOG"
        fi
        echo "=== run idle, monitor stopped $(date '+%F %T') ===" >> "$LOG"; break
      fi
    else
      startup=$((startup+1))
      [ $startup -ge $STARTUP_MAX ] && { echo "=== no cell appeared, monitor gave up $(date '+%F %T') ===" >> "$LOG"; break; }
    fi
  fi
  sleep 20
done
