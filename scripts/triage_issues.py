#!/usr/bin/env python3
"""Triage GitHub issues by scoring impact, clarity, fix scope, and strategic value."""

import argparse
import json
import re
import subprocess
import sys
import textwrap


HIGH_IMPACT_KEYWORDS = re.compile(
    r"\b(crash|crashes|crashing|data\s*loss|corrupt|blocks|blocked|blocking|"
    r"segfault|panic|deadlock|race\s*condition|regression|security|vulnerability|"
    r"FileNotFoundError|KeyError|TypeError|IndexError|NullPointerException|"
    r"SIGSEGV|OOM|out\s*of\s*memory|hang|freeze|broken)\b",
    re.IGNORECASE,
)
LOW_IMPACT_KEYWORDS = re.compile(
    r"\b(cosmetic|typo|minor|nitpick|trivial|formatting|whitespace|style|"
    r"rename|documentation|docs|readme)\b",
    re.IGNORECASE,
)

CLARITY_PATTERNS = {
    "repro_steps": re.compile(
        r"(steps?\s+to\s+reproduce|repro(duction)?\s+steps?|how\s+to\s+reproduce|"
        r"1\.\s+.+\n\s*2\.\s+)",
        re.IGNORECASE,
    ),
    "error_trace": re.compile(
        r"(Traceback|stack\s*trace|at\s+\S+\.\S+\(|Error:|Exception:|panic:)",
        re.IGNORECASE,
    ),
    "expected_vs_actual": re.compile(
        r"(expected\s+(behavior|result|output)|actual\s+(behavior|result|output))",
        re.IGNORECASE,
    ),
    "proposed_fix": re.compile(
        r"(proposed\s+fix|suggestion|fix\s+would\s+be|could\s+be\s+fixed\s+by|"
        r"root\s+cause|the\s+issue\s+is\s+in)",
        re.IGNORECASE,
    ),
}

FIX_SCOPE_PATTERNS = {
    "file_ref": re.compile(r"\b[\w/]+\.(py|js|ts|go|rs|java|rb|c|cpp|h|yaml|yml|toml)\b"),
    "function_ref": re.compile(r"\b(function|def|func|fn|method)\s+\w+", re.IGNORECASE),
    "line_ref": re.compile(r"(line\s+\d+|L\d+)", re.IGNORECASE),
    "patch": re.compile(r"(```diff|```patch|\+\+\+\s|---\s|@@\s)", re.IGNORECASE),
}


