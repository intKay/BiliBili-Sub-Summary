#!/usr/bin/env sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
skill_name="bilibili-video-analysis"

if [ "${1:-}" != "" ]; then
  install_root="$1"
elif [ "${CODEX_HOME:-}" != "" ]; then
  install_root="$CODEX_HOME/skills"
else
  install_root="$HOME/.codex/skills"
fi

target="$install_root/$skill_name"
mkdir -p "$target/scripts"

cp "$repo_root/skills/$skill_name/SKILL.md" "$target/"
cp "$repo_root/skills/$skill_name/PORTABLE_AGENT_PROMPT.md" "$target/"
cp "$repo_root/requirements.txt" "$target/"
cp "$repo_root"/scripts/*.py "$target/scripts/"

printf 'Installed %s to %s\n' "$skill_name" "$target"
printf 'For Python helpers, create a venv and install dependencies from: %s\n' "$target/requirements.txt"
