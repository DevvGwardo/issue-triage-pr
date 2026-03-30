---
name: issue-triage-pr
description: Triage GitHub issues by severity, investigate root causes, fix bugs, and open pull requests — full autonomous issue-to-PR pipeline.
version: 1.0.0
author: devgwardo
license: MIT
metadata:
  hermes:
    tags: [GitHub, Issues, Triage, Pull-Requests, Bug-Fixing, Automation, CI/CD]
    related_skills: [github-issues, github-pr-workflow, github-auth, github-code-review, codebase-inspection, systematic-debugging, test-driven-development]
---

# Issue Triage → Fix → PR Pipeline

Autonomous workflow for triaging GitHub issues, selecting impactful bugs, investigating root causes, applying fixes, and opening pull requests — all following the target repository's contributing conventions.

## The Iron Law

> **NO PR WITHOUT UNDERSTANDING THE ROOT CAUSE FIRST.**
> Triage is not "pick the easiest issue." Triage is "find the highest-impact fixable issue and prove you understand why it's broken before touching the code."

## Autonomy Model

This skill runs **fully autonomously** — no human approval gates. Instead, the agent
self-validates at each phase using confidence checks. If confidence is insufficient,
the agent **does not ask the user** — it skips to the next candidate or aborts with
a clear explanation of why it couldn't proceed.

**Self-validation principle:** At each decision point, the agent must be able to answer
these questions affirmatively before proceeding:

1. **Can I state the root cause in one sentence?** (not "something is wrong" — the *specific* reason)
2. **Can I name the exact file(s) and function(s) that need changing?**
3. **Can I describe the fix without hand-waving?** (not "add error handling" — the *exact* change)
4. **Can I explain why this fix won't break anything else?**

If any answer is "no", the agent either investigates deeper or moves to the next issue.
It never guesses and never asks the user to fill in gaps it should resolve itself.

## Overview

This skill operates in **six phases**, flowing continuously without user interaction:

1. **FETCH** — Pull open issues from a GitHub repository
2. **TRIAGE** — Score and rank issues by severity, impact, and fix clarity
3. **INVESTIGATE** — Deep-dive the top candidate: read source, trace the bug, identify root cause. If root cause can't be determined, automatically fall back to the next candidate.
4. **FIX** — Create branch, apply minimal correct fix, run tests
5. **PR** — Open a pull request following the repo's contributing conventions
6. **FOLLOW-UP** — Comment on the issue, link the PR, report summary

---

## When to Use

- User asks to "find bugs to fix" or "triage issues" in a GitHub repo
- User asks to "contribute to" an open-source project
- User asks to "fix an issue and open a PR"
- User provides a GitHub repo URL and wants automated bug fixing
- User wants to triage a backlog of issues and prioritize them
- User asks to "pick an issue and submit a fix"

## When NOT to Use

- User wants to discuss architecture or design (not a bug fix workflow)
- The repo has no open issues
- User wants to create issues, not fix them (use `github-issues` skill instead)
- The fix requires multi-week effort or cross-team coordination

## Execution Mode

This skill runs **end-to-end without stopping for approval**. The agent:
- Selects the best issue autonomously based on scoring
- Falls back to the next candidate if investigation hits a dead end
- Self-validates root cause understanding before writing any code
- Only reports back to the user when the pipeline completes (PR opened) or
  when no actionable issue could be found (with explanation of why each was skipped)

---

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- `gh` CLI installed and authenticated (`gh auth status`)
- `git` installed
- Write access to fork the repo (or push access to the repo itself)

### Setup

```bash
# Verify auth
gh auth status

# Determine working mode
if gh auth status 2>&1 | grep -q "Logged in"; then
  echo "✓ GitHub CLI authenticated"
else
  echo "✗ Run: gh auth login"
  exit 1
fi
```

---

## Phase 1: FETCH

Pull the latest open issues from the target repository.

### Inputs

- `REPO` — GitHub repository in `owner/repo` format (e.g., `NousResearch/hermes-agent`)
- `LIMIT` — Number of issues to fetch (default: 20)
- `FILTER` — Optional: `bug`, `enhancement`, `all` (default: `all`)

