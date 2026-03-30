#!/usr/bin/env python3
"""Extract repository contributing conventions and output a structured markdown summary."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


def read_file(path: Path) -> str | None:
    """Read a file and return its contents, or None if it doesn't exist."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, IsADirectoryError):
        return None


def find_contributing_docs(repo: Path) -> dict[str, str]:
    """Locate and read all contributing-related documents."""
    candidates = [
        "CONTRIBUTING.md",
        "CONTRIBUTING",
        ".github/CONTRIBUTING.md",
        "DEVELOPMENT.md",
        "docs/contributing.md",
        "docs/CONTRIBUTING.md",
    ]
    found: dict[str, str] = {}
    for name in candidates:
        content = read_file(repo / name)
        if content:
            found[name] = content
    return found


def find_agent_instructions(repo: Path) -> dict[str, str]:
    """Locate and read AI-agent instruction files (AGENTS.md, CLAUDE.md, etc.).

    These files contain project-specific rules for AI agents: architecture
    boundaries, import rules, build gates, coding style, naming conventions,
    restricted paths, and other constraints that override default behavior.
    """
    # Root-level agent instruction files
    root_candidates = [
        "AGENTS.md",
        "CLAUDE.md",
        ".cursorrules",
        ".github/copilot-instructions.md",
        ".windsurfrules",
        ".clinerules",
        "CONVENTIONS.md",
    ]
    found: dict[str, str] = {}
    for name in root_candidates:
        content = read_file(repo / name)
        if content:
            found[name] = content

    # Scan for nested AGENTS.md files (some repos use per-directory guides)
    try:
        for agents_file in repo.rglob("AGENTS.md"):
            rel = str(agents_file.relative_to(repo))
            if rel.startswith(".git"):
                continue
            # Limit depth to avoid crawling deep into node_modules etc.
            if rel.count(os.sep) > 3:
                continue
            if rel not in found:
                content = read_file(agents_file)
                if content:
                    found[rel] = content
    except OSError:
        pass

    return found


def extract_agent_conventions(texts: dict[str, str]) -> dict[str, list[str]]:
    """Extract structured conventions from agent instruction files."""
    result: dict[str, list[str]] = {
        "architecture_boundaries": [],
        "build_gates": [],
        "coding_style": [],
        "restricted_paths": [],
        "naming_conventions": [],
        "import_rules": [],
    }

    all_text = "\n".join(texts.values())

    # Architecture boundaries
    boundary_patterns = [
        r"(?i)(?:architecture|module|import)\s+boundar(?:y|ies)[^\n]*",
        r"(?i)rule:\s+[^\n]+",
        r"(?i)do\s+not\s+import\s+[^\n]+",
    ]
    for pattern in boundary_patterns:
        for match in re.finditer(pattern, all_text):
            line = match.group(0).strip()
            if line and line not in result["architecture_boundaries"]:
                result["architecture_boundaries"].append(line)

    # Build gates / verification commands
    gate_patterns = [
        r"(?i)(?:build|test|lint|format|type[- ]?check)\s+(?:gate|command|step)[^\n]*:\s*`([^`]+)`",
        r"(?i)(?:pnpm|npm|yarn|bun|cargo|make|pytest|go)\s+(?:test|check|build|lint|format)[^\s]*",
    ]
    for pattern in gate_patterns:
        for match in re.finditer(pattern, all_text):
            cmd = match.group(0).strip()
            if cmd and cmd not in result["build_gates"]:
                result["build_gates"].append(cmd)

    # Coding style rules
    style_patterns = [
        r"(?i)(?:prefer|avoid|never|always|do not)\s+(?:use\s+)?`?(?:any|unknown|strict|ESM|CommonJS)[^\n]*",
        r"(?i)formatting.*(?:via|using|with)\s+\w+",
        r"(?i)never\s+add\s+[^\n]+",
    ]
    for pattern in style_patterns:
        for match in re.finditer(pattern, all_text):
            rule = match.group(0).strip()
            if rule and len(rule) > 10 and rule not in result["coding_style"]:
                result["coding_style"].append(rule)

    # Restricted paths / CODEOWNERS
    restricted_patterns = [
        r"(?i)(?:do not edit|restricted|codeowners)[^\n]*",
        r"(?i)treat\s+(?:those|these)\s+paths\s+as\s+restricted[^\n]*",
    ]
    for pattern in restricted_patterns:
        for match in re.finditer(pattern, all_text):
            rule = match.group(0).strip()
            if rule and rule not in result["restricted_paths"]:
                result["restricted_paths"].append(rule)

    # Naming conventions
    naming_patterns = [
        r"(?i)nomenclature:\s+[^\n]+",
        r"(?i)(?:naming|terminology)\s+(?:convention|rule|pattern)[^\n]*",
        r"(?i)use\s+[\"'][\w-]+[\"']\s+(?:in\s+)?(?:docs|UI|code)[^\n]*",
    ]
    for pattern in naming_patterns:
        for match in re.finditer(pattern, all_text):
            rule = match.group(0).strip()
            if rule and rule not in result["naming_conventions"]:
                result["naming_conventions"].append(rule)

    # Import rules
    import_patterns = [
        r"(?i)import\s+boundar(?:y|ies)[^\n]*",
        r"(?i)(?:must|should|must not|should not)\s+import\s+[^\n]+",
        r"(?i)(?:extensions?|plugins?)\s+must\s+(?:cross|import|use)[^\n]+",
    ]
    for pattern in import_patterns:
        for match in re.finditer(pattern, all_text):
            rule = match.group(0).strip()
            if rule and rule not in result["import_rules"]:
                result["import_rules"].append(rule)

    # Filter out empty categories
    return {k: v for k, v in result.items() if v}


