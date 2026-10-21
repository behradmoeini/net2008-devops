#!/usr/bin/env python3
"""Week 13 lab self-check (NET2008 DevOps).

Run it from inside your lab folder (bytown-ci):

    python3 /path/to/W13_Lab_selfcheck.py --seed 17

It reads your files, runs ruff and pytest on your code, and checks the Git
history. It changes nothing and cannot see GitHub: your instructor opens your
Actions runs. Use your own seed: the sum of the last four digits of your ID.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def run(*args, cwd=None):
    """Run a command and return (exit code, output text). Never raises."""
    try:
        p = subprocess.run(list(args), capture_output=True, text=True, encoding="utf-8", timeout=120, cwd=cwd)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ""


RUN_URL = re.compile(r"^https://github\.com/[\w.-]+/bytown-ci/actions/runs/\d+/?$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="sum of the last four digits of your student ID")
    seed = ap.parse_args().seed
    if not 0 < seed <= 36:
        sys.exit("The seed must be between 1 and 36.")

    root = Path.cwd()
    if root.name != "bytown-ci":
        sys.exit("Run this from the folder ~/bytown-ci.")

    results = []

    def check(part, description, passed, points):
        results.append((part, description, bool(passed), points))

    def read(rel):
        p = root / rel
        return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

    # ---- Part 1 (5 points)
    fleet = read("fleet.py")
    check(1, f"fleet.py has SEED = {seed}", re.search(rf"^SEED\s*=\s*{seed}\s*$", fleet, re.M) is not None, 1)
    tests = read("test_fleet.py")
    n_tests = len(re.findall(r"^def test_\w+\(", tests, re.M))
    expected_port = 9000 + seed * 10 + 3
    check(1, f"test_fleet.py has 5 or more tests, one checking the port of device 3 ({expected_port})",
          n_tests >= 5 and str(expected_port) in tests, 1)
    py = sys.executable
    rc, out = run(py, "-m", "pytest", "-q", "-p", "no:cacheprovider", cwd=root)
    check(1, "pytest passes on your code", rc == 0, 1)
    rc, out = run(py, "-m", "ruff", "check", ".", cwd=root)
    if rc != 0 and "No module named" in out:
        rc, out = run("ruff", "check", ".", cwd=root)
    check(1, "ruff check passes on your code", rc == 0, 1)
    ev = read("evidence/part1-pytest.txt")
    check(1, "evidence/part1-pytest.txt shows passed tests", re.search(r"\d+ passed", ev) is not None and "failed" not in ev, 1)

    # ---- Part 2 (6 points)
    wf = read(".github/workflows/ci.yml")
    check(2, "ci.yml triggers on push to main and on pull_request",
          "push:" in wf and "pull_request" in wf and "main" in wf, 1)
    check(2, f'ci.yml sets SEED to "{seed}" in env', re.search(rf'SEED:\s*"?{seed}"?\s*$', wf, re.M) is not None, 1)
    check(2, "ci.yml has a matrix of Python versions and uses it", "matrix:" in wf and "matrix.python-version" in wf, 1)
    check(2, "ci.yml runs ruff and pytest", "ruff check" in wf and "pytest" in wf, 1)
    check(2, "ci.yml has a job package that needs test and builds an image tagged with your seed",
          "needs: test" in wf and "docker build" in wf and "seed-" in wf, 1)
    green = read("evidence/actions-green.txt").strip()
    check(2, "evidence/actions-green.txt holds the address of a run (your instructor opens it)", RUN_URL.match(green) is not None, 1)

    # ---- Part 3 (2 points)
    red = read("evidence/actions-red.txt").strip()
    check(3, "evidence/actions-red.txt holds the address of a different run", RUN_URL.match(red) is not None and red != green, 1)
    rc, log = run("git", "log", "--oneline", cwd=root)
    check(3, "Git history has your break commit and a revert commit",
          "Break" in log and re.search(r"\bRevert\b", log) is not None, 1)

    # ---- Part 4 (5 points)
    jf = read("Jenkinsfile")
    check(4, "Jenkinsfile is a declarative pipeline with an agent and a stages block",
          "pipeline" in jf and "agent" in jf and "stages" in jf, 1)
    check(4, f"Jenkinsfile sets SEED to '{seed}' and has the stage 'Test seed {seed}'",
          re.search(rf"SEED\s*=\s*'{seed}'", jf) is not None and f"stage('Test seed {seed}')" in jf, 1)
    check(4, "Jenkinsfile runs pytest and has a post block", "pytest" in jf and "post" in jf, 1)
    jc = read("evidence/jenkins-console.txt")
    check(4, "evidence/jenkins-console.txt ends with Finished: SUCCESS", "Finished: SUCCESS" in jc, 1)
    check(4, f"The Jenkins log shows the port {expected_port} and a passed test run",
          str(expected_port) in jc and re.search(r"\d+ passed", jc) is not None, 1)

    # ---- Part 5 (2 points)
    ans = {}
    for line in read("answers.txt").splitlines():
        m = re.match(r"^\s*Q([1-3])\s*:\s*(.*)$", line)
        if m:
            ans[int(m.group(1))] = m.group(2).strip()
    good = all(len(ans.get(i, "")) >= 20 and "replace this" not in ans[i] for i in (1, 2, 3))
    check(5, "answers.txt has real answers for Q1 to Q3 (your instructor reads them)", good, 2)

    total = sum(p for *_, ok, p in results if ok)
    maxp = sum(p for *_, p in results)
    last = 0
    for part, desc, ok, pts in results:
        if part != last:
            print()
            print(f"Part {part}")
            last = part
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    print(f"\nSelf-check: {total:g} of {maxp:g} points. Your instructor also opens your Actions runs and reads answers.txt.")


if __name__ == "__main__":
    main()