### Procedure

```bash
# Fetch issues with full metadata
gh issue list \
  --repo "$REPO" \
  --limit "$LIMIT" \
  --state open \
  --json number,title,labels,createdAt,author,body,comments,reactions,assignees

# If filtering by label:
gh issue list \
  --repo "$REPO" \
  --limit "$LIMIT" \
  --state open \
  --label "bug" \
  --json number,title,labels,createdAt,author,body,comments,reactions,assignees
```

### Completion Criteria

- [ ] Issues fetched successfully
- [ ] Issue data includes: number, title, body, labels, author, creation date
- [ ] Present issue list to user in summary table format

---

## Phase 2: TRIAGE

Score and rank each issue using the severity matrix. The goal is to identify the **single best bug to fix** — highest impact with clearest path to resolution.

### Severity Scoring Matrix

Each issue is scored on four dimensions (1-5 each, max 20):

| Dimension | 1 (Low) | 3 (Medium) | 5 (High) |
|-----------|---------|------------|----------|
| **Impact** | Cosmetic, edge case | Affects common workflow | Crash, data loss, blocks users |
| **Clarity** | Vague report, no repro steps | Partial info, needs investigation | Full repro, root cause identified |
| **Fix Scope** | Architecture change needed | Multi-file, moderate complexity | 1-3 files, clear patch |
| **Strategic Value** | Niche use case | Moderate user base affected | Core feature, many users, contributor priority |

### Scoring Procedure

For each fetched issue:

1. **Read the full issue body** — understand what's reported
2. **Check for labels** — `bug` label confirms it's a bug; missing labels need classification
3. **Assess impact** — Does it crash? Block users? Lose data? Or just cosmetic?
4. **Assess clarity** — Does the reporter include reproduction steps? Error traces? Root cause analysis? Proposed fix?
5. **Assess fix scope** — How many files would need changing? Is the fix isolated?
6. **Assess strategic value** — Does it align with the repo's contributing priorities? Does it affect cross-platform compatibility?
7. **Check for competing PRs** — Skip issues where someone already submitted a fix

```bash
# Check if an issue already has a linked PR
gh pr list --repo "$REPO" --search "fixes #$ISSUE_NUM OR closes #$ISSUE_NUM" --json number,title,state
```

### Triage Output Format

Present results as a ranked table:

```
## Triage Report — $REPO

| Rank | Issue | Title | Impact | Clarity | Scope | Strategic | Total | Recommendation |
|------|-------|-------|--------|---------|-------|-----------|-------|----------------|
| 1    | #NNN  | ...   | 5      | 5       | 4     | 5         | 19    | FIX NOW        |
| 2    | #NNN  | ...   | 4      | 4       | 4     | 4         | 16    | GOOD CANDIDATE |
| ...  |       |       |        |         |       |           |       |                |
```

Recommendation categories:
- **FIX NOW** (16-20): High impact, clear fix, strong strategic value
- **GOOD CANDIDATE** (12-15): Solid fix opportunity, some investigation needed
- **INVESTIGATE FIRST** (8-11): Promising but unclear scope or root cause
- **SKIP** (1-7): Vague, low impact, or requires architecture changes
- **BLOCKED** — Already has a competing PR or the author is working on it

### Automated Triage (Optional)

For batch scoring, use the helper script:

```bash
python3 ~/.hermes/skills/github/issue-triage-pr/scripts/triage_issues.py \
  --repo "$REPO" \
  --limit 20
```

### Completion Criteria

- [ ] All fetched issues scored on 4 dimensions
- [ ] Issues ranked by total score
- [ ] Top candidate identified with justification
- [ ] No competing PR exists for the top candidate
- [ ] Candidate queue built (ranked list to fall back through if top pick fails investigation)

### Auto-Selection Logic

Work through the ranked list top-down. For each candidate, apply these **gate checks**
before committing to investigate:

1. **Not BLOCKED** — no competing open PR
2. **Not claimed** — issue author hasn't said "I'd like to fix this myself"
3. **Minimum clarity** — has at least an error trace OR reproduction steps OR a proposed fix
4. **Not contentious** — no long unresolved design debate in comments
5. **Not security-critical** — doesn't touch auth, crypto, or secret handling (unless the fix is trivially safe, e.g., adding a null check)

