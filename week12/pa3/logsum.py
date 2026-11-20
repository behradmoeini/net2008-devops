import json, sys
from collections import Counter
import xml.etree.ElementTree as ET

def summarise(path):
    total = bad = nbytes = 0
    classes = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}
    paths, clients = Counter(), set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = line.split()
            if len(p) != 6 or not (len(p[4]) == 3 and p[4].isdigit() and p[4].isascii()) or not (p[5].isdigit() and p[5].isascii()):
                bad += 1
                continue
            total += 1
            nbytes += int(p[5])
            clients.add(p[1])
            paths[p[3]] += 1
            k = p[4][0] + "xx"
            if k in classes:
                classes[k] += 1
    top = sorted(paths.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    return {"total_requests": total, "malformed": bad, "status_classes": classes,
            "top_paths": [{"path": a, "count": b} for a, b in top],
            "total_bytes": nbytes, "unique_clients": len(clients)}

def to_xml(s):
    r = ET.Element("summary")
    for k in ("total_requests", "malformed"):
        ET.SubElement(r, k).text = str(s[k])
    sc = ET.SubElement(r, "status_classes")
    for k, v in s["status_classes"].items():
        ET.SubElement(sc, "class", name=k).text = str(v)
    tp = ET.SubElement(r, "top_paths")
    for t in s["top_paths"]:
        ET.SubElement(tp, "path", count=str(t["count"])).text = t["path"]
    for k in ("total_bytes", "unique_clients"):
        ET.SubElement(r, k).text = str(s[k])
    ET.indent(r)
    return ET.tostring(r, encoding="unicode")

def main():
    if len(sys.argv) != 3:
        print("usage: python logsum.py INPUT_LOG OUTPUT_FOLDER")
        sys.exit(2)
    try:
        s = summarise(sys.argv[1])
    except OSError as e:
        print(f"cannot read {sys.argv[1]}: {e}", file=sys.stderr)
        sys.exit(1)
    out = sys.argv[2]
    with open(f"{out}/summary.json", "w") as f:
        json.dump(s, f, indent=2)
    with open(f"{out}/summary.xml", "w") as f:
        f.write(to_xml(s) + "\n")
    print(json.dumps(s))

main()
