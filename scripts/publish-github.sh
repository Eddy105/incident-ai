#!/usr/bin/env bash
set -euo pipefail

REPO="Eddy105/incident-ai"

if ! command -v gh >/dev/null 2>&1; then
  echo "error: GitHub CLI (gh) is required for automated repository creation." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "error: gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi

if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "Repository $REPO already exists."
  if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "git@github.com:${REPO}.git"
  fi
else
  gh repo create "$REPO" \
    --public \
    --description "AI-assisted Linux and service incident analysis for DevOps and SRE workflows." \
    --source . \
    --remote origin
fi

git push -u origin main

if git rev-parse -q --verify refs/tags/v0.1.0 >/dev/null; then
  git push origin v0.1.0
fi

echo "Published: https://github.com/$REPO"
