# Branch Protection Policy (main)

Apply this policy to `main`:

- Require pull request reviews: 1
- Dismiss stale reviews: true
- Require status checks: true
- Strict status checks: true
- Required checks:
  - `CI / quality-gate`
- Enforce for administrators: true
- Require conversation resolution: true

## Apply With GitHub CLI

```bash
gh api --method PUT repos/<owner>/<repo>/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -f required_status_checks.strict=true \
  -f required_status_checks.contexts[]="CI / quality-gate" \
  -f enforce_admins=true \
  -f required_pull_request_reviews.dismiss_stale_reviews=true \
  -f required_pull_request_reviews.required_approving_review_count=1 \
  -f required_conversation_resolution=true \
  -F restrictions=
```
