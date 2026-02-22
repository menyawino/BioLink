#!/usr/bin/env python3
"""Check NiFi pipeline status."""
import json, requests, sys
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

NIFI_URL = "https://localhost:8443"

# Auth
resp = requests.post(f"{NIFI_URL}/nifi-api/access/token",
    data={"username": "admin", "password": "biolink_nifi_secret_123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    verify=False, timeout=15)
TOKEN = resp.text.strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Get status
r = requests.get(f"{NIFI_URL}/nifi-api/flow/process-groups/root/status",
    params={"recursive": "true"}, headers=HEADERS, verify=False, timeout=30)
data = r.json()
snap = data["processGroupStatus"]["aggregateSnapshot"]

print(f"FlowFiles Queued: {snap['flowFilesQueued']}")
print(f"Bytes Queued: {snap['bytesQueued']}")
print()

for ps in snap.get("processorStatusSnapshots", []):
    s = ps["processorStatusSnapshot"]
    print(f"  {s['name']:40s} {s['runStatus']:10s} in={s['flowFilesIn']:>5}  out={s['flowFilesOut']:>5}  tasks={s['taskCount']:>5}")

# Also check connections for queued items
print()
r2 = requests.get(f"{NIFI_URL}/nifi-api/flow/process-groups/root",
    headers=HEADERS, verify=False, timeout=30)
flow = r2.json()
for conn in flow.get("processGroupFlow", {}).get("flow", {}).get("connections", []):
    cs = conn.get("status", {}).get("aggregateSnapshot", {})
    name = cs.get("name", "unnamed")
    queued = cs.get("queued", "0")
    if queued != "0 (0 bytes)":
        print(f"  Queue [{name}]: {queued}")

# Check bulletins
r3 = requests.get(f"{NIFI_URL}/nifi-api/flow/bulletin-board",
    params={"limit": "10"}, headers=HEADERS, verify=False, timeout=30)
bulletins = r3.json().get("bulletinBoard", {}).get("bulletins", [])
if bulletins:
    print("\nRecent Bulletins:")
    for b in bulletins[:5]:
        bb = b.get("bulletin", {})
        print(f"  [{bb.get('level','?')}] {bb.get('sourceComponent','?')}: {bb.get('message','?')[:200]}")
