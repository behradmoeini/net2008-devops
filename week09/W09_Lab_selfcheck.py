#!/usr/bin/env python3
"""Week 9 lab self-check (NET2008 DevOps).

Run it from inside your lab folder (bytown-containers):

    python3 /path/to/W09_Lab_selfcheck.py --seed 17

It only reads your files and asks Docker for information. It changes nothing.
Use your own seed: the sum of the last four digits of your student ID.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def run(*args):
    """Run a command and return (exit code, stdout text). Never raises."""
    try:
        p = subprocess.run(list(args), capture_output=True, text=True, encoding="utf-8", timeout=60)
        return p.returncode, p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="sum of the last four digits of your student ID")
    seed = ap.parse_args().seed
    if not 0 < seed <= 36:
        sys.exit("The seed must be between 1 and 36.")

    root = Path.cwd()
    if root.name != "bytown-containers":
        sys.exit("Run this from the folder ~/bytown-containers.")

    results = []

    def check(part, description, passed, points):
        results.append((part, description, bool(passed), points))

    def read(rel):
        p = root / rel
        return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

    docker_ok = run("docker", "info")[0] == 0
    if not docker_ok:
        print("Docker is not running: the checks that ask Docker will fail. Start Docker and run this again.\n")

    # ---- Part 1 (3 points)
    log = read("evidence/part1-logs.txt")
    check(1, "evidence/part1-logs.txt shows a GET / request answered with 200", bool(re.search(r'"GET / HTTP/1\.[01]" 200', log)), 2)
    rc, names = run("docker", "ps", "-a", "--format", "{{.Names}}")
    check(1, f"The container web-{seed} is deleted", f"web-{seed}" not in names.split(), 1)

    # ---- Part 2 (6 points)
    page = read("web/index.html")
    check(2, f"web/index.html contains Seed: {seed}", f"Seed: {seed}" in page, 1)
    df = [l.strip() for l in read("web/Dockerfile").splitlines()]
    check(2, "web/Dockerfile has FROM, ARG SEED, a seed LABEL and COPY",
          any(l.startswith("FROM ") for l in df) and "ARG SEED" in df
          and any(l.startswith("LABEL org.bytown.seed=") for l in df)
          and any(l.startswith("COPY ") for l in df), 1)
    check(2, "evidence/part2-curl.txt shows your seed", f"Seed: {seed}" in read("evidence/part2-curl.txt"), 1)
    labels = {}
    for tag in ("1.0", "1.1"):
        rc, out = run("docker", "image", "inspect", f"bytown-web:{tag}", "--format", "{{json .Config.Labels}}")
        try:
            labels[tag] = json.loads(out) if rc == 0 else None
        except ValueError:
            labels[tag] = None
    check(2, f"Image bytown-web:1.0 exists with the label org.bytown.seed={seed}",
          bool(labels["1.0"]) and labels["1.0"].get("org.bytown.seed") == str(seed), 1)
    check(2, "Image bytown-web:1.1 exists with the same label",
          bool(labels["1.1"]) and labels["1.1"].get("org.bytown.seed") == str(seed), 1)
    try:
        insp = json.loads(read("evidence/part2-inspect.json") or "[]")
        ok = bool(insp) and insp[0]["Config"]["Labels"].get("org.bytown.seed") == str(seed)
    except (ValueError, KeyError, TypeError, IndexError, AttributeError):
        ok = False
    check(2, "evidence/part2-inspect.json is the inspect output of your image", ok, 1)

    # ---- Part 3 (4 points)
    vol = f"bytown-data-{seed}"
    rc, vols = run("docker", "volume", "ls", "--format", "{{.Name}}")
    check(3, f"The volume {vol} exists", vol in vols.split(), 1)
    rc, content = run("docker", "run", "--rm", "-v", f"{vol}:/d", "alpine", "cat", "/d/status.txt")
    check(3, f"The volume holds status.txt with seed={seed}", rc == 0 and content == f"seed={seed}", 2)
    check(3, "evidence/part3-curl.txt shows the file served by a second container", read("evidence/part3-curl.txt").strip() == f"seed={seed}", 1)

    # ---- Part 4 (5 points)
    try:
        import yaml
        comp = yaml.safe_load(read("stack/compose.yaml")) or {}
    except Exception:  # PyYAML missing or invalid file
        comp = {}
    services = comp.get("services") or {}
    web, proxy = services.get("web") or {}, services.get("proxy") or {}
    rc, _ = run("docker", "compose", "--project-directory", str(root / "stack"), "config", "-q")
    check(4, "stack/compose.yaml is valid (docker compose config)", rc == 0 and bool(services), 1)
    check(4, "The service web has a build and no published ports", "build" in web and "ports" not in web, 1)
    ports = [str(p) for p in (proxy.get("ports") or [])]
    check(4, "The service proxy publishes ${PROXY_PORT}:80", any(p.endswith(":80") and "PROXY_PORT" in p for p in ports), 1)
    env = read("stack/.env")
    check(4, f"stack/.env has SEED={seed} and PROXY_PORT={8300 + seed}",
          f"SEED={seed}" in env.splitlines() and f"PROXY_PORT={8300 + seed}" in env.splitlines(), 1)
    check(4, "evidence/part4-curl.txt shows your seed, and part4-ps.txt shows the proxy port",
          f"Seed: {seed}" in read("evidence/part4-curl.txt") and str(8300 + seed) in read("evidence/part4-ps.txt"), 1)

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
    print(f"\nSelf-check: {total:g} of {maxp:g} points. Your instructor also reads answers.txt and your repository on GitHub.")


if __name__ == "__main__":
    main()