If a candidate fails any gate, skip it silently and try the next one. If all candidates
fail, report the triage results and explain why none were actionable.

### Red Flags — Auto-Skip to Next Candidate

- The top issue has no reproduction steps AND no error trace → skip, try next
- The issue author says "I'd like to fix this myself" → respect their intent, skip
- The issue has been open for months with active unresolved debate → contentious, skip
- The fix would touch security-critical code paths → skip unless fix is trivially safe

---

## Phase 3: INVESTIGATE

Deep-dive the selected issue. Understand the root cause before writing any code.

### 3.1 — Read Contributing Guidelines and Agent Instructions

**Always check the repo's contributing conventions AND AI-agent instruction files first.** These determine branch naming, commit format, test requirements, PR template, architecture boundaries, coding style, and rules that AI agents must follow.

```bash
# Clone the repo (or navigate to existing clone)
gh repo clone "$REPO" /tmp/triage-work/"$REPO_NAME" -- --depth=50
cd /tmp/triage-work/"$REPO_NAME"

# Read contributing guidelines
for f in CONTRIBUTING.md CONTRIBUTING .github/CONTRIBUTING.md DEVELOPMENT.md docs/contributing.md; do
  if [ -f "$f" ]; then
    echo "=== Found: $f ==="
    cat "$f"
  fi
done

# Read AI-agent instruction files — these contain project-specific rules
# that override default behavior (architecture boundaries, import rules,
# build gates, coding style, naming conventions, etc.)
for f in AGENTS.md CLAUDE.md .cursorrules .github/copilot-instructions.md .windsurfrules .clinerules CONVENTIONS.md; do
  if [ -f "$f" ]; then
    echo "=== Found agent instructions: $f ==="
    cat "$f"
  fi
done

# Check for nested AGENTS.md files (some repos use per-directory agent guides)
find . -name "AGENTS.md" -not -path "./.git/*" -maxdepth 3 2>/dev/null

# Check for PR templates
ls -la .github/PULL_REQUEST_TEMPLATE* .github/pull_request_template* 2>/dev/null
ls -la .github/ISSUE_TEMPLATE/ 2>/dev/null
```

Extract and record:
- [ ] Branch naming convention (e.g., `fix/description`, `bugfix/issue-NNN`)
- [ ] Commit message format (e.g., Conventional Commits)
- [ ] Required tests before submitting
- [ ] PR description template or required sections
- [ ] Any CI/linting requirements
- [ ] Code style preferences
- [ ] Architecture boundaries and import rules (from AGENTS.md / CLAUDE.md)
- [ ] Build/test/lint gate commands (from agent instructions)
- [ ] File ownership or restricted paths (e.g., CODEOWNERS rules)
- [ ] Naming conventions and terminology rules

### 3.2 — Extract Conventions Automatically

```bash
python3 ~/.hermes/skills/github/issue-triage-pr/scripts/extract_conventions.py \
  --repo-dir /tmp/triage-work/"$REPO_NAME"
```

### 3.3 — Trace the Bug

Follow the error path described in the issue:

1. **Read the error trace** — identify the file and line number where the crash occurs
2. **Read the source file** — understand the surrounding code context
3. **Trace backwards** — find where the bad state originates
4. **Read related tests** — understand what's currently tested
5. **Check git blame** — understand when and why the current code was written

```bash
# If the issue includes a traceback, find the file
# Example: "File gateway.py, line 42, in start_gateway"
cat gateway.py

# Check git history for context
git log --oneline -10 -- gateway.py
git blame -L 35,50 gateway.py
```

### 3.4 — Formulate and Self-Validate Root Cause

Before writing any fix, articulate:

1. **What's broken** — the specific behavior that's wrong
2. **Why it's broken** — the root cause (not just the symptom)
3. **What the fix should do** — the minimal change that corrects the behavior
4. **What could go wrong** — potential regressions from the fix
5. **How to verify** — test(s) that confirm the fix works

### 3.5 — Confidence Gate (Self-Validation)

