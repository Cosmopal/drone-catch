#!/usr/bin/env bash
# Mirrors docs/**/*.md into the Obsidian vault (drone-catch subfolder).
# Skips docs/agents/research/transcripts/ (raw JSONL logs, not notes).
# Run manually any time, or via .git/hooks/post-commit after a commit that touches docs/.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/docs"
DST="/c/Users/Palash/iCloudDrive/Documents/Dev Sync/drone-catch"

if [ ! -d "$SRC" ]; then
  echo "sync_docs_to_obsidian: no docs/ dir, skipping" >&2
  exit 0
fi

mkdir -p "$DST"

count=0
while IFS= read -r f; do
  rel="${f#"$SRC"/}"
  target="$DST/$rel"
  mkdir -p "$(dirname "$target")"
  # [[target::alias]] is a table-safe placeholder for [[target|alias]] (a literal
  # `|` inside a Markdown table cell breaks the table); only the vault copy needs
  # the real Obsidian alias syntax, so rewrite it here rather than in the repo.
  sed -E 's/\[\[([^]]*)::([^]]*)\]\]/[[\1|\2]]/g' "$f" > "$target"
  count=$((count + 1))
done < <(find "$SRC" -name "*.md" -not -path "*/research/transcripts/*")

while IFS= read -r f; do
  rel="${f#"$DST"/}"
  if [ ! -f "$SRC/$rel" ]; then
    echo "sync_docs_to_obsidian: removing stale note $rel"
    rm "$f"
  fi
done < <(find "$DST" -name "*.md")

echo "sync_docs_to_obsidian: synced $count notes to $DST"
