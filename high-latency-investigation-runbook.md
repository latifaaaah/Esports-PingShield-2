# Runbook: High Latency Investigation

**Category:** Network Operations
**Related Project:** Esports-PingShield
**Severity Scope:** General network latency issues (applicable to both standard NOC environments and esports/event environments)

---

## 1. Overview

This runbook defines the standard procedure for investigating reports of high network latency. It follows a layered diagnostic approach (based on the OSI model) to isolate whether the root cause is network-related or application-related, and to distinguish between **expected latency** (due to geographic distance) and **anomalous latency** (indicating an actual issue).

---

## 2. Incident Severity

| Level | Criteria |
|---|---|
| **P1 — Critical** | Packet loss present; multiple players/devices affected; active gameplay/live event impact |
| **P2 — High** | Elevated jitter with no packet loss; limited/specific group of users affected |
| **P3 — Medium** | Latency above baseline but stable (low jitter, 0% loss); single device or isolated segment affected |
| **P4 — Low** | Minor deviation from baseline within normal variance; no reported user impact |

Severity determines response urgency and escalation path (see Section 8).

---

## 3. Trigger / Detection

This runbook is triggered when:
- Esports-PingShield (or equivalent monitoring tool) flags latency above the defined threshold (e.g. >150ms for local traffic)
- A user or player reports lag/slow connection
- Round-trip time (RTT) baseline deviates significantly from historical norms

---

## 4. Initial Triage (First 5 Minutes)

Before deep diagnosis, answer these three questions:

| Question | Why it matters |
|---|---|
| Is the issue affecting one device or everyone? | Determines if it's a local device issue or a network-wide issue |
| Is it affecting all destinations or one specific destination? | Determines if it's a local network problem or a routing/remote server problem |
| Is it constant or intermittent? | Changes which diagnostic tool and time window to use |

---

## 5. Decision Tree

```
High Latency Detected
        │
        ▼
One device or multiple?
        │
        ▼
One destination or all destinations?
        │
        ▼
Packet loss present?
   │            │
  Yes           No
   │            │
   ▼            ▼
 P1/P2      Jitter (stddev) high?
              │            │
             Yes           No
              │            │
              ▼            ▼
         Local hop     International hop
         (real fault)  (likely propagation delay)
              │            │
              ▼            ▼
          Root Cause Identified
                   │
                   ▼
          Resolution / Escalation
```

This tree mirrors the diagnostic logic in Sections 6–7 in a scannable format for quick reference during a live incident.

---

## 6. Diagnosis Steps

### Step 6.1 — Establish Baseline
Compare current latency against known-good historical values. Without a baseline, no latency figure has meaningful context.

### Step 6.2 — Basic Connectivity & RTT Check
```bash
ping -c 30 <destination>
```
Capture:
- `avg` (round-trip average) — the primary comparison metric
- `stddev` (jitter) — measures connection *stability*, independent of raw speed
- `packet loss %` — any value above 0% indicates dropped packets

**Interpretation guide:**
- High avg + low stddev + 0% loss → likely just geographic distance (propagation delay), not a fault
- High avg + high stddev → indicates instability (congestion or unstable routing), not just distance
- Any packet loss → escalate priority regardless of avg/stddev values

### Step 6.3 — Path Isolation
```bash
traceroute <destination>
# or, for repeated sampling:
mtr -r -c 20 <destination>
```
Identify the hop(s) where latency jumps significantly. Cross-reference the hop's hostname/location against known geographic/network boundaries (e.g., regional ISP backbone handoffs, international carrier links).

**Key rule:** A large latency jump that aligns with a known international hop (e.g., a regional-to-international backbone handoff) is expected and not inherently a fault. A large jump *within* the same local/regional segment is the real red flag.

**Note on `* * *` responses:** Some routers do not respond to ICMP (used by traceroute/ping) for security or policy reasons. This does **not** mean the packet was dropped — only that the router silently forwards traffic without replying to probes. Do not treat this alone as evidence of an issue.

