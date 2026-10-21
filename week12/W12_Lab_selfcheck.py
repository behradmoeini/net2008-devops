#!/usr/bin/env python3
"""Week 12 lab self-check (NET2008 DevOps).

Run it from inside your lab folder (bytown-ansible):

    python3 /path/to/W12_Lab_selfcheck.py --seed 17

It reads your files and your proof, and runs `ansible-playbook --syntax-check`.
It changes nothing. Use your own seed: the sum of the last four digits of your
student ID.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def run(*args, cwd=None):
    """Run a command and return (exit code, stdout text). Never raises."""
    try:
        p = subprocess.run(list(args), capture_output=True, text=True, encoding="utf-8", timeout=120, cwd=cwd)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ""


def recap(text):
    """Return {host: (ok, changed, unreachable, failed)} from a PLAY RECAP."""
    rows = {}
    for m in re.finditer(r"^(\S+)\s*:\s*ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)", text, re.M):
        rows[m.group(1)] = tuple(int(m.group(i)) for i in range(2, 6))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="sum of the last four digits of your student ID")
    seed = ap.parse_args().seed
    if not 0 < seed <= 36:
        sys.exit("The seed must be between 1 and 36.")

    root = Path.cwd()
    if root.name != "bytown-ansible":
        sys.exit("Run this from the folder ~/bytown-ansible.")

    results = []

    def check(part, description, passed, points):
        results.append((part, description, bool(passed), points))

    def read(rel):
        p = root / rel
        return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

    try:
        import yaml
    except ImportError:
        yaml = None

    hosts = [f"bytown-web1-{seed}", f"bytown-web2-{seed}", f"bytown-db1-{seed}"]

    # ---- Part 1 (4 points)
    inv = read("inventory.ini")
    groups, cur = {}, None
    for line in inv.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[(.+)\]$", line)
        if m:
            cur = m.group(1)
            groups[cur] = []
        elif cur:
            groups[cur].append(line)
    check(1, "inventory.ini has the group web with your two servers and the group db with your database server",
          groups.get("web") == hosts[:2] and groups.get("db") == [hosts[2]], 1)
    check(1, "inventory.ini connects through community.docker.docker", "ansible_connection=community.docker.docker" in inv, 1)
    ping = read("evidence/part1-ping.txt")
    check(1, "evidence/part1-ping.txt shows SUCCESS and pong for all three servers",
          all(re.search(re.escape(h) + r" \| SUCCESS", ping) for h in hosts) and ping.count('"ping": "pong"') == 3, 1)
    check(1, "ansible.cfg points to inventory.ini", "inventory = inventory.ini" in read("ansible.cfg"), 1)

    # ---- Part 2 (4 points)
    hn = read("evidence/part2-hostname.txt")
    check(2, "evidence/part2-hostname.txt shows the two web servers", all(h in hn for h in hosts[:2]), 1)
    check(2, "evidence/part2-facts.txt shows bookworm for all three servers",
          read("evidence/part2-facts.txt").count("bookworm") >= 3, 1)
    idem = read("evidence/part2-idempotent.txt")
    check(2, "evidence/part2-idempotent.txt shows an ad hoc apt run with changed: false", '"changed": false' in idem and hosts[2] in idem, 2)

    # ---- Part 3 (6 points)
    gv = {}
    if yaml:
        try:
            gv = yaml.safe_load(read("group_vars/all.yml")) or {}
        except Exception:
            gv = {}
    check(3, f"group_vars/all.yml has seed: {seed} and a site", gv.get("seed") == seed and bool(gv.get("site")), 1)
    tpl = read("templates/index.html.j2")
    check(3, "templates/index.html.j2 uses the variables seed, site and the fact ansible_distribution",
          "{{ seed }}" in tpl and "{{ site }}" in tpl and "ansible_distribution" in tpl, 1)
    plays = []
    if yaml:
        try:
            plays = yaml.safe_load(read("site.yml")) or []
        except Exception:
            plays = []
    plays = plays if isinstance(plays, list) else []
    tasks_text = read("site.yml")
    ok_struct = (len(plays) >= 3 and {p.get("hosts") for p in plays if isinstance(p, dict)} >= {"all", "web", "db"}
                 and "ansible.builtin.template" in tasks_text and "notify:" in tasks_text and "handlers:" in tasks_text
                 and all(t.get("name") for p in plays if isinstance(p, dict) for t in (p.get("tasks") or [])))
    check(3, "site.yml has three plays (all, web, db), a template task, a notify and a handler, and every task is named", ok_struct, 1)
    rc, out = run("ansible-playbook", "--syntax-check", "site.yml", cwd=root)
    check(3, "ansible-playbook --syntax-check site.yml passes", rc == 0 and "site.yml" in out, 1)
    r1, r2 = recap(read("evidence/part3-run1.txt")), recap(read("evidence/part3-run2.txt"))
    ok1 = set(r1) >= set(hosts) and all(r1[h][2] == 0 and r1[h][3] == 0 for h in hosts) and any(r1[h][1] > 0 for h in hosts)
    ok2 = set(r2) >= set(hosts) and all(r2[h][1] == 0 and r2[h][2] == 0 and r2[h][3] == 0 for h in hosts)
    check(3, "First run: no failures and some changes. Second run: changed=0 for all three servers", ok1 and ok2, 1)
    page = read("evidence/part3-page.txt")
    check(3, f"evidence/part3-page.txt shows Seed: {seed} for both web servers", page.count(f"Seed: {seed}") >= 2 and all(h in page for h in hosts[:2]), 1)

    # ---- Part 4 (3 points)
    chk = read("evidence/part4-check.txt")
    check(4, "evidence/part4-check.txt is a check-mode run with a diff of the site name (ott-dc1 to ott-dc2)",
          "ott-dc2" in chk and "ott-dc1" in chk and re.search(r"^[+-]", chk, re.M) is not None, 2)
    r4 = recap(chk)
    check(4, "The check-mode run had no failures", set(r4) >= set(hosts) and all(r4[h][3] == 0 and r4[h][2] == 0 for h in hosts), 1)

    # ---- Part 5 (3 points)
    ans = {}
    for line in read("answers.txt").splitlines():
        m = re.match(r"^\s*Q([1-3])\s*:\s*(.*)$", line)
        if m:
            ans[int(m.group(1))] = m.group(2).strip()
    good = all(len(ans.get(i, "")) >= 20 and "replace this" not in ans[i] for i in (1, 2, 3))
    check(5, "answers.txt has real answers for Q1 to Q3 (your instructor reads them)", good, 3)

    total = sum(p for *_, ok, p in results if ok)
    maxp = sum(p for *_, p in results)
    last = 0
    for part, desc, ok, pts in results:
        if part != last:
            print()
            print(f"Part {part}")
            last = part
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    print(f"\nSelf-check: {total:g} of {maxp:g} points. Your instructor also reads answers.txt and your repository on GitHub.")


if __name__ == "__main__":
    main()
