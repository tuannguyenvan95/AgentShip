# ⚓ AgentShip: Protocol Architecture & Consensus Mechanics

## Overview
AgentShip is an autonomous maritime demurrage dispute and weather risk court deployed on GenLayer. It bridges international maritime law (BIMCO / Laytime Charterparty rules) with subjective AI validator consensus.

```mermaid
flowchart TD
    A["Charterer (Shipper)"] -->|"create_voyage_escrow (Locks Freight + Demurrage Buffer)"| B("AgentShip Escrow Contract")
    S["Syndicate Co-Funders"] -->|"pledge_voyage_escrow (Pools Additional Share)"| B
    C["Carrier (Shipowner)"] -->|"submit_voyage_logs (Links AIS Tracking & NOAA Weather)"| B
    
    B -->|"adjudicate_demurrage"| T["AI Maritime Tribunal (gl.vm.run_nondet)"]
    T -->|"gl.nondet.web.render"| AIS["AIS Live Coordinates & Port Arrival"]
    T -->|"gl.nondet.web.render"| W["NOAA/ECMWF Sea State & Waves"]
    
    T --> D{"Consensus Verdict"}
    D -->|"Waves >= 6m"| V1["FORCE_MAJEURE_EXCUSED (Demurrage Waived)"]
    D -->|"Delay > 0 & Waves < 6m"| V2["DEMURRAGE_ENFORCED (Penalty to Carrier)"]
    D -->|"Delay == 0"| V3["CLEAN_ON_TIME (100% Payout to Carrier)"]
    
    V1 --> W1["Cooling-off Challenge Window (12h Fast-Track / 24h Standard)"]
    V2 --> W1
    V3 --> W1
    
    W1 -->|"Appeal within Window + 10% Bond"| APP["Supreme Appellate Jury"]
    W1 -->|"finalize_settlement after Window"| PAY["Native Transfer Payout Execution"]
```

## Consensus Security & Injection Defense
1. **Security Canary Token**: `CANARY_AGENT_SHIP_MARITIME_V1` is enforced in the system prompt and validated in `validator_fn`.
2. **XML Isolation Boundaries**: All external telemetry text from AIS and NOAA stations is wrapped in `<voyage_data>` tags and treated as strictly untrusted inputs.
3. **Dual Cryptographic Digest**: The contract calculates `SHA-256(combined_telemetry)` and requires that leader and validator consensus match the exact snapshot digest.
4. **Milestone v3 Fast-Track Engine**: Grantees and carriers with Gold ($\ge 50$ pts) or Platinum ($\ge 100$ pts) trust status automatically unlock a 12-block dispute window.
