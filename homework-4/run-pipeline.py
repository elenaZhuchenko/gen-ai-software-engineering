#!/usr/bin/env python3
"""run-pipeline.py — Single-command orchestrator for the 4-agent pipeline.

Drives six agents in the required order using the Cursor Python SDK:
  1. Bug Researcher        → codebase-research.md
  2. Research Verifier     → verified-research.md
  3. Bug Planner           → implementation-plan.md
  4. Bug Fixer             → fix-summary.md
  5. Security Verifier     → security-report.md
  6. Unit Test Generator   → test-report.md + tests/test_generated.py

Each agent's *.agent.md body serves as the prompt.  Skill files referenced in
the agent's frontmatter are loaded and appended to the prompt automatically.

Usage:
    python run-pipeline.py                  # full run (requires CURSOR_API_KEY)
    python run-pipeline.py --dry-run        # validate config without API calls
    python run-pipeline.py --from-stage 3   # restart from stage 3

Requirements:
    pip install cursor-sdk PyYAML
    export CURSOR_API_KEY=cursor_...
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

try:
    from cursor_sdk import Agent, AgentOptions, LocalAgentOptions, CursorAgentError
except ImportError:
    print(
        "ERROR: cursor-sdk is not installed.\n"
        "       Run: pip install cursor-sdk",
        file=sys.stderr,
    )
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

HERE: Path = Path(__file__).parent.resolve()
AGENTS_DIR: Path = HERE / "agents"
SKILLS_DIR: Path = HERE / "skills"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _parse_agent_file(path: Path) -> tuple[dict, str]:
    """Return ``(frontmatter_dict, body_text)`` from a ``*.agent.md`` file."""
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---"):
        end_idx = raw.find("---", 3)
        if end_idx != -1:
            fm_text = raw[3:end_idx].strip()
            body = raw[end_idx + 3:].strip()
            fm: dict = yaml.safe_load(fm_text) or {}
            return fm, body
    return {}, raw.strip()


def _load_skill(skill_rel_path: str) -> str:
    """Return the content of a skill file (path relative to homework-4/)."""
    skill_path = HERE / skill_rel_path
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return f"<!-- skill not found: {skill_rel_path} -->"


def _build_prompt(frontmatter: dict, body: str) -> str:
    """Compose the full agent prompt: body + appended skill sections."""
    parts: list[str] = [body]
    skills: list[str] = frontmatter.get("skills", []) or []
    if skills:
        parts.append("\n\n---\n# Referenced Skills\n")
        for skill_path in skills:
            skill_content = _load_skill(skill_path)
            skill_name = Path(skill_path).stem
            parts.append(f"\n## Skill: {skill_name}\n\n{skill_content}")
    return "\n".join(parts)


def _print_banner(title: str, width: int = 60) -> None:
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def _validate_output(expected_rel: str) -> bool:
    """Return True when the expected output file exists and is non-empty."""
    p = HERE / expected_rel
    if not p.exists():
        return False
    return p.stat().st_size > 0


# ──────────────────────────────────────────────────────────────────────────────
# Stage runner
# ──────────────────────────────────────────────────────────────────────────────

def run_stage(
    *,
    stage_num: int,
    total_stages: int,
    name: str,
    agent_file: str,
    expected_output: str | None,
    dry_run: bool,
) -> bool:
    """Execute one pipeline stage.  Returns True on success, False on failure."""
    path = AGENTS_DIR / agent_file
    if not path.exists():
        print(f"  ERROR: agent file not found: {path}", file=sys.stderr)
        return False

    frontmatter, body = _parse_agent_file(path)
    model: str = frontmatter.get("model", "composer-2.5")
    prompt = _build_prompt(frontmatter, body)
    skills = frontmatter.get("skills", []) or []

    _print_banner(f"[{stage_num}/{total_stages}] {name}")
    print(f"  Agent  : {agent_file}")
    print(f"  Model  : {model}")
    print(f"  Skills : {skills or '(none)'}")
    if expected_output:
        print(f"  Output : {expected_output}")
    print(f"  Prompt : {len(prompt):,} chars")

    if dry_run:
        print("  → [DRY RUN] skipping API call")
        return True

    api_key = os.environ.get("CURSOR_API_KEY", "")
    if not api_key:
        print("  ERROR: CURSOR_API_KEY not set", file=sys.stderr)
        return False

    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=model,
                local=LocalAgentOptions(cwd=str(HERE)),
            ),
        )
    except CursorAgentError as err:
        print(
            f"  ERROR: agent startup failed — {err.message} "
            f"(retryable={err.is_retryable})",
            file=sys.stderr,
        )
        # Startup failure (auth / network) — hard exit so the user can fix env
        sys.exit(1)

    print(f"  Status : {result.status}  (run_id={result.id})")

    if result.status == "error":
        print(
            f"  ERROR: agent run failed mid-flight (run_id={result.id}).\n"
            "         Check the Cursor dashboard for the full transcript.",
            file=sys.stderr,
        )
        return False

    # Validate expected artifact
    if expected_output:
        if _validate_output(expected_output):
            print(f"  ✓ Output verified: {expected_output}")
        else:
            print(
                f"  WARNING: expected output not found or empty: {expected_output}\n"
                "           The agent may have written to a different path.",
                file=sys.stderr,
            )
            return False

    return True


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline definition
# ──────────────────────────────────────────────────────────────────────────────

PIPELINE: list[dict] = [
    {
        "name": "Bug Researcher",
        "agent_file": "researcher.agent.md",
        "expected_output": "context/bugs/001/research/codebase-research.md",
    },
    {
        "name": "Research Verifier",
        "agent_file": "research-verifier.agent.md",
        "expected_output": "context/bugs/001/research/verified-research.md",
    },
    {
        "name": "Bug Planner",
        "agent_file": "bug-planner.agent.md",
        "expected_output": "context/bugs/001/implementation-plan.md",
    },
    {
        "name": "Bug Fixer",
        "agent_file": "bug-fixer.agent.md",
        "expected_output": "context/bugs/001/fix-summary.md",
    },
    {
        "name": "Security Verifier",
        "agent_file": "security-verifier.agent.md",
        "expected_output": "context/bugs/001/security-report.md",
    },
    {
        "name": "Unit Test Generator",
        "agent_file": "unit-test-generator.agent.md",
        "expected_output": "context/bugs/001/test-report.md",
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="4-Agent Bug/Security/Test Pipeline — single-command orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate agents/skills without making API calls.",
    )
    parser.add_argument(
        "--from-stage",
        type=int,
        default=1,
        metavar="N",
        help="Start (or resume) from stage N (1-based). Default: 1.",
    )
    args = parser.parse_args()

    _print_banner("4-Agent Bug/Security/Test Pipeline")
    print(f"  Working directory : {HERE}")
    print(f"  Dry run           : {args.dry_run}")
    print(f"  Starting at stage : {args.from_stage}")

    if not args.dry_run and not os.environ.get("CURSOR_API_KEY"):
        print(
            "\nERROR: CURSOR_API_KEY environment variable is required.\n"
            "       export CURSOR_API_KEY=cursor_...\n"
            "       Get your key at: https://cursor.com/dashboard/integrations",
            file=sys.stderr,
        )
        return 1

    start_idx = max(0, args.from_stage - 1)
    stages = PIPELINE[start_idx:]
    total = len(PIPELINE)

    for offset, stage in enumerate(stages):
        stage_num = start_idx + offset + 1
        success = run_stage(
            stage_num=stage_num,
            total_stages=total,
            name=stage["name"],
            agent_file=stage["agent_file"],
            expected_output=stage.get("expected_output"),
            dry_run=args.dry_run,
        )
        if not success:
            _print_banner(f"PIPELINE FAILED at stage {stage_num}: {stage['name']}")
            print(
                "  Fix the issue above and re-run with:\n"
                f"    python run-pipeline.py --from-stage {stage_num}",
                file=sys.stderr,
            )
            return 2

    _print_banner("Pipeline completed successfully ✓")
    print("\n  Artifacts produced:")
    for stage in PIPELINE:
        out = stage.get("expected_output")
        if out:
            exists = _validate_output(out)
            mark = "✓" if exists else "✗"
            print(f"    {mark} {out}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