def run_gh(args: list[str]) -> str:
    """Run a gh CLI command and return stdout. Raises SystemExit on failure."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        print("Error: 'gh' CLI is not installed or not on PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Error: gh command timed out.", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        print(f"Error running gh {' '.join(args)}: {stderr}", file=sys.stderr)
        sys.exit(1)

    return result.stdout


def fetch_issues(repo: str, limit: int, label: str | None) -> list[dict]:
    """Fetch open issues from the repository."""
    cmd = [
        "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--limit", str(limit),
        "--json", "number,title,body,labels,reactionGroups,comments,createdAt,url",
    ]
    if label:
        cmd += ["--label", label]

    raw = run_gh(cmd)
    if not raw.strip():
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("Error: failed to parse issue list JSON.", file=sys.stderr)
        sys.exit(1)


def has_competing_pr(repo: str, issue_number: int) -> bool:
    """Check whether an open PR references this issue as a fix."""
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", repo, "--state", "open",
             "--search", f"fixes #{issue_number}",
             "--json", "number", "--limit", "1"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

    if result.returncode != 0:
        return False

    try:
        prs = json.loads(result.stdout)
        return len(prs) > 0
    except (json.JSONDecodeError, TypeError):
        return False


def total_reactions(reaction_groups: list[dict]) -> int:
    """Sum all reaction counts from reactionGroups."""
    total = 0
    for group in reaction_groups or []:
        total += group.get("totalCount", 0)
        # gh sometimes nests users list instead of totalCount
        users = group.get("users", {})
        if isinstance(users, dict):
            total += users.get("totalCount", 0)
        elif isinstance(users, list):
            total += len(users)
    return total


def score_impact(text: str) -> int:
    """Score 1-5 based on severity keywords in title+body."""
    high_hits = len(HIGH_IMPACT_KEYWORDS.findall(text))
    low_hits = len(LOW_IMPACT_KEYWORDS.findall(text))

    if high_hits >= 3:
        return 5
    if high_hits >= 2:
        return 4
    if high_hits >= 1:
        return 3
    if low_hits >= 2:
        return 1
    if low_hits >= 1:
        return 2
    return 2


def score_clarity(text: str) -> int:
    """Score 1-5 based on how well the issue describes the problem."""
    hits = sum(1 for p in CLARITY_PATTERNS.values() if p.search(text))
    return min(hits + 1, 5)


def score_fix_scope(text: str) -> int:
    """Score 1-5 based on how precisely the fix location is identified."""
    hits = sum(1 for p in FIX_SCOPE_PATTERNS.values() if p.search(text))
    return min(hits + 1, 5)


def score_strategic(issue: dict) -> int:
    """Score 1-5 based on labels, reactions, and comments."""
    score = 1
    label_names = [lbl.get("name", "").lower() for lbl in issue.get("labels", [])]

    if "bug" in label_names:
        score += 2
    if any(l in label_names for l in ("critical", "priority", "p0", "p1", "urgent")):
        score += 2
    if any(l in label_names for l in ("enhancement", "feature", "good first issue")):
        score += 1

    reactions = total_reactions(issue.get("reactionGroups", []))
    if reactions >= 10:
        score += 2
    elif reactions >= 3:
        score += 1

    comments = issue.get("comments", [])
    comment_count = len(comments) if isinstance(comments, list) else 0
    if comment_count >= 5:
        score += 1

    return min(score, 5)


def classify(total: int, blocked: bool) -> str:
    """Map total score to a triage category."""
    if blocked:
        return "BLOCKED"
    if total >= 16:
        return "FIX NOW"
    if total >= 12:
        return "GOOD CANDIDATE"
    if total >= 8:
        return "INVESTIGATE FIRST"
    return "SKIP"


def triage(repo: str, limit: int, label: str | None) -> list[dict]:
    """Fetch, score, and rank issues."""
    issues = fetch_issues(repo, limit, label)
    if not issues:
        return []

    results = []
    for issue in issues:
        num = issue["number"]
        title = issue.get("title", "")
        body = issue.get("body", "") or ""
        text = f"{title}\n{body}"

        impact = score_impact(text)
        clarity = score_clarity(text)
        fix_scope = score_fix_scope(text)
        strategic = score_strategic(issue)
        total = impact + clarity + fix_scope + strategic

        blocked = has_competing_pr(repo, num)
        category = classify(total, blocked)

        results.append({
            "number": num,
            "title": title,
            "url": issue.get("url", ""),
            "impact": impact,
            "clarity": clarity,
            "fix_scope": fix_scope,
            "strategic": strategic,
            "total": total,
            "category": category,
            "blocked": blocked,
        })

    results.sort(key=lambda r: r["total"], reverse=True)
    return results


def format_report(results: list[dict], repo: str) -> str:
    """Build a markdown triage report."""
    lines = [
        f"# Issue Triage Report: {repo}",
        "",
        f"**{len(results)} issues scored** | Dimensions: Impact, Clarity, Fix Scope, Strategic Value (each 1-5)",
        "",
        "| # | Title | Impact | Clarity | Scope | Strategic | Total | Category |",
        "|---|-------|--------|---------|-------|-----------|-------|----------|",
    ]

    for r in results:
        short_title = textwrap.shorten(r["title"], width=50, placeholder="...")
        title_cell = f"[{short_title}]({r['url']})" if r["url"] else short_title
        lines.append(
            f"| #{r['number']} | {title_cell} "
            f"| {r['impact']} | {r['clarity']} | {r['fix_scope']} | {r['strategic']} "
            f"| **{r['total']}** | {r['category']} |"
        )

    lines.append("")

    # Summary counts
    categories = {}
    for r in results:
        categories[r["category"]] = categories.get(r["category"], 0) + 1

    lines.append("### Summary")
    for cat in ("FIX NOW", "GOOD CANDIDATE", "INVESTIGATE FIRST", "SKIP", "BLOCKED"):
        count = categories.get(cat, 0)
        if count:
            lines.append(f"- **{cat}**: {count}")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Triage GitHub issues by scoring and ranking them."
    )
    parser.add_argument("--repo", required=True, help="Repository in owner/repo format")
    parser.add_argument("--limit", type=int, default=20, help="Max issues to fetch (default: 20)")
    parser.add_argument("--output", help="Write report to file instead of stdout")
    parser.add_argument("--label", help="Filter issues by label")
    args = parser.parse_args()

    results = triage(args.repo, args.limit, args.label)
    if not results:
        print("No open issues found.", file=sys.stderr)
        sys.exit(0)

    report = format_report(results, args.repo)

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report written to {args.output}")
        except OSError as e:
            print(f"Error writing to {args.output}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(report)


if __name__ == "__main__":
    main()
