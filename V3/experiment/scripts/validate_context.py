"""校验并冻结 V3，仅读原始输入及配置，不接触评分资产。"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import difflib
import hashlib
import json
import re

E = Path(__file__).resolve().parents[1]
H = E.parents[1]
V1 = E.parent / "shared-context-v2-20261016"
CONTROL = E.parent / "operator-control-v1"
SKILL = "project/.claude/skills/scientific-evidence/"
ALLOWED = {
    "system_prompt.md", "project/CLAUDE.md", "project/context/INDEX.md", "project/context/delegation.md",
    SKILL + "SKILL.md", *(SKILL + "references/" + name + ".md" for name in [
        "delegation-contract", "analysis-state", "data-design", "inference", "verification", "delivery"]),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store"}


def inspect():
    old = json.loads((V1 / "context-manifest.json").read_text())
    spec = json.loads((E / "batches/qwen3.7-flash-main-6d52948-20261016/control/run-spec.json").read_text())
    previous = hashes(V1 / "subject")
    current = hashes(E / "subject")
    errors = []
    if previous != old["subject_files"]:
        errors.append("Baseline V2 subject changed")
    changed = sorted(p for p in previous.keys() | current.keys()
                     if previous.get(p) != current.get(p))
    if set(changed) != ALLOWED:
        errors.append("Subject changes differ from authorized shared-context whitelist")
    project = E / "subject/project"
    for path in (E / "subject").rglob("*.md"):
        value = path.read_text()
        if any(task["task_id"] in value for task in spec["tasks"]):
            errors.append("Task-specific shared context: " + str(path))
        if re.search(r"(?:^|\s)@(?:\.?/|[\w-]+/)", value):
            errors.append("Eager context import: " + str(path))
        for target in re.findall(r"\]\(([^)]+)\)", value):
            if target.startswith(("http://", "https://", "#")):
                continue
            dest = (path.parent / target.split("#")[0]).resolve()
            if not dest.is_relative_to(project.resolve()) or not dest.is_file():
                errors.append("Invalid shared link: " + target)
    core = (E / "subject" / (SKILL + "SKILL.md")).read_text()
    if not core.startswith("---\nname: scientific-evidence\ndescription: "):
        errors.append("Invalid native skill frontmatter")
    if "版本：3.1.0" not in core:
        errors.append("Missing V3 version")
    inputs = {}
    for task in spec["tasks"]:
        source = Path(task["original_workspace"])
        inputs[task["task_id"]] = hashes(source)
        if inputs[task["task_id"]] != old["original_participant_inputs"][task["task_id"]]:
            errors.append("Original input changed: " + task["task_id"])
        if any(p.is_file() for p in (source / "output").rglob("*")):
            errors.append("Original input contains prior output")
    control = hashes(CONTROL)
    provenance = json.loads((CONTROL / "provenance.json").read_text())
    if hashes(CONTROL / "original-harness") != provenance["original_harness_sha256"]:
        errors.append("Original operator harness changed")
    return {
        "schema": "shared-scientific-context-freeze-v3",
        "version": "3.1.0", "errors": errors,
        "baseline_manifest_sha256": sha(V1 / "context-manifest.json"),
        "baseline_subject_files": previous, "subject_files": current,
        "changed_subject_files": changed, "original_participant_inputs": inputs,
        "control_entry_files": control,
        "shared_operator_entry_sha256": sha(E.parent / "operator-control-v2/README.md"),
        "run_control_files": {p: sha(E / p) for p in [
            "batches/qwen3.7-flash-main-6d52948-20261016/control/operator-task.md", "batches/qwen3.7-flash-main-6d52948-20261016/control/run-spec.json", "batches/qwen3.7-flash-main-6d52948-20261016/control/environment.md"]},
        "validator_sha256": sha(Path(__file__)),
        "scoring_allowed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    result = inspect()
    path = E / "context-manifest.json"
    if path.exists():
        frozen = json.loads(path.read_text())
        for key, value in result.items():
            if key != "errors" and value != frozen.get(key):
                result["errors"].append("Frozen field changed: " + key)
    elif args.freeze and not result["errors"]:
        result["frozen_at"] = datetime.now(timezone.utc).isoformat()
        with path.open("x") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        diff = []
        for rel in result["changed_subject_files"]:
            oldpath = V1 / "subject" / rel
            before = oldpath.read_text().splitlines(True) if oldpath.exists() else []
            after = (E / "subject" / rel).read_text().splitlines(True)
            diff.extend(difflib.unified_diff(before, after, fromfile="V2/"+rel, tofile="V3/"+rel))
        (E / "docs/subject-v2-to-v3.diff").write_text("".join(diff))
    print(json.dumps({"passed": not result["errors"], "errors": result["errors"],
                      "frozen": path.exists(), "subject_files": len(result["subject_files"]),
                      "changed_subject_files": result["changed_subject_files"],
                      "task_count": len(result["original_participant_inputs"]),
                      "input_files": sum(map(len, result["original_participant_inputs"].values()))},
                     ensure_ascii=False, indent=2))
    raise SystemExit(bool(result["errors"]))


if __name__ == "__main__":
    main()
