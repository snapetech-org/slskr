# Suricata / IDS alerts and Soulseek

**A controlled false positive has been reproduced for Emerging Threats SID
2055754, revision 1, `ET MALWARE VenomRAT CnC Server Keepalive`.** Valid
Soulseek replies can satisfy this rule. Confirm the actual signature and
matching traffic before classifying an alert from your installation as benign.
This finding does not establish that an arbitrary container or host is clean.

Some firewalls display `ET TROJAN` instead of `ET MALWARE`. Compare the
generator ID, signature ID, revision, and deployed rule text; a shortened
label such as “Venom” is insufficient. Certificate, HTTP, DNS, and reputation
alerts are outside this finding.

## What was verified

On 2026-11-09, Suricata **7.0.3** with the unchanged ET Open rule alerted on:

- User-info and queue-position replies encoded and decoded by slskR's protocol
  crate at commit `2f212d3c5090566b38adb24275570102ca8c6b90`.
- User-info reply bytes received from the official Linux **slskR 0.2.86**
  binary, whose archive matched the publisher's release checksum.

The release test used a valid **46-byte ASCII profile description**, no picture,
and no optional upload-permissions field. Ten requests on ten separate local
TCP connections returned 68-byte replies. Replaying the response bytes in
generated TCP packets triggered the rule on the tenth reply. A queue-position
reply for a 52-byte filename also matched. Seven negative controls covered
67/69-byte replies, nine matches, ports outside the rule's ranges, matches
outside its time window, and the opposite direction.

**The packet headers, addresses, timing, and segmentation were synthesized for
offline replay.** These are benign fixtures, not captures from a reported
deployment. The application response bytes were obtained from the real binary.
The investigation did not examine a reporter's container image or perform a
complete supply-chain audit. See the [reproduction evidence](security/suricata-2055754/README.md).

## Why the rule can match ordinary traffic

The tested rule has these conditions:

| Condition | Value |
| --- | --- |
| Flow | Established TCP, toward the endpoint that initiated the connection |
| Source | `$EXTERNAL_NET`, TCP source port 1024 or higher |
| Destination | `$HOME_NET`, TCP destination port 49152 or higher |
| TCP payload | Exactly 68 bytes, starting with `40 00 00 00` |
| Following four bytes | Must not all be zero |
| Alert threshold | Ten matches from the same source IP within 120 seconds, including across connections |

Soulseek's regular message framing writes a little-endian length followed by
a 32-bit message code and the message body. A 60-byte body produces a 68-byte
frame: four bytes for length 64, four bytes for the message code, and 60 bytes
of body. Valid examples begin with:

```text
40 00 00 00 10 00 00 00   UserInfoResponse (code 16)
40 00 00 00 2c 00 00 00   PlaceInQueueResponse (code 44)
```

The rule does not decode Soulseek. Its pattern can match these messages when
TCP segmentation produces a matching 68-byte packet payload. It does not
identify a malicious executable. The rule's Windows metadata does not prevent
it from matching traffic involving Linux containers.

## Verify an alert from your installation

1. Preserve the exact alert, including `alert.signature`, `alert.signature_id`,
   `alert.gid`, `alert.rev`, timestamp, `flow_id`, source/destination IPs and
   ports, and `alert.action`. Record the Suricata/firewall version and ruleset.
2. Record `slskr version`, the image reference, and its immutable image digest.
   Docker operators can inspect their own container without dumping its
   environment or credentials:

   ```sh
   docker inspect --format '{{.Config.Image}} {{.Image}}' slskr
   docker image inspect --format '{{json .RepoDigests}}' \
     "$(docker inspect --format '{{.Image}}' slskr)"
   ```

   `.Image` is a local image ID; `RepoDigests` records registry digests when
   available. An empty digest list is possible for locally built images.
3. Establish which endpoints the sensor sees. Docker NAT, a shared host, and
   a VPN can change the observed IPs. A container's published peer port is not
   necessarily the destination port of an outbound connection's reply.
4. Decode the matching packet/flow as Soulseek and check the rule conditions.
   Match the traffic to an expected user-info, queue, or other peer operation.
   A matching SID or the first four bytes alone is not enough.

