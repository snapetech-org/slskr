# Benign Soulseek reproduction for ET SID 2055754

See the [operator guide](../../suricata-alerts.md) before applying any workaround.

This directory contains a synthetic packet trace using real slskR 0.2.86
user-info response bytes and the unchanged ET Open rule that misclassified
them. It is suitable for reproducing the collision without sharing a user's
network traffic or running malware. The replay never modifies a live sensor.

## Replay

Install Python 3 and Suricata, then run from the repository root:

```sh
python3 docs/security/suricata-2055754/replay.py --suricata suricata
```

Logs go to a new temporary directory printed by the command. Use
`--output /path/to/test-output` to select another directory. Root access and
live packet capture are not needed for offline replay. The script uses an
isolated configuration, checks the input hashes, and runs six cases:

| Case | SID 2055754 alerts | Simulated blocked packets in Suricata 7.0.3 |
| --- | ---: | ---: |
| Original `alert` rule | 1 | 0 |
| Suppress SID for the fixture destination | 0 | 0 |
| Suppress SID for a different destination | 1 | 0 |
| Suppress SID with a separate control signature loaded | 0; control signature still alerts once | 0 |
| Rule action changed locally to `drop` | 1 | 1 |
| `drop` rule with alert suppression | 0 | 10 |

The last two cases are deliberately modified **temporary copies** illustrating
the effect of an appliance converting the rule to `drop`. The original ET rule
remains unchanged. `--simulate-ips` reports what this engine would block;
no packets are transmitted or dropped on a real network. Exact packet counts
can differ with engine versions; the script checks that suppression still
does not resolve blocking. Review any changed behavior in the emitted logs.
The [recorded six-case result](observed-suricata-7.0.3.json) is included for
comparison with a fresh replay.

## Fixture provenance and limits

- Application: official `slskr-v0.2.86-x86_64-unknown-linux-gnu.tar.gz`, checked
  against the release's `SHA256SUMS.txt`. Archive SHA-256:
  `c9878466be8dd224baf1038fc1dc3874a3d6dd755af23d885ef19df99034a2c4`.
- Binary SHA-256:
  `a3d124c4dc3e739b33ddec7333790191987a9fac81391a29f327142db0a4c28d`.
- Profile: 46 ASCII bytes, `Music is for sharing. Enjoy browsing my albums`, no
  picture, 20 upload slots, queue size zero, a free slot, no optional
  upload-permissions field. These are ordinary user-info values.
- Response: 68 bytes, beginning `40 00 00 00 10 00 00 00`. The whole response
  SHA-256 is `81ba3402d018734b22f8b8cf5b0f8a1ea1c073bdbc1519698edc986cd2bf9ac4`.
- Actual collection: ten user-info requests over ten separate loopback TCP
  connections to the release daemon. Soulseek auto-connect, DHT, version
  checking and HTTPS were disabled; no network credentials were used.
- Offline trace: **generated Ethernet/IP/TCP headers, packet boundaries,
  addresses, and timestamps** around those response bytes. It has ten distinct
  TCP connections and a common source IP, `198.51.100.23:2234`, replying to
  `10.23.0.2:55000` through `10.23.0.2:55009`. The alert is on the tenth reply.
- PCAP SHA-256:
  `24eb3bdab6f61dc41933c736424183e46bbdfc933d2db0b13b6bcf340cb0fb34`.
- Rule: SID 2055754, revision 1, from the official ET Open Suricata 7.0.3 rules
  downloaded on 2026-11-09. The original rule line, including its newline,
  hashes to `5e8dd22e30fe36c78ef94c827a50cf01cf3a1037e74ecb6b04c99869739573f6`.
  Its BSD license/copyright header is retained in [2055754.rules](2055754.rules).

The source-code investigation used commit
`2f212d3c5090566b38adb24275570102ca8c6b90`. Typed user-info and queue-position
messages passed codec round trips. Seven separate negative controls for
payload length, count, ports, timing and direction did not alert. Those broader
results are described in the operator guide; this directory retains the
release-response PCAP and the independently replayable mitigation cases.

This is not a raw capture from any deployment. It proves a benign pattern can
match this specific rule; it cannot classify someone else's alert or certify
their container. Checksums establish consistency with the publisher's release,
not independent supply-chain assurance. No upstream rule fix is claimed.

## Source references

- [slskR v0.2.86 release](https://github.com/snapetech-org/slskr/releases/tag/v0.2.86)
- [ET Open rule source](https://rules.emergingthreats.net/open/suricata-7.0.3/rules/emerging-malware.rules)
- [Message framing](../../../crates/slskr-protocol/src/frame.rs)
- [Peer response encoding](../../../crates/slskr-protocol/src/peer.rs)
- [Suricata suppression behavior](https://docs.suricata.io/en/suricata-7.0.3/configuration/global-thresholds.html)
