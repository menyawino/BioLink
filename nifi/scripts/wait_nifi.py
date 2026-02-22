#!/usr/bin/env python3
import time, subprocess, sys

for i in range(40):
    print(f"Attempt {i+1}...")
    try:
        r = subprocess.run(
            ["curl", "-skf", "https://localhost:8443/nifi-api/system-diagnostics"],
            capture_output=True, text=True, timeout=8
        )
        if r.returncode == 0:
            print("NiFi is READY!")
            sys.exit(0)
    except Exception as e:
        print(f"  {e}")
    time.sleep(5)

print("TIMEOUT waiting for NiFi")
sys.exit(1)