### Step 6.4 — Deeper Checks (if Steps 6.2–6.3 don't explain the issue)
- Bandwidth utilization on the local link (is it saturated?)
- QoS configuration (is latency-sensitive traffic being deprioritized?)
- CPU/memory load on local network hardware (an overloaded router/switch causes queuing delay)
- For esports/event contexts specifically: check for Wi-Fi congestion from high device density (crowd + player devices on the same venue network), and check for bufferbloat on the streaming/broadcast link

---

## 7. Resolution

Resolution path depends on diagnosis outcome:

| Root Cause Identified | Action |
|---|---|
| Expected geographic propagation delay | No action needed — document as baseline, close ticket |
| Local congestion / Wi-Fi saturation | Reduce contending traffic, isolate critical devices to a separate SSID/VLAN if available |
| Faulty hop / routing instability | Escalate to ISP or upstream provider with traceroute evidence |
| Application-layer delay (not network) | Redirect to application/dev team with network evidence ruling out transport-layer cause |

### 7.1 Post-Mitigation Validation

An incident is not closed once a fix is applied — it is closed once the fix is *verified*. After any resolution action:

1. **Re-run the baseline test:** `ping -c 30 <destination>` (same parameters as the original diagnostic test)
2. **Compare avg/stddev/packet loss** against both the pre-incident baseline and the during-incident readings — confirm all three have returned to healthy ranges
3. **Confirm no lateral impact:** verify the issue has not shifted to a different zone/segment/device group (e.g., fixing congestion on one venue Wi-Fi zone shouldn't push load onto an adjacent zone)
4. **Sustained check:** re-test after a short interval (e.g., 10–15 minutes) to confirm the fix holds under continued load, not just at the moment of intervention
5. **Log closure:** record final readings in the incident log before marking resolved

Skipping this step is a common failure mode — a fix that looks correct at the moment of action can silently regress or relocate the problem.

---

## 8. Escalation Path

Escalate when:
- Packet loss > 0% persists across repeated tests
- Jitter (stddev) exceeds an agreed threshold (context-dependent — tighter thresholds apply in esports/live-event scenarios where jitter affects gameplay more than raw latency)
- The problematic hop is outside your organization's control (e.g., ISP backbone)

Escalate to: [Define based on your organization structure — e.g., ISP support / Network Engineering team / Venue IT]

---

## 9. Post-Incident Notes

Document for every investigation:
```
Date:
Command(s) used:
Baseline (expected avg):
Observed avg / stddev / packet loss:
Traceroute — hop where latency jump occurred:
Conclusion (expected vs. anomalous):
Action taken:
```

---

## 10. Planned Integration — PingShield Disaster Injector

*Status: Planned / Not yet implemented.*

The intent is to connect this runbook directly to Esports-PingShield's planned **Disaster Injector** module, turning the runbook from a reference document into a testable, repeatable training exercise:

1. **Inject:** Trigger a simulated latency/jitter/packet-loss event via the Disaster Injector (e.g., simulate an international-hop degradation or local Wi-Fi saturation)
2. **Detect:** PingShield's monitoring flags the anomaly, replicating a real Trigger/Detection event (Section 3)
3. **Respond:** The operator follows this runbook's Decision Tree and Diagnosis Steps against the simulated scenario
4. **Validate:** Apply Section 7.1 (Post-Mitigation Validation) against the injector's live readout to confirm resolution
5. **Score/Log:** Record time-to-diagnosis and time-to-resolution as training metrics

This turns the Technical Operations Training Lab from static documentation into a closed-loop training system — the same runbook used for reference during a real incident becomes the training exercise for a simulated one.

---

## 11. Key Diagnostic Principle

> Do not judge an issue by the absolute latency number alone. Always compare it against the expected baseline for that geographic distance, and check jitter and packet loss before concluding there is a fault. A junior response reacts to a high number; a professional response contextualizes it first.

---

## Appendix: Worked Example (Reference Data)

| Test | Avg | Stddev | Packet Loss | Conclusion |
|---|---|---|---|---|
| Local/regional destination | ~79.5 ms | ~10.4 ms | 0% | Healthy baseline |
| International destination (multi-region hop) | ~203.4 ms | ~8.8 ms | 0% | Elevated avg explained by propagation delay across international backbone hops; stability (low, comparable stddev) confirms no additional fault |