Before proceeding to Phase 4, pass ALL of these checks internally:

| Check | Pass Condition | Fail Action |
|-------|---------------|-------------|
| **Root cause is specific** | Can state it in one sentence naming the exact file, function, and defect | Investigate deeper — read more code, trace further |
| **Fix is concrete** | Can describe the exact code change (not "add error handling" — the specific lines) | Read more surrounding code until the change is clear |
| **Files are identified** | Know every file that needs modification | Search the codebase for all references to the broken path |
| **Regression risk is bounded** | Can explain why the fix won't break other callers/paths | Read callers, check tests, trace impact |
| **Fix is within scope** | Change is <50 lines across ≤3 files | If larger, this issue is too complex — **fall back to next candidate** |

**If any check fails after reasonable investigation (3+ attempts to resolve it),
do not ask the user.** Fall back to the next ranked issue and restart from Phase 3.
Log why the candidate was dropped:

```
Skipped #NNN: Could not determine root cause — error trace points to
third-party dependency (requests library), not project code.
Falling back to #NNN (next candidate).
```

### Completion Criteria

- [ ] Contributing guidelines and agent instructions read and conventions extracted
- [ ] Source code at the crash/bug site read and understood
- [ ] Root cause articulated as a specific, one-sentence statement
- [ ] Fix approach described as concrete code changes (files, functions, exact modifications)
- [ ] Potential regressions identified and bounded
- [ ] All 5 confidence gate checks passed

### Red Flags — Auto-Fallback to Next Candidate

- Can't identify root cause after reading the source → fall back to next candidate
- Root cause is in a dependency, not the project itself → fall back, note in skip log
- Fix requires changing a public API → too risky for autonomous fix, fall back
- Multiple bugs are tangled together → fix only the one reported if separable, otherwise fall back
- Fix would exceed 50 lines or touch >3 files → scope too large, fall back

---

## Phase 4: FIX

Apply the minimal correct fix. Follow the repository's conventions exactly.

### 4.1 — Create Branch

```bash
# Ensure we're on the latest default branch
DEFAULT_BRANCH=$(gh repo view "$REPO" --json defaultBranchRef --jq '.defaultBranchRef.name')
git checkout "$DEFAULT_BRANCH"
git pull origin "$DEFAULT_BRANCH"

# Create fix branch following repo conventions
# Common patterns:
git checkout -b "fix/$DESCRIPTION"              # Conventional Commits style
git checkout -b "fix/issue-$ISSUE_NUM-$SLUG"    # Issue-referenced style
git checkout -b "bugfix/$DESCRIPTION"            # Alternative style
```

### 4.2 — Apply the Fix

Rules for the fix:
- **Minimal** — change only what's necessary to fix the bug
- **Correct** — fix the root cause, not the symptom
- **Safe** — don't introduce new bugs or security issues
- **Consistent** — follow the repo's code style exactly
- **Documented** — add a code comment only if the fix is non-obvious

**Do NOT:**
- Refactor surrounding code
- Add unrelated improvements
- Change formatting of untouched lines
- Add type annotations to existing code
- "Clean up" imports or comments

### 4.3 — Run Tests

```bash
# Find and run the test suite
# Common patterns:
pytest tests/ -v                           # Python
npm test                                   # Node.js
go test ./...                              # Go
cargo test                                 # Rust
make test                                  # Makefile-based

# Run only tests related to the changed files
pytest tests/ -v -k "test_gateway" --no-header

# Check for linting requirements
# Common patterns:
ruff check .                               # Python (ruff)
flake8 .                                   # Python (flake8)
npm run lint                               # Node.js
```

### 4.4 — Commit

Follow the repo's commit message convention exactly. If none is specified, use Conventional Commits:

```bash
git add <changed-files>
git commit -m "fix(<scope>): <description>

<Root cause explanation — 1-2 sentences>

Fixes #$ISSUE_NUM"
```

**Never commit:**
- Unrelated file changes
- IDE config files (.vscode/, .idea/)
- OS files (.DS_Store, Thumbs.db)
- Environment files (.env, credentials)

### Completion Criteria

