#!/usr/bin/env python3
"""Week 11 lab self-check (NET2008 DevOps).

Run it from inside your lab folder (bytown-iac), after Part 4:

    python3 /path/to/W11_Lab_selfcheck.py --seed 17

It reads your files, runs `terraform fmt -check` and `terraform validate`, and
asks Docker and Git for information. It changes nothing. Use your own seed: the
sum of the last four digits of your student ID.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="sum of the last four digits of your student ID")
    seed = ap.parse_args().seed
    if not 0 < seed <= 36:
        sys.exit("The seed must be between 1 and 36.")

    root = Path.cwd()
    if root.name != "bytown-iac":
        sys.exit("Run this from the folder ~/bytown-iac.")

    results = []

    def check(part, description, passed, points):
        results.append((part, description, bool(passed), points))

    def read(rel):
        p = root / rel
        return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

    # ---- Part 1 (3 points)
    vf = read("vagrant/Vagrantfile")
    check(1, f'The Vagrantfile has the host name bytown-vm-{seed}', f'config.vm.hostname = "bytown-vm-{seed}"' in vf, 1)
    check(1, f'The Vagrantfile has the private address 192.168.56.{10 + seed}',
          f'ip: "192.168.56.{10 + seed}"' in vf and "private_network" in vf, 1)
    check(1, f'The Vagrantfile has the provisioning line for seed={seed}', f"seed={seed}" in vf and "provision" in vf and "ubuntu/jammy64" in vf, 1)

    # ---- Part 2 (6 points)
    tf = root / "terraform"
    main_tf, var_tf, out_tf = read("terraform/main.tf"), read("terraform/variables.tf"), read("terraform/outputs.tf")
    check(2, "main.tf, variables.tf and outputs.tf exist and use the Docker provider, a network and count",
          "kreuzwerker/docker" in main_tf and "docker_network" in main_tf and "count" in main_tf
          and 'variable "seed"' in var_tf and "output" in out_tf, 1)
    if run("terraform", "version")[0] == 0:
        rc, out = run("terraform", "fmt", "-check", "-diff", cwd=tf)
        check(2, "terraform fmt -check passes (the code is formatted)", rc == 0, 1)
        rc, out = run("terraform", "validate", "-no-color", cwd=tf)
        check(2, "terraform validate passes", rc == 0 and "valid" in out.lower(), 1)
    else:
        check(2, "terraform fmt -check passes (Terraform is not installed: cannot check)", False, 1)
        check(2, "terraform validate passes (Terraform is not installed: cannot check)", False, 1)
    tfvars = {}
    for line in read("terraform/terraform.tfvars").splitlines():
        m = re.match(r"^\s*(\w+)\s*=\s*(\d+)\s*$", line)
        if m:
            tfvars[m.group(1)] = int(m.group(2))
    check(2, f"terraform.tfvars has seed = {seed}", tfvars.get("seed") == seed, 1)
    out2 = read("evidence/part2-output.txt")
    check(2, f"evidence/part2-output.txt lists the ports {8500 + seed} and {8501 + seed}", f":{8500 + seed}" in out2 and f":{8501 + seed}" in out2, 1)
    c0, c1 = read("evidence/part2-curl0.txt"), read("evidence/part2-curl1.txt")
    check(2, "The two evidence pages show your seed and instance 0 and 1",
          f"Seed: {seed}, instance: 0" in c0 and f"Seed: {seed}, instance: 1" in c1, 1)

    # ---- Part 3 (4 points)
    plan = read("evidence/part3-plan.txt")
    check(3, "evidence/part3-plan.txt shows the drift: Plan: 1 to add, 0 to change, 0 to destroy", "Plan: 1 to add, 0 to change, 0 to destroy" in plan, 2)
    st = read("evidence/part3-state.txt")
    n = len(re.findall(r"docker_container\.web\[\d+\]", st))
    check(3, "evidence/part3-state.txt lists three containers", n == 3, 1)
    check(3, f"evidence/part3-curl2.txt shows instance 2 with your seed", f"Seed: {seed}, instance: 2" in read("evidence/part3-curl2.txt"), 1)

    # ---- Part 4 (4 points)
    rc, tracked = run("git", "ls-files", cwd=root)
    files = tracked.splitlines() if rc == 0 else []
    rc, ever = run("git", "log", "--all", "--name-only", "--format=", cwd=root)
    everything = set(files) | set(ever.splitlines())
    check(4, "No .tfstate file was ever committed", not any(".tfstate" in f for f in everything), 1)
    ign = [l.strip() for l in read(".gitignore").splitlines()]
    check(4, ".gitignore lists .terraform/ and *.tfstate", ".terraform/" in ign and "*.tfstate" in ign, 1)
    check(4, "terraform/.terraform.lock.hcl is committed", "terraform/.terraform.lock.hcl" in files, 1)
    rc, left = run("docker", "ps", "-a", "--filter", f"name=bytown-tf-{seed}", "--format", "{{.Names}}")
    after = read("evidence/part4-after-destroy.txt")
    check(4, "Everything is destroyed: no container is left and the proof file shows only the header",
          rc == 0 and left == "" and "bytown-tf" not in after.replace("name=", "") and "CONTAINER ID" in after, 1)

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
