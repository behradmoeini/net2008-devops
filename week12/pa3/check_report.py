import json, sys, urllib.request
import xml.etree.ElementTree as ET

def get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        if r.status != 200:
            raise ValueError(f"{url} answered {r.status}")
        return r.read().decode()

def main():
    if len(sys.argv) != 2:
        print("usage: python check_report.py BASE_URL")
        sys.exit(2)
    base = sys.argv[1].rstrip("/")
    try:
        j = json.loads(get(base + "/summary.json"))["total_requests"]
        x = int(ET.fromstring(get(base + "/summary.xml")).findtext("total_requests"))
        if j != x:
            raise ValueError(f"JSON says {j}, XML says {x}")
    except Exception as e:
        print(f"FAIL {e}")
        sys.exit(1)
    print(f"OK total_requests={j}")

main()
