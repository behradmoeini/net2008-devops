#!/usr/bin/env python3
"""Week 10 lab self-check (NET2008 DevOps).

Run it from inside your lab folder (bytown-cluster), with the cluster bytown running:

    python3 /path/to/W10_Lab_selfcheck.py --seed 17     (macOS / Linux)
    python  /path/to/W10_Lab_selfcheck.py --seed 17     (Windows PowerShell)

It only reads your files and asks the cluster for information. It changes
nothing. Use your own seed: the sum of the last four digits of your student ID.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CONTEXT = "k3d-bytown"
AGE_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


def run(*args):
    """Run a command and return (exit code, stdout text). Never raises."""
    try:
        p = subprocess.run(list(args), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
        return p.returncode, p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 1, ""


def kube_json(*args):
    """Ask the lab cluster for objects as JSON. None if that fails."""
    rc, out = run("kubectl", "--context", CONTEXT, *args, "-o", "json")
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except ValueError:
        return None


def decode(data):
    """Decode a text file. Windows PowerShell 5.1 writes UTF-16 with tee, so handle that too."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8", errors="replace")
    if b"\x00" in data[:400]:
        return data.decode("utf-16-le", errors="replace")
    return data.decode("utf-8", errors="replace")


def age_seconds(token):
    """Turn a kubectl AGE such as 45s, 2m10s, 3h or 2d4h into seconds. None if it is not an age."""
    parts = re.findall(r"(\d+)([dhms])", token)
    if not parts or "".join(n + u for n, u in parts) != token:
        return None
    return sum(int(n) * AGE_UNITS[u] for n, u in parts)


