# Changelog

All notable changes to the AgentShip protocol will be documented in this file.

## [v3.0.0] - 2026-10-05
### Added
- **On-Chain Maritime Reputation & Trust Tier Engine (`contracts/contract.py`)**:
  - Implemented credit score accounting with granular operational metrics: `stats_completed`, `stats_force_majeure`, `stats_demurrage_fault`, `stats_appeals_won`, and `stats_appeals_lost`.
  - Defined 4 distinct Trust Tiers: `BRONZE_NEWCOMER` (<20 pts), `SILVER_VERIFIED` (20-49 pts), `GOLD_ESTABLISHED` (50-99 pts), and `PLATINUM_ADMIRALTY_MASTER` ($\ge 100$ pts).
  - Implemented **Dynamic Fast-Track Adjudication**: Gold and Platinum operators automatically qualify for an expedited **12-block (43,200s equivalent) dispute cooling-off window**, while Bronze/Silver retain the standard 24 blocks.
  - Implemented `@gl.public.view def get_reputation_profile(user_address)` and `@gl.public.view def get_maritime_leaderboard()` returning top 20 ranked operators.
- **Cargo Syndicate Co-Funding Pool (`contracts/contract.py`)**:
  - Implemented `@gl.public.write.payable def pledge_voyage_escrow(voyage_id)` enabling co-shippers, consignees, and forwarders to pool native GEN into open voyage bookings.
  - Implemented proportional solvency clawback: in the event of voyage cancellation or demurrage buffer refunds, escrow shares are distributed proportionally to each contributor without precision loss.
  - Implemented `@gl.public.view def get_voyage_pledges(voyage_id)` inspecting active syndicate pledges.
- **Milestone v3 Verification Suite (`tests/test_agentship.py`)**:
  - Full suite expanded to 9/9 passing tests (100% pass rate).
- **Maritime Admiralty Radar Console Frontend (`frontend/`)**:
  - Added Syndicate Co-Funding Modal with tranche selection.
  - Added On-Chain Leaderboard & Trust Tier Drawer displaying ranks, scores, badges, and fast-track statuses.
  - Added dynamic `⚡ FAST-TRACK 12H` badges on qualifying voyages.

## [v2.0.0] - 2026-10-05
### Added
- **Stake-Based Judicial Appeal Protocol**:
  - Implemented `@gl.public.write.payable def appeal_verdict(voyage_id, dispute_reason)` with mandatory 10% staked bond.
  - Implemented Supreme Appellate Admiralty Court `@gl.public.write def adjudicate_appeal(...)` reviewing supplemental harbor master records.
  - Implemented bond return on appeal upheld and slashing to counterparty on appeal dismissal.
- **24-Block Cooling-off Challenge Window**:
  - Added `AWAITING_PAYOUT` state on initial consensus.
  - Payout can only be finalized via `finalize_settlement` after cooling-off window.

## [v1.0.0] - 2026-10-05
### Added
- **Core Maritime Escrow & AI Tribunal**:
  - Dual telemetry crawling: live AIS vessel coordinates and NOAA oceanic weather.
  - Canary Token Defense (`CANARY_AGENT_SHIP_MARITIME_V1`).
  - Force Majeure evaluation: severe waves ($\ge 6m$) waive demurrage.
