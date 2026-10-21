#!/usr/bin/env python3
"""Week 10 lab self-check (NET2008 DevOps).

Run it from inside your lab folder (bytown-k8s), with your cluster running:

    python3 /path/to/W10_Lab_selfcheck.py --seed 17

It only reads your files and asks the cluster for information. It changes
nothing. Use your own seed: the sum of the last four digits of your student ID.
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


def kube_json(*args):
    rc, out = run("kubectl", "-n", "bytown", *args, "-o", "json")
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="sum of the last four digits of your student ID")
    seed = ap.parse_args().seed
    if not 0 < seed <= 36:
        sys.exit("The seed must be between 1 and 36.")
    repl = 2 + seed % 3

    root = Path.cwd()
    if root.name != "bytown-k8s":
        sys.exit("Run this from the folder ~/bytown-k8s.")

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

    def load_yaml(rel):
        if yaml is None:
            return {}
        try:
            return yaml.safe_load(read(rel)) or {}
        except Exception:
            return {}

    cluster_up = run("kubectl", "get", "nodes")[0] == 0
    if not cluster_up:
        print("The cluster does not answer: the live checks will fail. Run `minikube start` and try again.\n")

    # ---- Part 1 (3 points)
    rc, out = run("kubectl", "get", "namespace", "bytown", "-o", "name")
    check(1, "The namespace bytown exists", rc == 0 and "bytown" in out, 1)
    img = read("evidence/part1-images.txt")
    check(1, "evidence/part1-images.txt lists bytown-web 1.0 and 1.1", "bytown-web:1.0" in img and "bytown-web:1.1" in img, 2)

    # ---- Part 2 (5 points)
    dep_file = load_yaml("k8s/deployment.yaml")
    spec = (dep_file.get("spec") or {})
    check(2, f"k8s/deployment.yaml has replicas: {repl}", spec.get("replicas") == repl, 1)
    tmpl_labels = (((spec.get("template") or {}).get("metadata") or {}).get("labels") or {})
    sel = ((spec.get("selector") or {}).get("matchLabels") or {})
    check(2, "The selector matches the pod labels (app: bytown-web)", sel == {"app": "bytown-web"} and tmpl_labels.get("app") == "bytown-web", 1)
    dep = kube_json("get", "deployment", "bytown-web")
    ok = False
    if dep:
        st = dep.get("status", {})
        ok = dep["spec"].get("replicas") == repl and st.get("readyReplicas") == repl
    check(2, f"The Deployment bytown-web has {repl} replicas, all ready", ok, 1)
    check(2, "evidence/part2-pods.txt lists your pods Running", read("evidence/part2-pods.txt").count("Running") >= repl, 1)
    healed = read("evidence/part2-healed.txt")
    ages = re.findall(r"\b(\d+)s\b", healed)
    check(2, "evidence/part2-healed.txt shows the replacement pod (a young AGE) and all pods Running",
          healed.count("Running") >= repl and any(int(a) < 120 for a in ages), 1)

    # ---- Part 3 (3 points)
    svc = load_yaml("k8s/service.yaml")
    ssel = ((svc.get("spec") or {}).get("selector") or {})
    check(3, "k8s/service.yaml selects app: bytown-web on port 80", ssel == {"app": "bytown-web"}
          and any(p.get("port") == 80 for p in ((svc.get("spec") or {}).get("ports") or [])), 1)
    ep = kube_json("get", "endpoints", "bytown-web")
    n = 0
    if ep:
        for sub in ep.get("subsets") or []:
            n += len(sub.get("addresses") or [])
    check(3, f"The Service has {repl} endpoints (one per pod)", n == repl, 1)
    check(3, f"evidence/part3-curl.txt shows Seed: {seed}", f"Seed: {seed}" in read("evidence/part3-curl.txt"), 1)

    # ---- Part 4 (4 points)
    cm = kube_json("get", "configmap", "bytown-config")
    check(4, f"The ConfigMap bytown-config has SITE=ott-dc1-{seed}", bool(cm) and cm.get("data", {}).get("SITE") == f"ott-dc1-{seed}", 1)
    sec = kube_json("get", "secret", "bytown-secret")
    check(4, "The Secret bytown-secret has a TOKEN", bool(sec) and "TOKEN" in (sec.get("data") or {}), 1)
    env = []
    if dep:
        env = dep["spec"]["template"]["spec"]["containers"][0].get("env", [])
    uses_cm = any((e.get("valueFrom") or {}).get("configMapKeyRef", {}).get("name") == "bytown-config" for e in env)
    uses_sec = any((e.get("valueFrom") or {}).get("secretKeyRef", {}).get("name") == "bytown-secret" for e in env)
    check(4, "The Deployment reads SITE from the ConfigMap and TOKEN from the Secret", uses_cm and uses_sec, 1)
    check(4, f"evidence/part4-site.txt shows ott-dc1-{seed}", read("evidence/part4-site.txt").strip() == f"ott-dc1-{seed}", 1)

    # ---- Part 5 (3 points)
    check(5, "evidence/part5-v11.txt shows Version 1.1", "Version 1.1" in read("evidence/part5-v11.txt"), 1)
    images = set()
    rs = kube_json("get", "replicaset")
    if rs:
        for item in rs.get("items", []):
            for c in item["spec"]["template"]["spec"]["containers"]:
                images.add(c["image"])
    cur = ""
    if dep:
        cur = dep["spec"]["template"]["spec"]["containers"][0]["image"]
    check(5, "The cluster ran 1.1 at some point and now runs bytown-web:1.0", "bytown-web:1.1" in images and cur == "bytown-web:1.0", 1)
    hist_rows = [l for l in read("evidence/part5-history.txt").splitlines() if re.match(r"^\s*\d+\s", l)]
    manifest_img = [l.strip() for l in read("k8s/deployment.yaml").splitlines() if l.strip().startswith("image:")]
    check(5, "The saved history has 3 or more revisions and k8s/deployment.yaml says bytown-web:1.0",
          len(hist_rows) >= 3 and manifest_img == ["image: bytown-web:1.0"], 1)

    # ---- Part 6 (2 points)
    ans = {}
    for line in read("answers.txt").splitlines():
        m = re.match(r"^\s*Q([1-3])\s*:\s*(.*)$", line)
        if m:
            ans[int(m.group(1))] = m.group(2).strip()
    good = all(len(ans.get(i, "")) >= 20 and "replace this" not in ans[i] for i in (1, 2, 3))
    check(6, "answers.txt has real answers for Q1 to Q3 (your instructor reads them)", good, 2)

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
