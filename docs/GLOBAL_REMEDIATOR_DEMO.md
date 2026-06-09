# 🤖 Global Remediator — Feature Demo

**Human-in-the-Loop Security Orchestration & Automation (SOAR) Agent**

The Global Remediator is SecureGlass's orchestration layer. It closes the gap between *detection*
(what the 20 controls surface) and *response* (what a human decides to do about it) — without ever
taking autonomous action on production systems.

---

## Why it exists

A single-pane-of-glass that only *shows* alerts still leaves the analyst to figure out the fix,
in the right tool, with the right blast-radius judgement. The Global Remediator drafts that fix
automatically for every meaningful alert — but enforces a hard rule: **a human must approve before
anything executes.** This is the SOAR component that the dashboard was missing.

---

## The core guarantee: human-in-the-loop

```
Detection → Global Remediator drafts a plan → HUMAN decides → (only then) execution
```

| Severity | Remediator behaviour |
|----------|----------------------|
| 🔴 CRITICAL | Drafts plan, pages on-call, **blocks auto-execution**, demands approval (co-sign for OT/medical safety-critical assets) |
| 🟠 HIGH | Drafts plan, queues for analyst approval |
| 🟡 MEDIUM | Drafts plan, queues for analyst approval |
| 🟢 LOW / INFO | Auto-closed, logged, **no human prompt** |

The agent never clicks "execute" itself. Approve / Reject / Defer is always a human action.

---

## Demo walkthrough

> Open `frontend/index.html` and click **🤖 Global Remediator** in the top navigation.

### 1. The agent header
Shows live counters: **Awaiting Approval**, **Approved**, and **Total Actioned**. These update in
real time as you make decisions.

### 2. The approval queue
Each card represents one alert the Remediator has triaged. A card contains:
- The original alert (severity, asset, source tool)
- **🤖 Global Remediator proposed plan** — an ordered, tool-specific remediation sequence
- **Impact assessment** — blast radius and business-disruption estimate in plain English
- **AI confidence** — how sure the agent is about the proposed plan

### 3. Make a decision
Three buttons on every pending card:
- **✓ Approve** — the plan is "dispatched" to the relevant control (CrowdStrike, Wiz, Qualys…) and the card shows a confirmation banner
- **✕ Reject** — no action taken; the item returns to the SOC queue
- **⏸ Defer** — snoozed for 4 hours, then re-prompted

### 4. The audit log
Every decision is written to the **Decision Audit Log** on the right with the verb, the alert,
the tool, and a timestamp — the tamper-evident trail auditors require (SOC 2 CC7.4, ISO 27001
A.5.26, NIST CSF RS.MI, DORA).

### 5. Switch verticals
Change the industry vertical (top bar) and the queue repopulates with sector-appropriate
remediations — e.g. *"Quarantine infusion pump to isolated clinical VLAN — DO NOT power off
(patient safety)"* for Healthcare, or *"Engage plant safety engineer — manual SIS verification"*
for Oil & Gas. Use **Reset Demo** to clear the log and start over.

---

## Example: a Healthcare CRITICAL

> **Alert:** Infusion pump lateral movement toward EMR server (Claroty)
>
> **🤖 Proposed plan:**
> 1. Quarantine infusion pump to isolated clinical VLAN
> 2. Block east-west traffic to EMR subnet at OT firewall
> 3. Alert biomedical engineering — DO NOT power off (patient safety)
> 4. Engage clinical continuity team for affected ward
>
> **Impact:** Network-isolates 1 device WITHOUT interrupting patient care. Clinical sign-off required.
> **AI confidence:** 88%

The analyst reads the plan, confirms it won't endanger a patient, and clicks **Approve** — at which
point (in production) the actions dispatch to Claroty and the OT firewall. Nothing happened until
the human said so.

---

## Production behaviour (Phase 2)

In the live system the Remediator:
1. Subscribes to the Risk Scorer output stream
2. Calls Claude to generate the plan (see `generate_remediation_plan()` in [LLD §4.4](./LLD.md))
3. Persists it to the `remediations` table with `status=PENDING`
4. Surfaces it in the queue via `GET /api/v1/remediations?status=PENDING`
5. On approval, dispatches to the target control's API and writes an immutable audit record

See the [LLD](./LLD.md) section 4.4 for the schema, state machine, prompt, and API endpoints.
