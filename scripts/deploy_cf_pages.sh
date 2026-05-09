#!/usr/bin/env bash
# Deploy foodie-web to Cloudflare Pages project "lamaisonfoodie".
#
# The CF Pages project is in DIRECT UPLOAD mode (not Git-connected),
# so pushing to GitHub does NOT trigger a redeploy. This script must
# be run manually after each push to refresh production.
#
# Reads CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID from ~/.ehads.env.
# Excludes scripts/, .git, *.bak.* and other dev artifacts via .cfignore.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Load credentials
if [[ -f "$HOME/.ehads.env" ]]; then
    # shellcheck disable=SC1091
    source "$HOME/.ehads.env"
fi

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]] || [[ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]]; then
    echo "✗ Missing CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID in ~/.ehads.env" >&2
    exit 1
fi

COMMIT_HASH="$(git rev-parse HEAD)"
COMMIT_MESSAGE="$(git log -1 --format=%s)"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

echo "→ deploying ${COMMIT_HASH:0:7} on branch '${BRANCH}'"
echo "  message: ${COMMIT_MESSAGE}"

CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_TOKEN" \
CLOUDFLARE_ACCOUNT_ID="$CLOUDFLARE_ACCOUNT_ID" \
npx --yes wrangler@4 pages deploy . \
    --project-name=lamaisonfoodie \
    --branch="$BRANCH" \
    --commit-message="$COMMIT_MESSAGE" \
    --commit-hash="$COMMIT_HASH" \
    --commit-dirty=true
