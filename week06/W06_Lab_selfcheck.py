#!/usr/bin/env python3
"""Week 6 lab self-check (NET2008 DevOps).

Run it from inside your lab repository folder (bytown-netops):

    python3 /path/to/W06_Lab_selfcheck.py --seed 17

It only reads your repository. It changes nothing. Use your own seed: the sum of
the last four digits of your student ID.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def git(*args):
    """Run a git command and return (exit code, stdout text)."""
    p = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="sum of the last four digits of your student ID")
    seed = ap.parse_args().seed
    if not 0 < seed <= 36:
        sys.exit("The seed must be between 1 and 36.")

    rc, top = git("rev-parse", "--show-toplevel")
    if rc != 0:
        sys.exit("This folder is not a Git repository. cd into ~/bytown-netops first.")
    root = Path(top)

    results = []  # (part, description, passed, points)

    def check(part, description, passed, points):
        results.append((part, description, bool(passed), points))

    def read(name):
        p = root / name
        return p.read_text(encoding="utf-8") if p.exists() else ""

    rc, subjects = git("log", "--format=%s", "--all")
    subjects = subjects.splitlines() if rc == 0 else []
    rc, branch = git("branch", "--show-current")
    cfg = read("core-rtr.cfg")
    cfg_lines = [l.rstrip() for l in cfg.splitlines()]
    ntp_lines = [l.rstrip() for l in read("ntp.cfg").splitlines()]

    # ---- Part 1: history and .gitignore (4 points)
    check(1, "You are on branch main", branch == "main", 0.5)
    ign = [l.strip() for l in read(".gitignore").splitlines()]
    check(1, ".gitignore lists *.log and secrets.env", "*.log" in ign and "secrets.env" in ign, 0.5)
    rc, tracked = git("ls-files")
    rc, ever = git("log", "--all", "--name-only", "--format=")
    bad = [f for f in (tracked + "\n" + ever).splitlines() if f.endswith(".log") or f == "secrets.env"]
    check(1, "No .log file and no secrets.env was ever committed", not bad, 1)
    need1 = ["Add .gitignore", "Add core router config", "Enable SNMP read-only"]
    check(1, "The three starting commits exist with the exact messages", all(m in subjects for m in need1), 1)
    check(1, f"core-rtr.cfg has your hostname and loopback (seed {seed})",
          f"hostname core-rtr-{seed}" in cfg_lines and f" ip address 10.{seed}.0.1 255.255.255.255" in cfg_lines
          and "snmp-server community netops-ro RO" in cfg_lines, 1)

    # ---- Part 2: undo (3 points)
    check(2, 'Commit "Shut down core uplink" exists', "Shut down core uplink" in subjects, 1)
    check(2, "It was undone with git revert (a commit whose message starts with Revert)",
          any(s.startswith('Revert "Shut down core uplink"') for s in subjects), 1)
    check(2, "No shutdown or MISTAKE line is left in core-rtr.cfg",
          cfg and not any("shutdown" in l or "MISTAKE" in l for l in cfg_lines), 1)

    # ---- Part 3: branches, merge, conflict (4 points)
    vlan = 100 + seed
    check(3, f"core-rtr.cfg has your guest VLAN (vlan {vlan})", f"vlan {vlan}" in cfg_lines and " name guest" in cfg_lines, 1)
    rc, merges = git("rev-list", "--merges", "--count", "HEAD")
    merges = int(merges) if merges.isdigit() else 0
    check(3, "At least 3 merge commits in main (guest VLAN, NTP conflict, pull request)", merges >= 3, 1)
    check(3, "ntp.cfg has exactly your two resolved lines and no conflict markers",
          ntp_lines == ["ntp server 10.0.0.11 prefer", "ntp server 10.0.0.12"], 1)
    rc, local = git("branch", "--format=%(refname:short)")
    check(3, "Only the branch main is left locally", local.split() == ["main"], 1)

    # ---- Part 4: GitHub push and pull (3 points)
    rc, url = git("config", "--get", "remote.origin.url")
    check(4, "origin points to a GitHub SSH address (git@github.com:...)", url.startswith("git@github.com:") and url.endswith("/bytown-netops.git"), 1)
    rc, up = git("rev-parse", "--abbrev-ref", "main@{upstream}")
    rc1, h_local = git("rev-parse", "main")
    rc2, h_remote = git("rev-parse", "origin/main")
    check(4, "main tracks origin/main and both are at the same commit", up == "origin/main" and rc1 == 0 and h_local == h_remote, 1)
    check(4, 'The GitHub edit "Send syslog to collector" is in your history and in core-rtr.cfg',
          "Send syslog to collector" in subjects and "logging host 10.0.0.50" in cfg_lines, 1)

    # ---- Part 5: pull request (3 points)
    check(5, 'Commit "Add login banner" exists and the banner line is in core-rtr.cfg',
          "Add login banner" in subjects and "banner motd Authorized access only" in cfg_lines, 1)
    check(5, "A pull request was merged on GitHub (Merge pull request ... add-banner)",
          any(s.startswith("Merge pull request") for s in subjects), 1)
    rc, remotes = git("branch", "-r", "--format=%(refname:short)")
    check(5, "The branch add-banner is deleted on GitHub (not listed as origin/add-banner)", "origin/add-banner" not in remotes.split() and "add-banner" not in local.split(), 1)

    # ---- Part 6: answers (3 points)
    ans = {}
    for line in read("answers.txt").splitlines():
        m = re.match(r"^\s*Q([1-5])\s*:\s*(.*)$", line)
        if m:
            ans[int(m.group(1))] = m.group(2).strip()
    check(6, "answers.txt is committed and has an answer for Q1 to Q5",
          "answers.txt" in tracked.splitlines() and all(ans.get(i) for i in range(1, 6)), 1)
    rc, blame = git("blame", "-l", "-L", "/^snmp-server community/,+1", "core-rtr.cfg")
    full = blame.split()[0].lstrip("^") if blame else ""
    a1 = ans.get(1, "").lower()
    check(6, "Q1 is the real commit ID of the SNMP line (git blame)", len(a1) >= 7 and full.startswith(a1[:40]), 1)
    check(6, f"Q2 matches the number of merge commits in your history ({merges})", ans.get(2, "").isdigit() and int(ans[2]) == merges, 1)

    total = sum(p for _, _, ok, p in results if ok)
    maxp = sum(p for *_, p in results)
    last = 0
    for part, desc, ok, pts in results:
        if part != last:
            print()
            print(f"Part {part}")
            last = part
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    print(f"\nSelf-check: {total:g} of {maxp:g} points. Your instructor also reads Q3 to Q5 and your pull request on GitHub.")


if __name__ == "__main__":
    main()