def pod_rows(text):
    """Rows of `kubectl get pods` for the bytown-web pods: (status, age in seconds)."""
    rows = []
    for line in text.splitlines():
        cols = line.split()
        if len(cols) < 5 or not cols[0].startswith("bytown-web-"):
            continue
        age = next((a for a in (age_seconds(c) for c in cols[3:]) if a is not None), None)
        rows.append((cols[2], age))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="sum of the last four digits of your student ID")
    seed = ap.parse_args().seed
    if not 0 < seed <= 36:
        sys.exit("The seed must be between 1 and 36.")
    repl = 2 + seed % 3
    swarm_port = 8500 + seed

    root = Path.cwd()
    if root.name != "bytown-cluster":
        sys.exit("Run this from the folder ~/bytown-cluster.")

    results = []

    def check(part, description, passed, points):
        results.append((part, description, bool(passed), points))

    def read(rel):
        p = root / rel
        return decode(p.read_bytes()) if p.is_file() else ""

    cluster_up = run("kubectl", "--context", CONTEXT, "get", "nodes")[0] == 0
    if not cluster_up:
        print("The cluster bytown does not answer: the live checks will fail.")
        print("Start it with `k3d cluster start bytown` (or create it, Part 2) and run this again.\n")

    # ---- Part 1: Docker Swarm (20 points). Swarm is off by now, so only the files are checked.
    stack = read("swarm/stack.yaml")
    check(1, f"swarm/stack.yaml runs bytown-web:1.0 with replicas: {repl} on port {swarm_port}",
          re.search(r"image:\s*bytown-web:1\.0\b", stack)
          and re.search(rf"^\s*replicas:\s*{repl}\s*$", stack, re.M)
          and f"{swarm_port}:80" in stack, 4)
    services = read("evidence/part1-services.txt")
    check(1, f"evidence/part1-services.txt shows bytown_web with {repl}/{repl} replicas and port {swarm_port}",
          any("bytown_web" in l and f"{repl}/{repl}" in l and str(swarm_port) in l for l in services.splitlines()), 4)
    check(1, f"evidence/part1-curl.txt shows Seed: {seed}", f"Seed: {seed}" in read("evidence/part1-curl.txt"), 4)
    tasks = [l for l in read("evidence/part1-healed.txt").splitlines() if "bytown_web." in l]
    replaced = [l for l in tasks if "\\_" in l]
    running = [l for l in tasks if "\\_" not in l and "Running" in l]
    check(1, f"evidence/part1-healed.txt shows {repl} running tasks and one replaced task (marked \\_)",
          len(running) >= repl and replaced, 8)

    # ---- Part 2: K3s cluster (8 points)
    nodes = kube_json("get", "nodes")
    ready = 0
    for item in (nodes or {}).get("items", []):
        conds = item.get("status", {}).get("conditions") or []
        if any(c.get("type") == "Ready" and c.get("status") == "True" for c in conds):
            ready += 1
    check(2, "The cluster bytown has 3 nodes, all Ready", ready == 3 and len((nodes or {}).get("items", [])) == 3, 4)
    saved = read("evidence/part2-nodes.txt")
    check(2, "evidence/part2-nodes.txt lists 3 Ready nodes of the cluster bytown",
          sum(1 for l in saved.splitlines() if l.startswith("k3d-bytown-") and re.search(r"\sReady\s", l)) == 3, 4)

    # ---- Part 3: Deployment (20 points)
    dep_file = read("k8s/deployment.yaml")
    check(3, f"k8s/deployment.yaml is a Deployment named bytown-web with replicas: {repl} and the label app: bytown-web",
          re.search(r"kind:\s*Deployment", dep_file) and re.search(r"name:\s*bytown-web\s*$", dep_file, re.M)
          and re.search(rf"^\s*replicas:\s*{repl}\s*$", dep_file, re.M)
          and len(re.findall(r"app:\s*bytown-web\s*$", dep_file, re.M)) >= 2, 4)
    dep = kube_json("get", "deployment", "bytown-web")
    ok = False
    if dep:
        ok = (dep["spec"].get("replicas") == repl and dep.get("status", {}).get("readyReplicas") == repl
              and dep["spec"].get("selector", {}).get("matchLabels") == {"app": "bytown-web"})
    check(3, f"The Deployment bytown-web runs {repl} ready pods, selected by app: bytown-web", ok, 4)
    pods_text = read("evidence/part3-pods.txt")
    check(3, "evidence/part3-pods.txt lists your pods Running, with their nodes",
          sum(1 for status, _ in pod_rows(pods_text) if status == "Running") >= repl and "k3d-bytown-" in pods_text, 4)
    healed = [(s, a) for s, a in pod_rows(read("evidence/part3-healed.txt")) if s == "Running"]
    ages = [a for _, a in healed if a is not None]
    check(3, "evidence/part3-healed.txt shows all pods Running, one of them younger than the others",
          len(healed) >= repl and len(ages) >= 2 and min(ages) < max(ages), 8)

    # ---- Part 4: Service (12 points)
    svc_file = read("k8s/service.yaml")
    check(4, "k8s/service.yaml is a NodePort Service on 30080 that selects app: bytown-web",
          re.search(r"type:\s*NodePort", svc_file) and re.search(r"nodePort:\s*30080\b", svc_file)
          and re.search(r"app:\s*bytown-web\s*$", svc_file, re.M), 4)
    svc = kube_json("get", "service", "bytown-web")
    slices = kube_json("get", "endpointslices", "-l", "kubernetes.io/service-name=bytown-web")
    endpoints = 0
    for item in (slices or {}).get("items", []):
        for ep in item.get("endpoints") or []:
            if (ep.get("conditions") or {}).get("ready", True):
                endpoints += 1
    ok = bool(svc) and svc["spec"].get("type") == "NodePort" \
        and svc["spec"].get("selector") == {"app": "bytown-web"} \
        and any(p.get("nodePort") == 30080 for p in svc["spec"].get("ports", [])) and endpoints == repl
    check(4, f"The Service bytown-web is a NodePort on 30080 with {repl} endpoints (one per pod)", ok, 4)
    check(4, f"evidence/part4-curl.txt shows Seed: {seed}", f"Seed: {seed}" in read("evidence/part4-curl.txt"), 4)

    # ---- Part 5: Rolling update and rollback (12 points)
    v11 = read("evidence/part5-v11.txt")
    check(5, "evidence/part5-v11.txt shows your page with Version 1.1", "Version 1.1" in v11 and f"Seed: {seed}" in v11, 4)
    images = set()
    rs = kube_json("get", "replicasets", "-l", "app=bytown-web")
    for item in (rs or {}).get("items", []):
        for c in item["spec"]["template"]["spec"]["containers"]:
            images.add(c["image"])
    current = dep["spec"]["template"]["spec"]["containers"][0]["image"] if dep else ""
    check(5, "The cluster ran bytown-web:1.1 and now runs bytown-web:1.0 again",
          "bytown-web:1.1" in images and current == "bytown-web:1.0", 4)
    undo = read("evidence/part5-undo.txt")
    check(5, "evidence/part5-undo.txt shows your page without Version 1.1",
          f"Seed: {seed}" in undo and "Version 1.1" not in undo, 4)

    # ---- Part 6: Answers (8 points)
    ans = {}
    for line in read("answers.txt").splitlines():
        m = re.match(r"^\s*Q([1-3])\s*:\s*(.*)$", line)
        if m:
            ans[int(m.group(1))] = m.group(2).strip()
    good = all(len(ans.get(i, "")) >= 20 and "replace this" not in ans[i] for i in (1, 2, 3))
    check(6, "answers.txt has real answers for Q1 to Q3 (your instructor reads them)", good, 8)

    total = sum(p for *_, ok, p in results if ok)
    maxp = sum(p for *_, p in results)
    last = 0
    for part, desc, ok, pts in results:
        if part != last:
            print()
            print(f"Part {part}")
            last = part
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    print(f"\nSelf-check: {total:g} of {maxp:g} points. The other 20 of the 100 points come from your instructor's review of your work.")


if __name__ == "__main__":
    main()
