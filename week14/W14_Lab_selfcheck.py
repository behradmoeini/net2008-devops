#!/usr/bin/env python3
"""Week 14 lab self-check (NET2008 DevOps).

Run it from inside your lab folder (bytown-monitor):

    python3 /path/to/W14_Lab_selfcheck.py --seed 17

It reads your files and your proof. It changes nothing and does not need Docker
to be running. Use your own seed: the sum of the last four digits of your ID.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

VALID_STATUSES = {200, 301, 404, 500}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True, help="sum of the last four digits of your student ID")
    seed = ap.parse_args().seed
    if not 0 < seed <= 36:
        sys.exit("The seed must be between 1 and 36.")

    root = Path.cwd()
    if root.name != "bytown-monitor":
        sys.exit("Run this from the folder ~/bytown-monitor.")

    results = []

    def check(part, description, passed, points):
        results.append((part, description, bool(passed), points))

    def read(rel):
        p = root / rel
        return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

    def load_json(rel):
        try:
            return json.loads(read(rel))
        except ValueError:
            return None

    nagios_port, es_port, kibana_port = 8600 + seed, 8650 + seed, 8700 + seed
    n_events = 60 + seed
    host = f"bytown-web-{seed}"

    # ---- Part 1 (8 points)
    cfg = read("nagios/conf.d/bytown.cfg")
    hosts_ok = (re.search(rf"host_name\s+{re.escape(host)}\b", cfg) is not None
                and re.search(rf"address\s+bytown-target-{seed}\b", cfg) is not None)
    check(1, f"bytown.cfg defines the host {host} with the address bytown-target-{seed}", hosts_ok, 1)
    services_ok = (cfg.count("define service") >= 2
                   and re.search(r"service_description\s+HTTP\b", cfg) is not None
                   and re.search(r"service_description\s+Seed file\b", cfg) is not None
                   and re.search(rf"check_http!.*-s\s+seed={seed}\b", cfg) is not None)
    check(1, f"bytown.cfg has the services HTTP and Seed file, and the file check looks for seed={seed}", services_ok, 1)
    env = read("nagios/.env")
    compose = read("nagios/compose.yaml")
    check(1, f"nagios/.env has SEED={seed} and NAGIOS_PORT={nagios_port}",
          re.search(rf"^SEED={seed}$", env, re.M) is not None and re.search(rf"^NAGIOS_PORT={nagios_port}$", env, re.M) is not None, 1)
    check(1, "nagios/compose.yaml has the target and nagios containers named with ${SEED}, and mounts conf.d",
          "bytown-target-${SEED}" in compose and "bytown-nagios-${SEED}" in compose and "conf.d" in compose, 1)

    def service_states(rel):
        data = load_json(rel)
        try:
            sl = data["data"]["servicelist"]
            if host in sl:
                sl = sl[host]
            return {str(k): int(v) for k, v in sl.items()}
        except (TypeError, KeyError, ValueError, AttributeError):
            return {}

    ok_states = service_states("evidence/nagios-ok.json")
    check(1, "evidence/nagios-ok.json shows HTTP and Seed file with state 2 (OK)",
          ok_states.get("HTTP") == 2 and ok_states.get("Seed file") == 2, 2)
    crit_states = service_states("evidence/nagios-critical.json")
    check(1, "evidence/nagios-critical.json shows HTTP and Seed file with state 16 (CRITICAL)",
          crit_states.get("HTTP") == 16 and crit_states.get("Seed file") == 16, 2)

    # ---- Part 2 (8 points)
    es_env = read("elk/.env")
    es_compose = read("elk/compose.yaml")
    check(2, f"elk/.env has SEED={seed}, ES_PORT={es_port}, KIBANA_PORT={kibana_port}, and compose.yaml has es and kibana",
          re.search(rf"^SEED={seed}$", es_env, re.M) is not None
          and re.search(rf"^ES_PORT={es_port}$", es_env, re.M) is not None
          and re.search(rf"^KIBANA_PORT={kibana_port}$", es_env, re.M) is not None
          and "elasticsearch" in es_compose and "kibana" in es_compose and "bytown-es-${SEED}" in es_compose, 2)

    # The events you generated
    lines = [ln for ln in read("elk/events.ndjson").splitlines() if ln.strip()]
    docs = []
    shape_ok = len(lines) == 2 * n_events
    if shape_ok:
        try:
            for i in range(0, len(lines), 2):
                action, doc = json.loads(lines[i]), json.loads(lines[i + 1])
                if action.get("index", {}).get("_index") != "bytown-events" or doc.get("id") != i // 2 or doc.get("status") not in VALID_STATUSES:
                    shape_ok = False
                docs.append(doc)
        except (ValueError, AttributeError):
            shape_ok = False
    by_status = Counter(d.get("status") for d in docs)
    n_errors = sum(1 for d in docs if isinstance(d.get("status"), int) and d["status"] >= 500)

    bulk = load_json("evidence/es-bulk.json")
    bulk_ok = isinstance(bulk, dict) and bulk.get("errors") is False and len(bulk.get("items", [])) == n_events
    count = load_json("evidence/es-count.json")
    count_ok = isinstance(count, dict) and count.get("count") == n_events
    check(2, f"events.ndjson has {n_events} events for your seed; es-bulk.json shows no errors; es-count.json shows {n_events}",
          shape_ok and bulk_ok and count_ok, 2)

    agg = load_json("evidence/es-status.json")
    got = {}
    try:
        got = {int(b["key"]): int(b["doc_count"]) for b in agg["aggregations"]["by_status"]["buckets"]}
    except (TypeError, KeyError, ValueError):
        got = {}
    check(2, "evidence/es-status.json has the right number of events for each status code", shape_ok and got == dict(by_status), 2)

    err = load_json("evidence/es-errors.json")
    check(2, f"evidence/es-errors.json counts the server errors correctly ({n_errors} for your data)",
          shape_ok and isinstance(err, dict) and err.get("count") == n_errors and n_errors > 0, 2)

    # ---- Part 3 (4 points)
    ans = {}
    for line in read("answers.txt").splitlines():
        m = re.match(r"^\s*Q([1-4])\s*:\s*(.*)$", line)
        if m:
            ans[int(m.group(1))] = m.group(2).strip()
    good = all(len(ans.get(i, "")) >= 20 and "replace this" not in ans[i] for i in (1, 2, 3, 4))
    check(3, "answers.txt has real answers for Q1 to Q4 (your instructor reads them)", good, 4)

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
