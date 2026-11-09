#!/usr/bin/env python3
"""Replay benign Soulseek bytes offline; never changes a running sensor.

The checked-in PCAP has generated packet headers and genuine slskR 0.2.86
user-info response bytes. Suricata's --simulate-ips reports hypothetical drops;
this tool never transmits packets or changes the host's firewall.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent
PCAP_SHA256 = "24eb3bdab6f61dc41933c736424183e46bbdfc933d2db0b13b6bcf340cb0fb34"
RULE_SHA256 = "5e8dd22e30fe36c78ef94c827a50cf01cf3a1037e74ecb6b04c99869739573f6"
SID = 2055754
CONTROL_SID = 9905754


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suricata", default="suricata", help="Suricata executable")
    parser.add_argument("--output", type=Path, help="Log directory; defaults to a new temporary directory")
    args = parser.parse_args()
    output = (args.output or Path(tempfile.mkdtemp(prefix="slskr-suricata-"))).resolve()
    output.mkdir(parents=True, exist_ok=True)
    pcap = HERE / "benign-userinfo.pcap"
    if hashlib.sha256(pcap.read_bytes()).hexdigest() != PCAP_SHA256:
        raise RuntimeError("The benign PCAP differs from the recorded reproduction")
    rules = [line for line in (HERE / "2055754.rules").read_text().splitlines() if line.startswith("alert ")]
    if len(rules) != 1 or hashlib.sha256((rules[0] + "\n").encode()).hexdigest() != RULE_SHA256:
        raise RuntimeError("The fixture must use the recorded, unchanged ET rule")
    rule = rules[0] + "\n"
    version = subprocess.check_output([args.suricata, "-V"], text=True).strip()
    (output / "classification.config").write_text(
        "config classification: command-and-control,Malware Command and Control Activity Detected,1\n"
    )
    (output / "reference.config").write_text("")
    suppression = "suppress gen_id 1, sig_id 2055754, track by_dst, ip 10.23.0.2\n"
    control = rule.replace(f"sid:{SID};", f"sid:{CONTROL_SID};").replace(
        "ET MALWARE VenomRAT CnC Server Keepalive", "FIXTURE unrelated signature remains active"
    )
    cases = [
        ("alert-baseline", rule, "", 1, False, 0),
        ("alert-scoped-suppression", rule, suppression, 0, False, 0),
        ("alert-other-destination", rule, suppression.replace("10.23.0.2", "10.23.0.3"), 1, False, 0),
        ("alert-other-signature", rule + control, suppression, 0, False, 1),
        ("drop-baseline", rule.replace("alert tcp", "drop tcp", 1), "", 1, True, 0),
        ("drop-with-suppression", rule.replace("alert tcp", "drop tcp", 1), suppression, 0, True, 0),
    ]
    results = []
    for name, case_rule, threshold, expected_alerts, expected_blocking, expected_control in cases:
        case = output / name
        case.mkdir(exist_ok=True)
        (case / "rule.rules").write_text(case_rule)
        (case / "threshold.config").write_text(threshold)
        (case / "eve.json").unlink(missing_ok=True)
        config = """%YAML 1.1
---
vars:
  address-groups:
    HOME_NET: "[10.23.0.0/24]"
    EXTERNAL_NET: "!$HOME_NET"
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert:
            payload: yes
            packet: yes
        - stats
logging:
  default-log-level: notice
  outputs:
    - console:
        enabled: yes
"""
        for key, path in [
            ("classification-file", output / "classification.config"),
            ("reference-config-file", output / "reference.config"),
            ("threshold-file", case / "threshold.config"),
        ]:
            config += f"{key}: {json.dumps(str(path))}\n"
        (case / "suricata.yaml").write_text(config)
        cmd = [args.suricata, "--runmode", "single", "--simulate-ips", "-c", str(case / "suricata.yaml"),
               "-S", str(case / "rule.rules"), "-r", str(pcap), "-l", str(case)]
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        (case / "console.txt").write_text(run.stdout + run.stderr)
        if run.returncode:
            raise RuntimeError(f"{name}: Suricata exited {run.returncode}; see {case / 'console.txt'}")
        events = [json.loads(line) for line in (case / "eve.json").read_text().splitlines()]
        alerts = [event["alert"] for event in events if event.get("event_type") == "alert"]
        stats = [event["stats"] for event in events if event.get("event_type") == "stats"]
        if not stats or "ips" not in stats[-1]:
            raise RuntimeError(f"{name}: missing IPS statistics; cannot validate blocking")
        blocked = stats[-1]["ips"]["blocked"]
        actual_alerts = sum(alert["signature_id"] == SID for alert in alerts)
        control_alerts = sum(alert["signature_id"] == CONTROL_SID for alert in alerts)
        passed = (actual_alerts == expected_alerts and bool(blocked) == expected_blocking
                  and control_alerts == expected_control)
        result = {"case": name, "sid_2055754_alerts": actual_alerts,
                  "control_alerts": control_alerts, "simulated_blocked_packets": blocked, "passed": passed}
        results.append(result)
        print(json.dumps(result), flush=True)
    (output / "summary.json").write_text(json.dumps({"engine": version, "results": results}, indent=2) + "\n")
    print(f"Evidence: {output}")
    if not all(result["passed"] for result in results):
        raise SystemExit("Observed behavior differs from the recorded reproduction; inspect the logs.")


if __name__ == "__main__":
    main()