An EVE alert may contain only the triggering packet, so it may not demonstrate
all ten matches. Use the associated flow records or a short, relevant packet
capture when available. Avoid posting raw captures publicly: other packets
can contain credentials, usernames, filenames, or private messages. Prefer
the synthetic fixture below when reporting the rule collision upstream.

## Resolve a confirmed false positive

### Prefer a correction to the detection rule

Update the sensor's supported ruleset and check whether the deployed rule has
changed. The investigation verified revision 1; updating alone is not proof
of a fix. Report the collision to [Emerging Threats feedback](https://feedback.emergingthreats.net/)
or the [ET community](https://community.emergingthreats.net/), including the SID,
revision, Suricata version, the benign fixture, and its reproduction command.
The fixture has no deployment credentials or private traffic.

A provider correction can address every affected client. slskR cannot update
an operator's firewall rules, and this document does not claim that ET has
accepted or released a correction. For a managed firewall, involve its vendor
if it repackages or overrides ET signatures.

### If only notifications need silencing

After validating the actual traffic, an operator can suppress **this one SID
for a dedicated slskR destination IP** using Suricata's threshold configuration.
Example only, using a documentation address:

```text
# Replace 192.0.2.10 with the dedicated destination IP seen by this sensor.
suppress gen_id 1, sig_id 2055754, track by_dst, ip 192.0.2.10
```

This matches the inbound reply direction of the tested rule. It suppresses
this SID for **all traffic to that IP**, not only the slskR process, and can
hide a genuine match to the same SID there. Do not use a shared NAT/VPN/host IP
as if it isolated one container. Keep other signatures active, record the
reason and review date, and remove the exception after a verified rule fix.
Use the firewall's supported configuration mechanism, validate it, and reload
the sensor; do not edit a generated rules file that an update will overwrite.

**Suppression does not necessarily stop IPS drops.** It suppresses alerts,
while rule actions and flowbit changes can remain active. In the offline
Suricata 7.0.3 IPS simulation, changing this rule's action to `drop` and then
adding suppression still blocked the matching traffic. See the
[replay tool](security/suricata-2055754/replay.py) for the measured distinction.

### If the firewall is blocking transfers

Check the deployed action: the upstream tested rule is `alert`, but appliances
can turn it into `drop` or `reject`. For a verified false positive, use a
vendor-supported action exception limited to **SID 2055754 and an isolated
slskR endpoint**, retaining inspection by other rules. Confirm that transfers
recover and the exception affects only the intended traffic. If that scope
is unavailable, request a provider correction instead of a broad allowlist.

Disabling this SID globally loses its detection everywhere. A blanket
container/peer `pass` rule or bypass can skip other detections too. Neither is
a suitable default workaround for this finding.

## Can slskR prevent it in application code?

There is no general, compatibility-preserving slskR switch that guarantees
this third-party signature will never match:

- Changing a profile's byte length can remove that particular 68-byte
  user-info reply, but other valid replies and other peers can still match.
- Padding or changing Soulseek frame lengths would change the wire protocol.
  The receiving client also does not control how remote peers encode replies.
- Splitting writes, adjusting TCP buffering, changing ports, or slowing
  requests cannot reliably control packet boundaries and the sensor's
  address/port view through NAT. These are not recommended fixes.
- Soulseek peer obfuscation depends on peer support and connection mode; it
  does not cover all traffic or establish that an alert is benign. It is not
  a security or remediation guarantee.

The supported approach is diagnosis, a corrected signature, and an explicitly
scoped operator workaround when necessary. slskR does not automatically weaken
firewall protections or alter valid protocol messages to avoid this alert.

## References

- [ET rule announcement](https://community.emergingthreats.net/t/ruleset-update-summary-2024-09-05-v10682/1948)
- [Official ET Open rule source](https://rules.emergingthreats.net/open/suricata-7.0.3/rules/emerging-malware.rules)
- [Suricata threshold and suppression documentation](https://docs.suricata.io/en/suricata-7.0.3/configuration/global-thresholds.html)
- [Suricata pass rules and traffic bypass](https://docs.suricata.io/en/suricata-7.0.3/performance/ignoring-traffic.html)
- [Suricata rule management](https://docs.suricata.io/en/suricata-7.0.3/rule-management/suricata-update.html)
- [Soulseek frame encoder](../crates/slskr-protocol/src/frame.rs)
- [Soulseek peer-message encoders](../crates/slskr-protocol/src/peer.rs)