- [ ] Branch created from latest default branch
- [ ] Fix applied — minimal, correct, safe
- [ ] All existing tests pass
- [ ] New regression test added (if applicable and conventions require it)
- [ ] Commit message follows repo conventions
- [ ] Commit references the issue number

### Red Flags — STOP

- Tests fail that aren't related to your change → investigate, don't skip
- The fix is more than ~50 lines → reassess scope, might be too large
- You need to change more than 3 files → likely architecture issue, flag to user
- You're adding a dependency → almost certainly wrong for a bug fix

---

## Phase 5: PR

Open a pull request following the repository's conventions.

### 5.1 — Fork (if needed)

```bash
# Check if you have push access
if ! git push --dry-run origin HEAD 2>/dev/null; then
  # Fork the repo
  gh repo fork "$REPO" --clone=false
  FORK_REMOTE=$(gh api user --jq '.login')
  git remote add fork "https://github.com/$FORK_REMOTE/$REPO_NAME.git"
  PUSH_REMOTE="fork"
else
  PUSH_REMOTE="origin"
fi
```

### 5.2 — Push

```bash
git push -u "$PUSH_REMOTE" "$(git branch --show-current)"
```

### 5.3 — Create PR

Use the repo's PR template if one exists. Otherwise, use this format:

```bash
gh pr create \
  --repo "$REPO" \
  --title "fix(<scope>): <concise description>" \
  --body "$(cat <<'EOF'
## Summary

<1-3 bullet points describing what this PR does>

- Fixes the root cause of #ISSUE_NUM
- <What was wrong>
- <What the fix does>

## Root Cause

<2-3 sentences explaining why the bug existed>

## Fix

<Description of the change>

- `file.py`: <what changed and why>

## How to Verify

1. <Step to reproduce the original bug>
2. <Step showing the fix works>
3. <Step confirming no regressions>

## Test Plan

- [ ] Existing tests pass
- [ ] New regression test added (if applicable)
- [ ] Manual verification of the fix
- [ ] Tested on: <platform(s)>

## Risk Assessment

Low / Medium / High — <explanation of blast radius>

Fixes #ISSUE_NUM
EOF
)"
```

### 5.4 — Verify CI

After opening the PR, monitor CI:

```bash
# Watch CI status
gh pr checks --repo "$REPO" --watch

# If CI fails, investigate and fix
gh pr checks --repo "$REPO" --json name,state,conclusion
```

If CI fails:
1. Read the failure log
2. Fix the issue
3. Push a new commit (do NOT force-push)
4. Re-check CI

### Completion Criteria

- [ ] PR opened with proper title and body
- [ ] PR references the issue with `Fixes #NNN`
- [ ] PR follows the repo's template/conventions
- [ ] CI passes (or known-flaky tests documented)
- [ ] PR URL returned to user

---

## Phase 6: FOLLOW-UP

### 6.1 — Comment on the Issue

```bash
gh issue comment "$ISSUE_NUM" \
  --repo "$REPO" \
  --body "I've investigated this and opened a fix: #PR_NUM

**Root cause:** <brief explanation>
**Fix:** <brief description of the change>

Happy to address any review feedback."
```

### 6.2 — Clean Up

```bash
# Remove temporary clone if used
rm -rf /tmp/triage-work/"$REPO_NAME"
```

### 6.3 — Report to User

Provide a summary:

```
## Issue Fix Summary

- **Issue:** #NNN — <title>
- **Root Cause:** <explanation>
- **Fix:** <description>
- **PR:** <URL>
- **CI Status:** passing/pending/failing
- **Next Steps:** Await review from maintainers
```

### Completion Criteria

- [ ] Issue comment posted linking to PR
- [ ] User has PR URL
- [ ] Temporary files cleaned up
- [ ] Summary provided

---

## Common Rationalizations (and Why They're Wrong)

