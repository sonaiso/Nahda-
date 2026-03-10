#!/usr/bin/env bash
set -euo pipefail

OWNER="${1:-sonaiso}"
REPO="${2:-Nahda-}"
BRANCH="${3:-main}"
CHECK_NAME="${4:-CI / quality-gate}"

gh api --method PUT "repos/${OWNER}/${REPO}/branches/${BRANCH}/protection" \
  -H "Accept: application/vnd.github+json" \
  -f required_status_checks.strict=true \
  -f required_status_checks.contexts[]="${CHECK_NAME}" \
  -f enforce_admins=true \
  -f required_pull_request_reviews.dismiss_stale_reviews=true \
  -f required_pull_request_reviews.required_approving_review_count=1 \
  -f required_conversation_resolution=true \
  -F restrictions=

echo "Branch protection applied to ${OWNER}/${REPO}:${BRANCH}"
