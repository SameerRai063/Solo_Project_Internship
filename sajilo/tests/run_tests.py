"""Run every case in tests/test_cases.json against the current prompt version.

    python tests/run_tests.py

Writes tests/results/<PROMPT_VERSION>.md. The auto-checks are hints, not verdicts:
open the file, read the outputs, and record your own verdict in prompt_log.md.
Cases whose text or file is missing are marked TODO.
"""
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import prompts  # noqa: E402
from utils import explain_document  # noqa: E402

CASES = json.loads((ROOT / "tests" / "test_cases.json").read_text(encoding="utf-8"))


def load_text(case):
    if case.get("text"):
        return case["text"]
    path = ROOT / case.get("file", "missing")
    return path.read_text(encoding="utf-8") if path.is_file() else None


def auto_check(case, outcome):
    data = outcome.result.model_dump()
    for item in data["action_items"] + data["watch_out_for"]:
        item.pop("source_quote")  # a good answer may quote the very text we are searching for
    blob = json.dumps(data, ensure_ascii=False).lower()
    problems = list(outcome.warnings)
    if outcome.unverified:
        problems.append(f"{len(outcome.unverified)} quote(s) not found in the source text")
    for bad in case.get("must_not_contain", []):
        if bad.lower() in blob:
            problems.append(f"contains {bad!r}")
    wanted = case.get("must_contain_any", [])
    if wanted and not any(w.lower() in blob for w in wanted):
        problems.append(f"none of {wanted} found")
    if case.get("expect_no_deadlines") and any(a.deadline for a in outcome.result.action_items):
        problems.append("invented a deadline")
    if case.get("expect_type") and outcome.result.document_type != case["expect_type"]:
        problems.append(f"document_type was {outcome.result.document_type!r}")
    return problems


rows, details, ran, passed = [], [], 0, 0
for case in CASES:
    label = f"| {case['id']} | {case['name']} | {case['kind']} |"
    text = load_text(case)
    if text is None:
        rows.append(f"{label} TODO | no text or file yet |")
        continue
    ran += 1
    retried = False
    try:
        outcome = explain_document(text, case.get("language", "English"), case.get("detail", "standard"))
        problems, retried = auto_check(case, outcome), outcome.retried
        output = outcome.result.model_dump_json(indent=2)
    except Exception as exc:  # a crash is a result too: record it and keep going
        problems, output = [f"crashed: {exc}"], ""
    if not problems:
        passed += 1
    status = ("PASS" if not problems else "FAIL") + (" (retried)" if retried else "")
    rows.append(f"{label} {status} | {'; '.join(problems)} |")
    details.append(f"### {case['id']}. {case['name']}\n\n```json\n{output}\n```")
    time.sleep(2)  # be gentle with free-tier rate limits

header = (
    f"# Results for prompt {prompts.PROMPT_VERSION}\n\n"
    f"Model: `{os.getenv('LLM_MODEL')}` | **{passed}/{ran} passed** | {len(CASES) - ran} case(s) still TODO\n\n"
    "| ID | Case | Kind | Auto-check | Problems |\n|---|---|---|---|---|\n"
)
table = "\n".join(rows)
out_dir = ROOT / "tests" / "results"
out_dir.mkdir(exist_ok=True)
report = header + table + "\n\n## Outputs\n\n" + "\n\n".join(details) + "\n"
(out_dir / f"{prompts.PROMPT_VERSION}.md").write_text(report, encoding="utf-8")
print(header + table)
