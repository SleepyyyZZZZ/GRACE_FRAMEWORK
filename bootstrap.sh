#!/usr/bin/env bash
# GRACE Framework bootstrapper (POSIX).
# Pulls the clean framework from GitHub and copies it into a target repository
# without touching the target's .git, README.md or the framework's own bootstrap files.
#
# Usage:
#   ./bootstrap.sh [TARGET_DIR]                 # default TARGET_DIR = current directory
#   curl -fsSL .../bootstrap.sh | bash          # bootstrap the current directory
#   GRACE_REF=main GRACE_FORCE=1 ./bootstrap.sh ../my-project
#
# Env:
#   GRACE_REPO   override source repo URL (default: SleepyyyZZZZ/GRACE_FRAMEWORK)
#   GRACE_REF    branch/tag/commit to pull (default: main)
#   GRACE_FORCE  if set to 1, overwrite existing framework files in the target
set -euo pipefail

REPO="${GRACE_REPO:-https://github.com/SleepyyyZZZZ/GRACE_FRAMEWORK.git}"
REF="${GRACE_REF:-main}"
TARGET="${1:-.}"
FORCE="${GRACE_FORCE:-0}"

# Files/dirs that belong to the framework repository itself, not to a consuming project.
EXCLUDES=(".git" "README.md" "bootstrap.sh" "bootstrap.ps1")

command -v git >/dev/null 2>&1 || { echo "[GRACE] git is required" >&2; exit 1; }
mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[GRACE] Cloning $REPO@$REF ..."
git clone --quiet --depth 1 --branch "$REF" "$REPO" "$TMP/grace" 2>/dev/null \
  || git clone --quiet --depth 1 "$REPO" "$TMP/grace"

build_rsync_excludes() {
  for e in "${EXCLUDES[@]}"; do printf -- "--exclude=%s " "$e"; done
}

echo "[GRACE] Installing framework into: $TARGET"
if command -v rsync >/dev/null 2>&1; then
  # shellcheck disable=SC2046
  if [ "$FORCE" = "1" ]; then
    rsync -a $(build_rsync_excludes) "$TMP/grace/" "$TARGET/"
  else
    rsync -a --ignore-existing $(build_rsync_excludes) "$TMP/grace/" "$TARGET/"
  fi
else
  # Fallback copy without rsync.
  ( cd "$TMP/grace"
    find . -path ./.git -prune -o -type f -print | while IFS= read -r f; do
      rel="${f#./}"
      case "$rel" in
        README.md|bootstrap.sh|bootstrap.ps1) continue ;;
      esac
      dest="$TARGET/$rel"
      if [ "$FORCE" != "1" ] && [ -e "$dest" ]; then
        echo "[GRACE] skip (exists): $rel"; continue
      fi
      mkdir -p "$(dirname "$dest")"
      cp -p "$f" "$dest"
    done )
fi

echo "[GRACE] Done. Open CLAUDE.md / AGENTS.md / GEMINI.md and start working."
echo "[GRACE] Next: pip install -r requirements.txt && python tools/check_semantics.py"