def find_pr_template(repo: Path) -> str | None:
    """Locate and read the pull request template."""
    candidates = [
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/pull_request_template.md",
        "PULL_REQUEST_TEMPLATE.md",
        "pull_request_template.md",
        ".github/PULL_REQUEST_TEMPLATE/pull_request_template.md",
    ]
    for name in candidates:
        content = read_file(repo / name)
        if content:
            return content
    return None


def find_issue_templates(repo: Path) -> list[str]:
    """List issue template filenames."""
    template_dir = repo / ".github" / "ISSUE_TEMPLATE"
    if not template_dir.is_dir():
        return []
    return sorted(f.name for f in template_dir.iterdir() if f.is_file())


def extract_branch_convention(text: str) -> str | None:
    """Try to extract branch naming conventions from contributing docs."""
    patterns = [
        r"(?i)branch(?:ing)?\s+(?:naming\s+)?(?:convention|strategy|format|pattern|rule)[s]?\s*[:\-—]\s*(.+)",
        r"(?i)(?:name|create)\s+(?:your\s+)?branch(?:es)?\s+(?:like|as|using|with)\s+[`\"]?([a-z]+/[a-z\-<>{}]+)[`\"]?",
        r"(?i)branch\s+(?:should|must)\s+(?:be\s+)?(?:named|formatted)\s+(?:as\s+)?[`\"]?([a-z]+/[^\s`\"]+)[`\"]?",
        r"(?i)(?:feature|bugfix|hotfix|fix|chore)/[\w<>\-{}\[\]]+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()

    # Look for branch-related paragraphs
    for line in text.splitlines():
        lower = line.lower()
        if "branch" in lower and any(
            kw in lower for kw in ["naming", "convention", "format", "prefix", "feature/", "fix/"]
        ):
            return line.strip()
    return None


def extract_commit_format(text: str) -> str | None:
    """Detect commit message format from contributing docs."""
    lower = text.lower()

    # Check for well-known conventions
    conventions = [
        ("conventional commits", "Conventional Commits (https://www.conventionalcommits.org/)"),
        ("angular commit", "Angular Commit Convention"),
        ("commitizen", "Commitizen / Conventional Commits"),
        ("semantic commit", "Semantic Commit Messages"),
        ("gitmoji", "Gitmoji"),
    ]
    for keyword, label in conventions:
        if keyword in lower:
            return label

    # Detect patterns like feat:, fix:, chore: in examples
    if re.search(r"(?:feat|fix|chore|docs|style|refactor|perf|test|ci)\s*(?:\([^)]*\))?\s*:", text):
        return "Conventional Commits style (feat:, fix:, chore:, etc.)"

    # Look for explicit commit message sections
    commit_section = re.search(
        r"(?i)(?:##?\s*)?commit\s+message[s]?\s+(?:format|convention|guide|style)[^\n]*\n((?:.*\n){1,10})",
        text,
    )
    if commit_section:
        return commit_section.group(0).strip()[:300]

    return None


def extract_license_requirement(text: str) -> str | None:
    """Detect CLA or DCO requirements."""
    lower = text.lower()
    requirements = []
    if "contributor license agreement" in lower or "cla" in lower.split():
        requirements.append("CLA (Contributor License Agreement)")
    if "developer certificate of origin" in lower or "dco" in lower.split() or "signed-off-by" in lower:
        requirements.append("DCO (Developer Certificate of Origin / Signed-off-by)")
    return "; ".join(requirements) if requirements else None


def parse_package_json(repo: Path) -> dict[str, str | None]:
    """Extract test and lint commands from package.json."""
    result: dict[str, str | None] = {"test": None, "lint": None}
    content = read_file(repo / "package.json")
    if not content:
        return result
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return result

    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return result

    for key in ("test", "test:unit", "test:all", "tests"):
        if key in scripts:
            result["test"] = f"npm run {key}  # {scripts[key]}"
            break

    for key in ("lint", "lint:all", "eslint", "lint:fix"):
        if key in scripts:
            result["lint"] = f"npm run {key}  # {scripts[key]}"
            break

    return result


def parse_pyproject_toml(repo: Path) -> dict[str, str | None]:
    """Extract test and lint config from pyproject.toml."""
    result: dict[str, str | None] = {"test": None, "lint": None}
    content = read_file(repo / "pyproject.toml")
    if not content or tomllib is None:
        return result
    try:
        data = tomllib.loads(content)
    except Exception:
        return result

    # pytest
    if "tool" in data and "pytest" in data["tool"]:
        result["test"] = "pytest"

    # ruff / flake8 / black / mypy
    tools = data.get("tool", {})
    lint_tools = []
    for name in ("ruff", "flake8", "black", "mypy", "isort", "pylint"):
        if name in tools:
            lint_tools.append(name)
    if lint_tools:
        result["lint"] = ", ".join(lint_tools) + " (configured in pyproject.toml)"

    # Check scripts in project.scripts or tool.poetry.scripts
    scripts_section = data.get("project", {}).get("scripts", {})
    if not scripts_section:
        scripts_section = data.get("tool", {}).get("poetry", {}).get("scripts", {})

    return result


def parse_makefile(repo: Path) -> dict[str, str | None]:
    """Extract test and lint targets from Makefile."""
    result: dict[str, str | None] = {"test": None, "lint": None}
    content = read_file(repo / "Makefile")
    if not content:
        return result

    targets = re.findall(r"^([\w\-]+)\s*:", content, re.MULTILINE)
    for target in targets:
        lower = target.lower()
        if lower in ("test", "tests", "check", "test-all", "test-unit") and not result["test"]:
            result["test"] = f"make {target}"
        if lower in ("lint", "lint-all", "check-style", "fmt-check", "format-check") and not result["lint"]:
            result["lint"] = f"make {target}"

    return result


def detect_test_command(repo: Path) -> str | None:
    """Auto-detect the primary test command by checking common files."""
    # Try each source in priority order
    sources = [
        parse_package_json,
        parse_pyproject_toml,
        parse_makefile,
    ]
    for parser in sources:
        info = parser(repo)
        if info.get("test"):
            return info["test"]

    # Fallback heuristics based on files present
    if (repo / "Cargo.toml").is_file():
        return "cargo test"
    if (repo / "go.mod").is_file():
        return "go test ./..."
    if (repo / "setup.py").is_file() or (repo / "pytest.ini").is_file() or (repo / "tox.ini").is_file():
        return "pytest"
    if (repo / "Gemfile").is_file():
        return "bundle exec rake test (or rspec)"

    return None


def detect_lint_command(repo: Path) -> str | None:
    """Auto-detect the primary lint command."""
    sources = [
        parse_package_json,
        parse_pyproject_toml,
        parse_makefile,
    ]
    for parser in sources:
        info = parser(repo)
        if info.get("lint"):
            return info["lint"]

    # Fallback heuristics
    if (repo / ".eslintrc.json").is_file() or (repo / ".eslintrc.js").is_file() or (repo / ".eslintrc.yml").is_file():
        return "eslint (config found)"
    if (repo / ".flake8").is_file():
        return "flake8"
    if (repo / ".golangci.yml").is_file() or (repo / ".golangci.yaml").is_file():
        return "golangci-lint run"
    if (repo / "rustfmt.toml").is_file():
        return "cargo fmt --check / cargo clippy"

    return None


def extract_pr_template_sections(template: str) -> list[str]:
    """Extract heading sections from a PR template."""
    headings = re.findall(r"^#+\s+(.+)", template, re.MULTILINE)
    if headings:
        return headings
    # Try HTML comments as section markers
    comments = re.findall(r"<!--\s*(.+?)\s*-->", template)
    if comments:
        return comments
    return []


def find_ci_workflows(repo: Path) -> list[str]:
    """List CI workflow names from .github/workflows/."""
    workflow_dir = repo / ".github" / "workflows"
    if not workflow_dir.is_dir():
        return []

    workflows = []
    for f in sorted(workflow_dir.iterdir()):
        if f.suffix in (".yml", ".yaml") and f.is_file():
            content = read_file(f)
            if content:
                name_match = re.search(r"^name:\s*['\"]?(.+?)['\"]?\s*$", content, re.MULTILINE)
                display = name_match.group(1) if name_match else f.stem
                workflows.append(f"{display} ({f.name})")
    return workflows


def generate_markdown(
    repo: Path,
    contributing_docs: dict[str, str],
    agent_instructions: dict[str, str],
    agent_conventions: dict[str, list[str]],
    branch_convention: str | None,
    commit_format: str | None,
    test_command: str | None,
    lint_command: str | None,
    pr_template_sections: list[str],
    issue_templates: list[str],
    ci_workflows: list[str],
    license_req: str | None,
) -> str:
    """Produce the final markdown summary."""
    lines: list[str] = []
    lines.append(f"# Repository Conventions: {repo.name}")
    lines.append("")

    # Contributing docs found
    lines.append("## Contributing Documentation")
    if contributing_docs:
        for name in contributing_docs:
            lines.append(f"- `{name}`")
    else:
        lines.append("_No contributing documentation found._")
    lines.append("")

    # Agent instruction files
    lines.append("## AI Agent Instructions")
    if agent_instructions:
        for name in agent_instructions:
            lines.append(f"- `{name}`")
        lines.append("")
        lines.append("**IMPORTANT:** These files contain project-specific rules that AI agents")
        lines.append("must follow. Read them in full before making changes.")
    else:
        lines.append("_No AI agent instruction files found (AGENTS.md, CLAUDE.md, etc.)._")
    lines.append("")

    # Extracted agent conventions (structured)
    if agent_conventions:
        category_labels = {
            "architecture_boundaries": "Architecture Boundaries",
            "build_gates": "Build / Verification Gates",
            "coding_style": "Coding Style Rules",
            "restricted_paths": "Restricted Paths / Ownership",
            "naming_conventions": "Naming Conventions / Terminology",
            "import_rules": "Import / Module Boundary Rules",
        }
        for key, items in agent_conventions.items():
            label = category_labels.get(key, key.replace("_", " ").title())
            lines.append(f"### {label}")
            for item in items[:10]:  # Cap at 10 per category to keep output manageable
                lines.append(f"- {item}")
            if len(items) > 10:
                lines.append(f"- _...and {len(items) - 10} more (read source files for full list)_")
            lines.append("")

    # Branch naming
    lines.append("## Branch Naming Convention")
    lines.append(branch_convention if branch_convention else "_Not explicitly documented._")
    lines.append("")

    # Commit format
    lines.append("## Commit Message Format")
    lines.append(commit_format if commit_format else "_Not explicitly documented._")
    lines.append("")

    # Test command
    lines.append("## Test Command")
    lines.append(f"`{test_command}`" if test_command else "_No test command detected._")
    lines.append("")

    # Lint command
    lines.append("## Lint Command")
    lines.append(f"`{lint_command}`" if lint_command else "_No lint command detected._")
    lines.append("")

    # PR template
    lines.append("## PR Template Sections")
    if pr_template_sections:
        for section in pr_template_sections:
            lines.append(f"- {section}")
    else:
        lines.append("_No PR template found._")
    lines.append("")

    # Issue templates
    lines.append("## Issue Templates")
    if issue_templates:
        for name in issue_templates:
            lines.append(f"- `{name}`")
    else:
        lines.append("_No issue templates found._")
    lines.append("")

    # CI workflows
    lines.append("## CI Checks")
    if ci_workflows:
        for wf in ci_workflows:
            lines.append(f"- {wf}")
    else:
        lines.append("_No GitHub Actions workflows found._")
    lines.append("")

    # License / CLA / DCO
    lines.append("## License / CLA / DCO Requirements")
    lines.append(license_req if license_req else "_No CLA or DCO requirement detected._")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract contributing conventions from a git repository."
    )
    parser.add_argument(
        "--repo-dir",
        required=True,
        type=Path,
        help="Path to a cloned git repository.",
    )
    args = parser.parse_args()

    repo: Path = args.repo_dir.resolve()
    if not repo.is_dir():
        print(f"Error: {repo} is not a directory.", file=sys.stderr)
        sys.exit(1)

    # 1. Contributing docs
    contributing_docs = find_contributing_docs(repo)
    all_contributing_text = "\n\n".join(contributing_docs.values())

    # 2. AI agent instruction files
    agent_instructions = find_agent_instructions(repo)
    agent_conventions = extract_agent_conventions(agent_instructions) if agent_instructions else {}

    # Combine contributing + agent text for convention extraction
    all_text = all_contributing_text
    if agent_instructions:
        all_text += "\n\n" + "\n\n".join(agent_instructions.values())

    # 3. Branch convention
    branch_convention = extract_branch_convention(all_text) if all_text else None

    # 4. Commit format
    commit_format = extract_commit_format(all_text) if all_text else None

    # 5. License requirement
    license_req = extract_license_requirement(all_text) if all_text else None

    # 6. Test and lint commands
    test_command = detect_test_command(repo)
    lint_command = detect_lint_command(repo)

    # 7. PR template
    pr_template_raw = find_pr_template(repo)
    pr_template_sections = extract_pr_template_sections(pr_template_raw) if pr_template_raw else []

    # 8. Issue templates
    issue_templates = find_issue_templates(repo)

    # 9. CI workflows
    ci_workflows = find_ci_workflows(repo)

    # Generate and print output
    output = generate_markdown(
        repo=repo,
        contributing_docs=contributing_docs,
        agent_instructions=agent_instructions,
        agent_conventions=agent_conventions,
        branch_convention=branch_convention,
        commit_format=commit_format,
        test_command=test_command,
        lint_command=lint_command,
        pr_template_sections=pr_template_sections,
        issue_templates=issue_templates,
        ci_workflows=ci_workflows,
        license_req=license_req,
    )
    print(output)


if __name__ == "__main__":
    main()
