"""Validate skills, plugin manifests, Markdown links and evals.

Run from anywhere: python scripts/validate_skills.py
Exits with status 1 and prints every problem found.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
LINK_RE = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
SKIP_DIRS = {".git", ".pytest_cache", "node_modules"}

errors: list[str] = []


def error(path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def parse_frontmatter(path: Path) -> dict[str, str] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fields = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith(" "):
            fields[key.strip()] = value.strip()
    return fields


def check_skills() -> set[str]:
    names = set()
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            error(skill_dir, "missing SKILL.md")
            continue
        fields = parse_frontmatter(skill_md)
        if fields is None:
            error(skill_md, "missing or unterminated YAML frontmatter")
            continue
        name = fields.get("name", "")
        description = fields.get("description", "")
        if not NAME_RE.fullmatch(name) or len(name) > 64:
            error(skill_md, f"name {name!r} must be lowercase-hyphenated, at most 64 characters")
        if name != skill_dir.name:
            error(skill_md, f"name {name!r} does not match directory {skill_dir.name!r}")
        if not description:
            error(skill_md, "description is empty")
        elif len(description) > 1024:
            error(skill_md, f"description is {len(description)} characters (max 1024)")
        names.add(skill_dir.name)
    return names


def check_manifests() -> None:
    for path in sorted((ROOT / ".claude-plugin").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            error(path, f"invalid JSON: {e}")
            continue
        if path.name == "plugin.json" and not SEMVER_RE.fullmatch(str(data.get("version", ""))):
            error(path, f"version {data.get('version')!r} is not MAJOR.MINOR.PATCH")


def check_links() -> None:
    for path in sorted(ROOT.rglob("*.md")):
        if SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        for target in LINK_RE.findall(path.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target):
                continue
            if not (path.parent / target).exists():
                error(path, f"broken link {target!r}")


def check_evals(skill_names: set[str]) -> None:
    evals_root = ROOT / "evals"
    if not evals_root.is_dir():
        return
    for eval_dir in sorted(p for p in evals_root.iterdir() if p.is_dir()):
        if eval_dir.name not in skill_names:
            error(eval_dir, "no skill with this name in skills/")
        evals_json = eval_dir / "evals.json"
        try:
            data = json.loads(evals_json.read_text(encoding="utf-8"))
        except FileNotFoundError:
            error(eval_dir, "missing evals.json")
            continue
        except json.JSONDecodeError as e:
            error(evals_json, f"invalid JSON: {e}")
            continue
        if data.get("skill_name") != eval_dir.name:
            error(evals_json, f"skill_name {data.get('skill_name')!r} does not match directory")
        ids = [case.get("id") for case in data.get("evals", [])]
        if len(ids) != len(set(ids)):
            error(evals_json, "duplicate eval ids")
        for case in data.get("evals", []):
            for file in case.get("files", []):
                if not (ROOT / file).exists():
                    error(evals_json, f"eval {case.get('id')}: file {file!r} not found")


def main() -> int:
    skill_names = check_skills()
    check_manifests()
    check_links()
    check_evals(skill_names)
    if errors:
        print("\n".join(errors))
        print(f"\n{len(errors)} problem(s) found.")
        return 1
    print(f"OK: {len(skill_names)} skill(s) validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
