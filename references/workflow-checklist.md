# Issue Triage → PR Workflow Checklist

Use this checklist to track progress through the full pipeline.

---

## Phase 1: FETCH

- [ ] Target repo identified (`owner/repo` format)
- [ ] `gh` CLI authenticated
- [ ] Issues fetched with `gh issue list --json ...`
- [ ] Issue data includes body, labels, reactions, assignees

## Phase 2: TRIAGE

- [ ] Each issue scored on Impact (1-5)
- [ ] Each issue scored on Clarity (1-5)
- [ ] Each issue scored on Fix Scope (1-5)
- [ ] Each issue scored on Strategic Value (1-5)
- [ ] Checked for competing PRs on top candidates
- [ ] Triage report generated with rankings
- [ ] Top candidate selected with justification
- [ ] Candidate queue built (fallback list if top pick fails)
- [ ] Auto-selection gate checks passed (not blocked, not claimed, minimum clarity)

## Phase 3: INVESTIGATE

### 3a: Conventions & Agent Instructions
- [ ] Repo cloned or navigated to
- [ ] CONTRIBUTING.md read
- [ ] AI agent instruction files scanned (AGENTS.md, CLAUDE.md, .cursorrules, etc.)
- [ ] Nested AGENTS.md files checked (per-directory guides)
- [ ] Architecture boundaries and import rules noted
- [ ] Restricted paths / CODEOWNERS rules noted
- [ ] Coding style and naming conventions noted
- [ ] Branch naming convention noted
- [ ] Commit message format noted
- [ ] Test command identified
- [ ] Lint requirements identified
- [ ] Build gate commands identified (from agent instructions)
- [ ] PR template found (if exists)
- [ ] CLA/DCO requirements checked

### 3b: Root Cause
- [ ] Error trace from issue located in source code
- [ ] Surrounding code context understood
- [ ] Git blame reviewed for relevant lines
- [ ] Related tests identified and read
- [ ] Root cause stated as specific one-sentence statement
- [ ] Fix described as concrete code changes (files, functions, exact modifications)
- [ ] Potential regressions identified and bounded
- [ ] Confidence gate passed (all 5 self-validation checks)
- [ ] If confidence gate failed → fell back to next candidate
- [ ] Fix approach documented for user review
- [ ] User approved fix approach

## Phase 4: FIX

- [ ] Default branch is up to date (`git pull`)
- [ ] Fix branch created with correct naming convention
- [ ] Fix applied — minimal changes only
- [ ] Code follows repo's style conventions
- [ ] No unrelated changes in the diff
- [ ] Tests pass locally
- [ ] Regression test added (if repo requires it)
- [ ] Commit message follows repo conventions
- [ ] Commit message references issue number (`Fixes #NNN`)

## Phase 5: PR

- [ ] Fork created (if no push access)
- [ ] Branch pushed to remote
- [ ] PR created with proper title format
- [ ] PR body includes: summary, root cause, fix, verification steps, test plan
- [ ] PR body includes `Fixes #NNN`
- [ ] CI status checked
- [ ] CI passes (or known flaky tests documented)
- [ ] PR URL recorded

## Phase 6: FOLLOW-UP

- [ ] Comment posted on the original issue linking to PR
- [ ] Temporary files cleaned up
- [ ] Summary report provided to user
- [ ] PR URL shared with user

---

## Post-Submission

- [ ] Monitor for review comments (check back in 24-48h)
- [ ] Address reviewer feedback promptly
- [ ] Do NOT force-push after review starts
- [ ] If changes requested, push new commits (not amendments)