| Rationalization | Reality |
|----------------|---------|
| "I'll just fix the obvious thing without reading CONTRIBUTING" | Every repo has conventions. Ignoring them guarantees review friction or rejection. |
| "I'll also read AGENTS.md later, CONTRIBUTING is enough" | Agent instruction files contain architecture boundaries, import rules, and restricted paths. Skipping them means violating project structure. |
| "This issue is probably easy, I don't need to trace the code" | Easy-looking issues often have subtle root causes. Investigate first. |
| "I'll also clean up the surrounding code while I'm here" | Scope creep kills PRs. Fix the bug, nothing more. |
| "The tests pass locally so it's fine" | CI may have different configs, Python versions, or OS. Wait for CI. |
| "I'll skip the regression test since the fix is obvious" | Obvious fixes break in obvious ways when someone refactors later. Add the test. |
| "I'll force-push to clean up the history" | Maintainers may have already reviewed. Never force-push after opening a PR. |
| "This vague issue is probably about X" | Don't guess. If the issue is unclear, **skip it and move to the next candidate**. Never guess root cause. |
| "I'm not sure about the root cause but I'll try a fix anyway" | This is the #1 cause of rejected PRs. If you can't state the root cause in one sentence, you don't understand it. Fall back to the next issue. |
| "I should ask the user what they think" | You have the codebase, the issue, the error trace, and the contributing docs. Investigate deeper instead of asking. Only report back when done or when all candidates are exhausted. |

---

## Quick Reference

| Phase | Key Action | Tool |
|-------|-----------|------|
| FETCH | `gh issue list --repo REPO --limit 20 --json ...` | terminal |
| TRIAGE | Score on Impact/Clarity/Scope/Strategic (1-5 each) | reasoning |
| INVESTIGATE | Read CONTRIBUTING.md, trace error, formulate hypothesis | read_file, terminal |
| FIX | Branch, minimal fix, tests, commit | terminal, write_file |
| PR | Push, `gh pr create`, monitor CI | terminal |
| FOLLOW-UP | Comment on issue, report to user | terminal |

---

## Integration with Other Skills

### With `github-auth`

If `gh auth status` fails, load the `github-auth` skill first to set up authentication.

### With `github-code-review`

After opening the PR, use `github-code-review` to self-review the diff before requesting maintainer review.

### With `systematic-debugging`

If the bug trace is complex, load `systematic-debugging` for structured root cause analysis.

### With `test-driven-development`

If the repo requires regression tests, use `test-driven-development` to write a failing test first, then fix it.

### With `codebase-inspection`

For unfamiliar repos, load `codebase-inspection` to understand the project structure before diving into specific files.

### With `delegate_task`

For large triage batches, use `delegate_task` to parallelize issue analysis:

```
Spawn subagents to:
1. Read and score issues in parallel (batch of 5 per subagent)
2. Each subagent returns structured scoring JSON
3. Main agent aggregates scores and produces final ranking
```

---

## Batch Triage Mode

When triaging many issues without fixing them, run the triage script and output a report:

```bash
python3 ~/.hermes/skills/github/issue-triage-pr/scripts/triage_issues.py \
  --repo "$REPO" \
  --limit 50 \
  --output /tmp/triage-report.md
```

This produces a markdown report using the `templates/triage-report.md` template.

---

## Pitfalls

1. **Rate limits** — GitHub API has rate limits (5000/hour authenticated). For large repos with hundreds of issues, paginate carefully.
2. **Stale issues** — Issues open for months may be outdated. Check if the code has changed since the report.
3. **Duplicate fixes** — Always check for existing PRs before starting work. Someone may have fixed it in an unlinked PR.
4. **Fork vs direct push** — Open-source repos usually require forking. Check push access first.
5. **Protected branches** — Default branch may be protected. Always create a feature branch.
6. **CLA/DCO** — Some repos require Contributor License Agreements or Developer Certificate of Origin sign-off. Check CONTRIBUTING.md.
7. **Issue templates** — If the repo uses issue templates and the report doesn't follow them, the issue may be incomplete.

---

## Verification

After the full pipeline completes, verify:

- [ ] The PR is visible on GitHub and references the correct issue
- [ ] CI is green (or all failures are pre-existing/flaky)
- [ ] The issue has a comment linking to the PR
- [ ] The fix addresses the root cause described in the issue
- [ ] No unrelated changes are included in the diff
- [ ] The commit message follows the repo's conventions
- [ ] The branch name follows the repo's conventions
