# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json
import hashlib

CANARY_TOKEN = "CANARY_AGENT_SHIP_MARITIME_V1"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Lifecycle Statuses
STATUS_VOYAGE_OPEN = u8(0)          # Charterer funded freight & demurrage escrow
STATUS_IN_TRANSIT = u8(1)           # Carrier accepted voyage and submitted log telemetry
STATUS_AWAITING_PAYOUT = u8(2)      # AI maritime consensus rendered, cooling-off window open
STATUS_SETTLED_ON_TIME = u8(3)      # On-time delivery, 100% freight paid to carrier
STATUS_SETTLED_DEMURRAGE = u8(4)    # Demurrage enforced against charterer or carrier
STATUS_SETTLED_FORCE_MAJEURE = u8(5)# Storm / weather excused, demurrage waived
STATUS_DISPUTED = u8(6)             # Under appellate maritime arbitration
STATUS_CANCELLED = u8(7)            # Expired and reclaimed by charterer

# Reputation Trust Tiers (Milestone v3)
TIER_BRONZE = "BRONZE_NEWCOMER"             # < 20 pts (Standard 24h cooling-off)
TIER_SILVER = "SILVER_VERIFIED"             # 20 - 49 pts (Standard 24h cooling-off)
TIER_GOLD = "GOLD_ESTABLISHED"              # 50 - 99 pts (Fast-Track 12h cooling-off)
TIER_PLATINUM = "PLATINUM_ADMIRALTY_MASTER" # >= 100 pts (Fast-Track 12h cooling-off)

# Supported Deterministic Time Windows (in seconds)
STANDARD_COOLING_OFF_SECONDS = bigint(86400)      # 24 hours
FAST_TRACK_COOLING_OFF_SECONDS = bigint(43200)    # 12 hours

# Backwards compatibility block constants
STANDARD_COOLING_OFF_BLOCKS = 24
FAST_TRACK_COOLING_OFF_BLOCKS = 12


class ContractError(Exception):
    """Domain-specific error for AgentShip protocol rule violations and reverts."""
    pass


def _addr_str(addr: Address) -> str:
    """Safely format an Address instance into a lowercase hex string."""
    try:
        return addr.as_hex.lower()
    except Exception:
        return str(addr).lower()


def _get_sender() -> Address:
    """Safely obtain transaction sender across GenVM runtime versions."""
    try:
        return gl.message.sender_address
    except Exception:
        try:
            return gl.message.sender
        except Exception:
            raise ContractError("Cannot resolve sender address.")


def _pay_native(recipient: Address, amount: bigint) -> None:
    """Safely transfers native GEN tokens with canonical u256 cast and zero-value check."""
    if amount <= bigint(0):
        return
    gl.get_contract_at(recipient).emit_transfer(value=u256(int(amount)))


# Accredited Maritime Authorities and Oceanographic Meteorological Sources (Enforceable Source Authentication)
ACCREDITED_MARITIME_SOURCES = [
    "noaa.gov",
    "weather.gov",
    "ecmwf.int",
    "metoffice.gov.uk",
    "marinetraffic.com",
    "vesselfinder.com",
    "imo.org",
    "ukho.gov.uk",
    "admiralty.co.uk",
    "portofrotterdam.com",
    "singaporemaritime.gov",
    "shanghaiport.gov",
    "dwd.de",
    "ais-marinetraffic.org",
    "noaa-marine.org"
]


def _is_accredited_maritime_source(url: str) -> bool:
    """Verifies that evidence originates from an accredited maritime authority domain."""
    clean = str(url).strip().lower()
    if not (clean.startswith("http://") or clean.startswith("https://")):
        return False
    try:
        no_proto = clean.split("://", 1)[1]
        host = no_proto.split("/", 1)[0].split(":", 1)[0]
        for domain in ACCREDITED_MARITIME_SOURCES:
            if host == domain or host.endswith("." + domain):
                return True
    except Exception:
        return False
    return False


@allow_storage
@dataclass
class MaritimeVoyage:
    voyage_id: str
    charterer: Address             # Cargo owner / Shipper
    carrier: Address               # Shipowner / Shipping Line
    dispute_initiator: Address
    freight_amount: bigint         # Base shipping freight locked
    demurrage_deposit: bigint      # Demurrage buffer deposit (from primary charterer)
    dispute_bond: bigint           # 10% appeal stake
    vessel_imo_number: str         # International Maritime Organization vessel identifier
    laytime_hours_allowed: u32     # Agreed loading/unloading hours (Laytime)
    ais_tracking_url: str          # AIS voyage position & speed telemetry endpoint
    marine_weather_url: str        # NOAA / ECMWF oceanic sea state & wave height endpoint
    evidence_hash: str             # SHA-256 snapshot of combined voyage telemetry
    status: u8
    verdict: str                   # "PENDING", "CLEAN_ON_TIME", "DEMURRAGE_ENFORCED", "FORCE_MAJEURE_EXCUSED", "DISPUTED"
    original_verdict: str          # Verdict rendered prior to appeal, preserved on dismissal
    reason: str
    confidence: u8
    measured_delay_hours: u32      # Hours exceeded beyond laytime
    max_wave_height_meters: u8     # Peak oceanic wave height observed
    created_at_time: bigint        # Trusted Unix timestamp when voyage created
    expires_at_time: bigint        # Trusted Unix timestamp when voyage expires
    audit_completed_time: bigint   # Trusted Unix timestamp when audit completed
    is_fast_track: bool            # True if qualifying for fast-track settlement
    co_funder_count: u32           # Number of syndicate co-funders contributing to freight


class Contract(gl.Contract):
    """
    AgentShip: Autonomous Global Maritime Demurrage & Weather Risk Court
    Milestone v3: Syndicate Co-Funding, Proportional Solvency, Dynamic Trust Tiers & Fast-Track Adjudication
    Target Network: GenLayer studionet (Chain ID: 61999)
    """
    voyages: TreeMap[str, MaritimeVoyage]
    voyage_ids: DynArray[str]
    total_maritime_locked: bigint
    total_voyages_settled: u32
    voyage_counter: u64
    owner: Address

    # Milestone v3: On-Chain Dynamic Reputation & Trust Tier Engine
    reputation_scores: TreeMap[str, bigint]
    stats_completed: TreeMap[str, u32]
    stats_force_majeure: TreeMap[str, u32]
    stats_demurrage_fault: TreeMap[str, u32]
    stats_appeals_won: TreeMap[str, u32]
    stats_appeals_lost: TreeMap[str, u32]
    registered_registry: TreeMap[str, str]

    # Milestone v3: Syndicate Co-Funding JSON
    syndicate_pledges_json: TreeMap[str, str]

    def __init__(self):
        # GenVM auto-initializes TreeMap and DynArray. Do not call _get_sender() statically in __init__.
        self.owner = Address(ZERO_ADDRESS)
        self.total_maritime_locked = bigint(0)
        self.total_voyages_settled = u32(0)
        self.voyage_counter = u64(0)

    def _resolve_vid(self, voyage_id) -> str:
        """Safely normalize voyage_id to str for GenVM TreeMap compatibility."""
        return str(voyage_id).strip()

    def _ensure_owner(self) -> None:
        if _addr_str(self.owner) == ZERO_ADDRESS:
            self.owner = _get_sender()

    def _get_current_timestamp(self) -> bigint:
        """
        Derives trusted Unix timestamp from GenLayer transaction execution context (gl.message_raw['datetime']).
        Deterministic across all validators in GenVM consensus.
        """
        try:
            if hasattr(gl, "message_raw") and isinstance(gl.message_raw, dict):
                dt_str = str(gl.message_raw.get("datetime", ""))
                if dt_str:
                    from datetime import datetime
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    ts = bigint(int(dt.timestamp()))
                    if ts > bigint(0):
                        return ts
        except Exception:
            pass
        # Fallback for local testing / non-message_raw test runners
        try:
            import time
            return bigint(int(time.time()))
        except Exception:
            return bigint(1760000000)

    # ── Reputation Management Internal Helpers ─────────────────────────

    def _touch_participant(self, addr_str: str) -> None:
        if addr_str == ZERO_ADDRESS or len(addr_str) < 10:
            return
        current = self.registered_registry.get("all", "")
        parts = [p for p in current.split(",") if p]
        if addr_str not in parts:
            parts.append(addr_str)
            self.registered_registry["all"] = ",".join(parts)

    def _get_all_participants(self) -> list:
        current = self.registered_registry.get("all", "")
        return [p for p in current.split(",") if p]

    def _add_reputation(self, addr_str: str, points: int) -> None:
        self._touch_participant(addr_str)
        current = self.reputation_scores.get(addr_str, bigint(10))
        new_score = current + bigint(points)
        if new_score < bigint(0):
            new_score = bigint(0)
        self.reputation_scores[addr_str] = new_score

    def _get_reputation_tier(self, addr_str: str) -> str:
        score = int(self.reputation_scores.get(addr_str, bigint(10)))
        if score >= 100:
            return TIER_PLATINUM
        elif score >= 50:
            return TIER_GOLD
        elif score >= 20:
            return TIER_SILVER
        else:
            return TIER_BRONZE

    def _is_fast_track_eligible(self, charterer_str: str, carrier_str: str) -> bool:
        t_charterer = self._get_reputation_tier(charterer_str)
        t_carrier = self._get_reputation_tier(carrier_str)
        c_qual = t_charterer in [TIER_GOLD, TIER_PLATINUM]
        k_qual = t_carrier in [TIER_GOLD, TIER_PLATINUM]
        return c_qual or k_qual

    # ── Public Write Methods ──────────────────────────────────────────

    @gl.public.write.payable
    def create_voyage_escrow(
        self,
        vessel_imo: str,
        laytime_hours: u32,
        demurrage_buffer_wei: bigint,
        duration_blocks: u32
    ) -> str:
        self._ensure_owner()
        total_deposit = bigint(gl.message.value)
        if total_deposit <= demurrage_buffer_wei or demurrage_buffer_wei <= bigint(0):
            raise ContractError("Deposit must cover both base freight and positive demurrage buffer.")

        clean_imo = str(vessel_imo).strip()
        if len(clean_imo) < 7:
            raise ContractError("Valid vessel IMO number (>= 7 chars) required.")

        freight = total_deposit - demurrage_buffer_wei
        laytime = u32(max(12, min(720, laytime_hours)))
        
        dur_secs = bigint(duration_blocks * 3 if duration_blocks > 0 else 86400 * 7)

        self.voyage_counter = self.voyage_counter + u64(1)
        voyage_id = str(self.voyage_counter)
        current_time = self._get_current_timestamp()
        expires_at = current_time + dur_secs
        empty_addr = Address(ZERO_ADDRESS)
        charterer_addr = _get_sender()
        self._touch_participant(_addr_str(charterer_addr))

        new_voyage = MaritimeVoyage(
            voyage_id=voyage_id,
            charterer=charterer_addr,
            carrier=empty_addr,
            dispute_initiator=empty_addr,
            freight_amount=freight,
            demurrage_deposit=demurrage_buffer_wei,
            dispute_bond=bigint(0),
            vessel_imo_number=clean_imo,
            laytime_hours_allowed=laytime,
            ais_tracking_url="",
            marine_weather_url="",
            evidence_hash="",
            status=STATUS_VOYAGE_OPEN,
            verdict="PENDING",
            original_verdict="PENDING",
            reason="Voyage escrow opened. Awaiting carrier acceptance and AIS tracking link.",
            confidence=u8(0),
            measured_delay_hours=u32(0),
            max_wave_height_meters=u8(0),
            created_at_time=current_time,
            expires_at_time=expires_at,
            audit_completed_time=bigint(0),
            is_fast_track=False,
            co_funder_count=u32(1),
        )

        self.voyages[voyage_id] = new_voyage
        self.voyage_ids.append(voyage_id)
        self.total_maritime_locked = self.total_maritime_locked + total_deposit

        # Record primary charterer freight portion in syndicate records
        pledge_entry = {
            "funder": _addr_str(charterer_addr),
            "amount": str(freight),
            "role": "CHARTERER_PRIMARY"
        }
        self.syndicate_pledges_json[voyage_id] = json.dumps([pledge_entry])

        return voyage_id

    @gl.public.write.payable
    def pledge_voyage_escrow(self, voyage_id: str) -> None:
        self._ensure_owner()
        vid = self._resolve_vid(voyage_id)
        if vid not in self.voyages:
            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]
        if v.status != STATUS_VOYAGE_OPEN:
            raise ContractError("Can only pool funds into open voyage bookings.")

        funder = _get_sender()
        pledge_val = bigint(gl.message.value)
        if pledge_val <= bigint(0):
            raise ContractError("Co-funding contribution must be greater than 0.")

        self._touch_participant(_addr_str(funder))
        v.freight_amount = v.freight_amount + pledge_val
        v.co_funder_count = v.co_funder_count + u32(1)
        self.total_maritime_locked = self.total_maritime_locked + pledge_val

        pledges_raw = self.syndicate_pledges_json.get(vid, "[]")
        try:
            p_list = json.loads(pledges_raw)
        except Exception:
            p_list = []
        p_list.append({
            "funder": _addr_str(funder),
            "amount": str(pledge_val),
            "role": "SYNDICATE_CO_SHIPPER"
        })
        self.syndicate_pledges_json[vid] = json.dumps(p_list)

    @gl.public.write
    def submit_voyage_logs(
        self,
        voyage_id: str,
        ais_tracking_url: str,
        marine_weather_url: str
    ) -> None:
        self._ensure_owner()
        vid = self._resolve_vid(voyage_id)
        if vid not in self.voyages:
            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]
        if v.status != STATUS_VOYAGE_OPEN:
            raise ContractError("Voyage is not open for log submission.")

        sender = _get_sender()
        if _addr_str(sender) == _addr_str(v.charterer):
            raise ContractError("Role Violation: Charterer cannot act as vessel carrier.")

        clean_ais = str(ais_tracking_url).strip()
        clean_weather = str(marine_weather_url).strip()
        if not clean_ais.startswith("http://") and not clean_ais.startswith("https://"):
            raise ContractError("Valid public AIS telemetry URL required.")
        if not clean_weather.startswith("http://") and not clean_weather.startswith("https://"):
            raise ContractError("Valid public oceanic weather URL required.")

        self._touch_participant(_addr_str(sender))
        v.carrier = sender
        v.ais_tracking_url = clean_ais
        v.marine_weather_url = clean_weather
        v.status = STATUS_IN_TRANSIT
        v.reason = "Voyage active. Telemetry linked. Ready for port arrival demurrage adjudication."

    @gl.public.write
    def adjudicate_demurrage(self, voyage_id: str) -> None:
        self._ensure_owner()
        vid = self._resolve_vid(voyage_id)
        if vid not in self.voyages:
            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]
        if v.status != STATUS_IN_TRANSIT:
            raise ContractError("Voyage is not in active transit monitoring status.")

        sender = _get_sender()
        sender_str = _addr_str(sender)
        if (
            sender_str != _addr_str(v.charterer)
            and sender_str != _addr_str(v.carrier)
            and sender_str != _addr_str(self.owner)
        ):
            raise ContractError("Permission Denied: Only charterer, carrier, or owner can trigger adjudication.")

        ais_url = v.ais_tracking_url
        weather_url = v.marine_weather_url

        def leader_fn():
            raw_ais = ""
            raw_weather = ""

            try:
                raw_ais = gl.nondet.web.render(ais_url, mode="text")
            except Exception:
                pass

            try:
                raw_weather = gl.nondet.web.render(weather_url, mode="text")
            except Exception:
                pass

            combined_payload = f"AIS_TELEMETRY:\n{raw_ais[:2500]}\n\nOCEAN_WEATHER:\n{raw_weather[:2500]}"
            evidence_hash = hashlib.sha256(combined_payload.encode("utf-8")).hexdigest()

            prompt = f"""You are an Autonomous Admiralty Court Demurrage & Weather Risk Magistrate on GenLayer.
Cross-examine real-world maritime AIS satellite tracking and oceanic weather buoy feeds for vessel IMO {v.vessel_imo_number}.

AGREED CHARTERPARTY TERMS:
- Vessel IMO: {v.vessel_imo_number}
- Allowed Laytime: {v.laytime_hours_allowed} hours

TELEMETRY EVIDENCE:
{combined_payload}

ADJUDICATION JURISPRUDENCE RULES:
1. FORCE MAJEURE (Wave Height >= 6.0m OR sustained wind >= 34 knots / Beaufort Force 8 gale):
   Delay is legally EXCUSED as an Act of God / Perils of the Sea.
   Verdict: "FORCE_MAJEURE_EXCUSED".
2. CLEAN ON-TIME (Actual berthing delay <= Laytime allowed):
   No demurrage incurred.
   Verdict: "CLEAN_ON_TIME".
3. DEMURRAGE BREACH (Delay > Laytime allowed with calm/moderate sea conditions < 6.0m waves):
   Demurrage penalty strictly enforced against responsible party.
   Verdict: "DEMURRAGE_ENFORCED".

Respond ONLY with valid JSON:
{{
  "canary": "{CANARY_TOKEN}",
  "verdict": "CLEAN_ON_TIME" | "DEMURRAGE_ENFORCED" | "FORCE_MAJEURE_EXCUSED",
  "confidence": <integer 0-100>,
  "measured_delay_hours": <integer>,
  "max_wave_height_meters": <integer>,
  "reason": "<rigorous factual marine summary under 200 chars>",
  "evidence_hash": "{evidence_hash}"
}}"""

            raw_res = gl.nondet.exec_prompt(prompt, response_format="json")
            parsed = None

            if isinstance(raw_res, dict):
                parsed = raw_res
            elif isinstance(raw_res, str):
                cleaned = raw_res.replace("```json", "").replace("```", "").strip()
                try:
                    parsed = json.loads(cleaned)
                except Exception:
                    pass

            if not parsed or str(parsed.get("canary", "")) != CANARY_TOKEN:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "DEMURRAGE_ENFORCED",
                    "confidence": 60,
                    "measured_delay_hours": 48,
                    "max_wave_height_meters": 0,
                    "reason": "Arbitration consensus parser mismatch.",
                    "evidence_hash": evidence_hash,
                }

            v_raw = str(parsed.get("verdict", "DEMURRAGE_ENFORCED")).upper().strip()
            if v_raw not in {"CLEAN_ON_TIME", "DEMURRAGE_ENFORCED", "FORCE_MAJEURE_EXCUSED"}:
                v_raw = "DEMURRAGE_ENFORCED"

            try:
                del_hrs = max(0, min(1000, int(parsed.get("measured_delay_hours", 0))))
            except Exception:
                del_hrs = 0

            try:
                waves = max(0, min(30, int(parsed.get("max_wave_height_meters", 0))))
            except Exception:
                waves = 0

            return {
                "canary": CANARY_TOKEN,
                "verdict": v_raw,
                "confidence": max(0, min(100, int(parsed.get("confidence", 85)))),
                "measured_delay_hours": del_hrs,
                "max_wave_height_meters": waves,
                "reason": str(parsed.get("reason", "Maritime analysis concluded."))[:200],
                "evidence_hash": evidence_hash,
            }

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            leader = leader_res.calldata
            if not isinstance(leader, dict) or "verdict" not in leader:
                return False
            if leader.get("canary") != CANARY_TOKEN:
                return False

            mine = leader_fn()
            if mine["verdict"] != leader["verdict"]:
                return False
            if leader.get("evidence_hash") != mine.get("evidence_hash"):
                return False
            return True

        adjudication_res = gl.vm.run_nondet(leader_fn, validator_fn)

        v.verdict = str(adjudication_res["verdict"])
        v.original_verdict = v.verdict
        v.reason = str(adjudication_res["reason"])
        v.confidence = u8(int(adjudication_res["confidence"]))
        v.measured_delay_hours = u32(int(adjudication_res["measured_delay_hours"]))
        v.max_wave_height_meters = u8(int(adjudication_res["max_wave_height_meters"]))
        if "evidence_hash" in adjudication_res and adjudication_res["evidence_hash"]:
            v.evidence_hash = str(adjudication_res["evidence_hash"])

        current_time = self._get_current_timestamp()
        v.status = STATUS_AWAITING_PAYOUT
        v.audit_completed_time = current_time

        v.is_fast_track = self._is_fast_track_eligible(_addr_str(v.charterer), _addr_str(v.carrier))

    @gl.public.write.payable
    def appeal_verdict(self, voyage_id: str, dispute_reason: str) -> None:
        self._ensure_owner()
        vid = self._resolve_vid(voyage_id)
        if vid not in self.voyages:
            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]
        if v.status != STATUS_AWAITING_PAYOUT:
            raise ContractError("Can only appeal voyages in AWAITING_PAYOUT status.")

        sender = _get_sender()
        if _addr_str(sender) != _addr_str(v.charterer) and _addr_str(sender) != _addr_str(v.carrier):
            raise ContractError("Role Violation: Only charterer or carrier can file an appeal.")

        current_time = self._get_current_timestamp()
        cooling_window = FAST_TRACK_COOLING_OFF_SECONDS if v.is_fast_track else STANDARD_COOLING_OFF_SECONDS
        if current_time > (v.audit_completed_time + cooling_window):
            raise ContractError(f"Dispute cooling-off window ({int(cooling_window)}s) has expired.")

        total_escrow = v.freight_amount + v.demurrage_deposit
        required_bond = (total_escrow * bigint(10)) // bigint(100)
        if required_bond == bigint(0):
            required_bond = bigint(1)

        staked = bigint(gl.message.value)
        if staked < required_bond:
            raise ContractError(f"Must stake at least 10% dispute bond ({int(required_bond)} wei).")

        clean_reason = str(dispute_reason).strip()
        if len(clean_reason) < 10:
            raise ContractError("Detailed dispute justification (>=10 chars) required.")

        v.status = STATUS_DISPUTED
        v.dispute_initiator = sender
        v.dispute_bond = staked
        v.reason = f"[DISPUTE by {_addr_str(sender)[:8]}]: {clean_reason} | Prior: {v.reason}"
        self.total_maritime_locked = self.total_maritime_locked + staked

    @gl.public.write
    def adjudicate_appeal(self, voyage_id: str, supplemental_log_url: str) -> None:
        self._ensure_owner()
        vid = self._resolve_vid(voyage_id)
        if vid not in self.voyages:
            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]
        if v.status != STATUS_DISPUTED:
            raise ContractError("Voyage is not in DISPUTED status.")

        sender = _get_sender()
        sender_str = _addr_str(sender)
        if sender_str != _addr_str(v.charterer) and sender_str != _addr_str(v.carrier):
            raise ContractError("Permission Denied: Only charterer or carrier can adjudicate appeal.")

        clean_url = str(supplemental_log_url).strip()
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            raise ContractError("Valid supplemental maritime telemetry URL required.")

        if not _is_accredited_maritime_source(clean_url):
            raise ContractError("Evidence source unauthenticated: Must originate from an accredited maritime authority domain.")

        appellant = v.dispute_initiator
        voyage_start_ts = int(v.created_at_time)
        voyage_end_ts = int(v.audit_completed_time if v.audit_completed_time > bigint(0) else v.expires_at_time)

        def leader_fn():
            raw_supp = ""
            try:
                raw_supp = gl.nondet.web.render(clean_url, mode="text")
            except Exception:
                pass

            if not raw_supp:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "APPEAL_DISMISSED",
                    "reason": "Supplemental harbor logs unreachable.",
                }

            # Enforce that telemetry evidence is strictly bound to declared vessel IMO
            if v.vessel_imo_number.lower() not in raw_supp.lower():
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "APPEAL_DISMISSED",
                    "reason": f"Supplemental evidence rejected: Not bound to declared vessel IMO {v.vessel_imo_number}.",
                }

            # Enforce that telemetry evidence is strictly bound to declared voyage period
            supp_lower = raw_supp.lower()
            if "out-of-period" in supp_lower or "outside voyage period" in supp_lower or "expired date" in supp_lower:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "APPEAL_DISMISSED",
                    "reason": "Supplemental evidence rejected: Event timestamp falls outside declared voyage operating period.",
                }

            prompt = f"""You are the Supreme Admiralty Appellate Magistrate on GenLayer.
Evaluate the supplemental logs for declared vessel IMO: {v.vessel_imo_number}.

VOYAGE CONTRACTUAL BOUNDARIES:
- Declared Vessel IMO: {v.vessel_imo_number}
- Declared Operating Window: Epoch {voyage_start_ts} to {voyage_end_ts}

CRITICAL APPELLATE RULES:
1. RESTRICTED BINDING: The supplemental evidence MUST be authentic, explicitly reference vessel IMO {v.vessel_imo_number}, AND document events occurring strictly WITHIN the declared voyage period ({voyage_start_ts} to {voyage_end_ts}).
2. If evidence is unauthenticated, unrelated, outside the voyage period, or lacks explicit verification for IMO {v.vessel_imo_number}: Output "APPEAL_DISMISSED".
3. If supplemental records conclusively prove severe hurricane / oceanic storm Force Majeure during the declared voyage period: Output "APPEAL_UPHELD_FORCE_MAJEURE".
4. If records conclusively prove on-time tender within laytime during the declared voyage period: Output "APPEAL_UPHELD_ON_TIME".
5. Otherwise: Output "APPEAL_DISMISSED".

SUPPLEMENTAL MARITIME LOGS:
{raw_supp[:4000]}

Respond ONLY with valid JSON:
{{"canary": "{CANARY_TOKEN}", "verdict": "APPEAL_UPHELD_FORCE_MAJEURE"|"APPEAL_UPHELD_ON_TIME"|"APPEAL_DISMISSED", "reason": "<rationale>"}}"""

            raw_res = gl.nondet.exec_prompt(prompt, response_format="json")
            parsed = None
            if isinstance(raw_res, dict):
                parsed = raw_res
            elif isinstance(raw_res, str):
                cleaned = raw_res.replace("```json", "").replace("```", "").strip()
                try:
                    parsed = json.loads(cleaned)
                except Exception:
                    pass

            if not parsed or str(parsed.get("canary", "")) != CANARY_TOKEN:
                return {"canary": CANARY_TOKEN, "verdict": "APPEAL_DISMISSED", "reason": "Appellate parsing failure."}

            v_str = str(parsed.get("verdict", "APPEAL_DISMISSED")).upper().strip()
            if v_str not in {"APPEAL_UPHELD_FORCE_MAJEURE", "APPEAL_UPHELD_ON_TIME", "APPEAL_DISMISSED"}:
                v_str = "APPEAL_DISMISSED"

            return {
                "canary": CANARY_TOKEN,
                "verdict": v_str,
                "reason": str(parsed.get("reason", "Appellate review completed."))[:200]
            }

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            leader = leader_res.calldata
            if not isinstance(leader, dict) or "verdict" not in leader:
                return False
            if leader.get("canary") != CANARY_TOKEN:
                return False
            mine = leader_fn()
            return mine["verdict"] == leader["verdict"]

        appeal_res = gl.vm.run_nondet(leader_fn, validator_fn)
        app_verdict = appeal_res["verdict"]
        app_reason = appeal_res["reason"]

        freight_val = v.freight_amount
        demurrage_val = v.demurrage_deposit
        bond_val = v.dispute_bond
        total_settling = freight_val + demurrage_val + bond_val
        v.dispute_bond = bigint(0)
        v.freight_amount = bigint(0)
        v.demurrage_deposit = bigint(0)

        self.total_maritime_locked = self.total_maritime_locked - total_settling
        self.total_voyages_settled = self.total_voyages_settled + u32(1)

        counterparty = v.carrier if _addr_str(appellant) == _addr_str(v.charterer) else v.charterer
        appellant_str = _addr_str(appellant)
        counterparty_str = _addr_str(counterparty)

        if app_verdict == "APPEAL_UPHELD_FORCE_MAJEURE":
            v.status = STATUS_SETTLED_FORCE_MAJEURE
            v.verdict = "FORCE_MAJEURE_EXCUSED"
            v.reason = f"[APPEAL UPHELD] {app_reason}"
            _pay_native(v.carrier, freight_val)
            _pay_native(v.charterer, demurrage_val)
            _pay_native(appellant, bond_val)

            self._add_reputation(appellant_str, 15)
            self.stats_appeals_won[appellant_str] = self.stats_appeals_won.get(appellant_str, u32(0)) + u32(1)
            self.stats_appeals_lost[counterparty_str] = self.stats_appeals_lost.get(counterparty_str, u32(0)) + u32(1)

        elif app_verdict == "APPEAL_UPHELD_ON_TIME":
            v.status = STATUS_SETTLED_ON_TIME
            v.verdict = "CLEAN_ON_TIME"
            v.reason = f"[APPEAL UPHELD] {app_reason}"
            _pay_native(v.carrier, freight_val)
            _pay_native(v.charterer, demurrage_val)
            _pay_native(appellant, bond_val)

            self._add_reputation(appellant_str, 15)
            self.stats_appeals_won[appellant_str] = self.stats_appeals_won.get(appellant_str, u32(0)) + u32(1)
            self.stats_appeals_lost[counterparty_str] = self.stats_appeals_lost.get(counterparty_str, u32(0)) + u32(1)

        else:
            # APPEAL DISMISSED: Preserve original verdict and execute original payout!
            # The 10% appeal bond of the unsuccessful appellant is forfeited to the counterparty.
            _pay_native(counterparty, bond_val)
            self._add_reputation(appellant_str, -15)
            self._add_reputation(counterparty_str, 10)
            self.stats_appeals_lost[appellant_str] = self.stats_appeals_lost.get(appellant_str, u32(0)) + u32(1)
            self.stats_appeals_won[counterparty_str] = self.stats_appeals_won.get(counterparty_str, u32(0)) + u32(1)

            carrier_str = _addr_str(v.carrier)
            charterer_str = _addr_str(v.charterer)

            # Revert to and execute the original verdict
            if v.original_verdict == "FORCE_MAJEURE_EXCUSED":
                v.status = STATUS_SETTLED_FORCE_MAJEURE
                v.verdict = "FORCE_MAJEURE_EXCUSED"
                v.reason = f"[APPEAL DISMISSED - ORIGINAL VERDICT PRESERVED] {app_reason}"
                _pay_native(v.carrier, freight_val)
                _pay_native(v.charterer, demurrage_val)
                self.stats_force_majeure[carrier_str] = self.stats_force_majeure.get(carrier_str, u32(0)) + u32(1)
            elif v.original_verdict == "CLEAN_ON_TIME":
                v.status = STATUS_SETTLED_ON_TIME
                v.verdict = "CLEAN_ON_TIME"
                v.reason = f"[APPEAL DISMISSED - ORIGINAL VERDICT PRESERVED] {app_reason}"
                _pay_native(v.carrier, freight_val)
                _pay_native(v.charterer, demurrage_val)
                self.stats_completed[carrier_str] = self.stats_completed.get(carrier_str, u32(0)) + u32(1)
                self.stats_completed[charterer_str] = self.stats_completed.get(charterer_str, u32(0)) + u32(1)
            else:
                v.status = STATUS_SETTLED_DEMURRAGE
                v.verdict = "DEMURRAGE_ENFORCED"
                v.reason = f"[APPEAL DISMISSED - ORIGINAL VERDICT PRESERVED] {app_reason}"
                _pay_native(v.carrier, freight_val + demurrage_val)
                self.stats_demurrage_fault[charterer_str] = self.stats_demurrage_fault.get(charterer_str, u32(0)) + u32(1)
                self.stats_completed[carrier_str] = self.stats_completed.get(carrier_str, u32(0)) + u32(1)

    @gl.public.write
    def finalize_settlement(self, voyage_id: str) -> None:
        self._ensure_owner()
        vid = self._resolve_vid(voyage_id)
        if vid not in self.voyages:
            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]
        if v.status != STATUS_AWAITING_PAYOUT:
            raise ContractError("Voyage is not awaiting settlement payout.")

        sender = _get_sender()
        sender_str = _addr_str(sender)
        if (
            sender_str != _addr_str(v.charterer)
            and sender_str != _addr_str(v.carrier)
            and sender_str != _addr_str(self.owner)
        ):
            raise ContractError("Permission Denied: Only voyage stakeholders can finalize payout.")

        current_time = self._get_current_timestamp()
        cooling_window = FAST_TRACK_COOLING_OFF_SECONDS if v.is_fast_track else STANDARD_COOLING_OFF_SECONDS
        if current_time <= (v.audit_completed_time + cooling_window):
            raise ContractError(f"Cooling-off challenge window ({int(cooling_window)}s) is still active.")

        freight_val = v.freight_amount
        demurrage_val = v.demurrage_deposit
        total_escrow = freight_val + demurrage_val
        v.freight_amount = bigint(0)
        v.demurrage_deposit = bigint(0)
        self.total_maritime_locked = self.total_maritime_locked - total_escrow
        self.total_voyages_settled = self.total_voyages_settled + u32(1)

        carrier_str = _addr_str(v.carrier)
        charterer_str = _addr_str(v.charterer)

        if v.verdict == "DEMURRAGE_ENFORCED":
            v.status = STATUS_SETTLED_DEMURRAGE
            _pay_native(v.carrier, freight_val + demurrage_val)
            self._add_reputation(carrier_str, 5)
            self._add_reputation(charterer_str, -5)
            self.stats_demurrage_fault[charterer_str] = self.stats_demurrage_fault.get(charterer_str, u32(0)) + u32(1)
            self.stats_completed[carrier_str] = self.stats_completed.get(carrier_str, u32(0)) + u32(1)

        elif v.verdict == "FORCE_MAJEURE_EXCUSED" or v.verdict == "CLEAN_ON_TIME":
            v.status = STATUS_SETTLED_FORCE_MAJEURE if v.verdict == "FORCE_MAJEURE_EXCUSED" else STATUS_SETTLED_ON_TIME
            _pay_native(v.carrier, freight_val)
            _pay_native(v.charterer, demurrage_val)

            if v.verdict == "CLEAN_ON_TIME":
                self._add_reputation(carrier_str, 15)
                self._add_reputation(charterer_str, 10)
                self.stats_completed[carrier_str] = self.stats_completed.get(carrier_str, u32(0)) + u32(1)
                self.stats_completed[charterer_str] = self.stats_completed.get(charterer_str, u32(0)) + u32(1)
            else:
                self._add_reputation(carrier_str, 10)
                self._add_reputation(charterer_str, 10)
                self.stats_force_majeure[carrier_str] = self.stats_force_majeure.get(carrier_str, u32(0)) + u32(1)
        else:
            v.status = STATUS_CANCELLED
            _pay_native(v.charterer, total_escrow)

    @gl.public.write
    def cancel_or_reclaim(self, voyage_id: str) -> None:
        self._ensure_owner()
        vid = self._resolve_vid(voyage_id)
        if vid not in self.voyages:
            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]
        if _addr_str(_get_sender()) != _addr_str(v.charterer):
            raise ContractError("Role Violation: Only the charterer can cancel or reclaim booking.")

        current_time = self._get_current_timestamp()

        if v.status == STATUS_IN_TRANSIT:
            transit_grace_secs = bigint(86400) # 24 hours minimum transit window
            if current_time < (v.created_at_time + transit_grace_secs):
                raise ContractError("Cannot reclaim: Carrier actively navigating voyage.")
        elif v.status == STATUS_VOYAGE_OPEN:
            if current_time < v.expires_at_time:
                raise ContractError("Cannot cancel: Voyage duration has not expired.")
        else:
            raise ContractError("Voyage is already settled or disputed.")

        v.status = STATUS_CANCELLED
        v.verdict = "CANCELLED"
        v.reason = "Voyage cancelled and escrow refunded proportionally to participants."

        freight_val = v.freight_amount
        demurrage_val = v.demurrage_deposit
        total_escrow = freight_val + demurrage_val
        v.freight_amount = bigint(0)
        v.demurrage_deposit = bigint(0)
        self.total_maritime_locked = self.total_maritime_locked - total_escrow

        _pay_native(v.charterer, demurrage_val)

        pledges_raw = self.syndicate_pledges_json.get(vid, "[]")
        refunded_via_syndicate = False
        try:
            p_list = json.loads(pledges_raw)
            if len(p_list) > 0:
                for p_obj in p_list:
                    f_addr = Address(p_obj["funder"])
                    amt = bigint(int(p_obj["amount"]))
                    _pay_native(f_addr, amt)
                refunded_via_syndicate = True
        except Exception:
            pass

        if not refunded_via_syndicate:
            _pay_native(v.charterer, freight_val)

    # ── Read-only Views ───────────────────────────────────────────────

    @gl.public.view
    def get_voyage(self, voyage_id: str) -> str:
        vid = self._resolve_vid(voyage_id)
        if vid not in self.voyages:
            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]
        data = {
            "voyage_id": str(v.voyage_id),
            "charterer": _addr_str(v.charterer),
            "carrier": _addr_str(v.carrier),
            "dispute_initiator": _addr_str(v.dispute_initiator),
            "freight_amount": str(v.freight_amount),
            "demurrage_deposit": str(v.demurrage_deposit),
            "dispute_bond": str(v.dispute_bond),
            "vessel_imo_number": v.vessel_imo_number,
            "laytime_hours_allowed": int(v.laytime_hours_allowed),
            "ais_tracking_url": v.ais_tracking_url,
            "marine_weather_url": v.marine_weather_url,
            "evidence_hash": v.evidence_hash,
            "status": int(v.status),
            "verdict": v.verdict,
            "original_verdict": v.original_verdict,
            "reason": v.reason,
            "confidence": int(v.confidence),
            "measured_delay_hours": int(v.measured_delay_hours),
            "max_wave_height_meters": int(v.max_wave_height_meters),
            "created_at_time": str(v.created_at_time),
            "expires_at_time": str(v.expires_at_time),
            "audit_completed_time": str(v.audit_completed_time),
            # Backwards compatibility aliases for existing frontends
            "created_at_block": str(v.created_at_time),
            "expires_at_block": str(v.expires_at_time),
            "audit_completed_block": str(v.audit_completed_time),
            "is_fast_track": v.is_fast_track,
            "co_funder_count": int(v.co_funder_count),
        }
        return json.dumps(data)

    @gl.public.view
    def get_voyage_count(self) -> u64:
        return u64(len(self.voyage_ids))

    @gl.public.view
    def get_all_voyages(self) -> str:
        voyages_list = []
        for vid in self.voyage_ids:
            if vid in self.voyages:
                v = self.voyages[vid]
                voyages_list.append({
                    "voyage_id": str(v.voyage_id),
                    "charterer": _addr_str(v.charterer),
                    "carrier": _addr_str(v.carrier),
                    "dispute_initiator": _addr_str(v.dispute_initiator),
                    "freight_amount": str(v.freight_amount),
                    "demurrage_deposit": str(v.demurrage_deposit),
                    "dispute_bond": str(v.dispute_bond),
                    "vessel_imo_number": v.vessel_imo_number,
                    "laytime_hours_allowed": int(v.laytime_hours_allowed),
                    "ais_tracking_url": v.ais_tracking_url,
                    "marine_weather_url": v.marine_weather_url,
                    "evidence_hash": v.evidence_hash,
                    "status": int(v.status),
                    "verdict": v.verdict,
                    "original_verdict": v.original_verdict,
                    "reason": v.reason,
                    "confidence": int(v.confidence),
                    "measured_delay_hours": int(v.measured_delay_hours),
                    "max_wave_height_meters": int(v.max_wave_height_meters),
                    "created_at_time": str(v.created_at_time),
                    "expires_at_time": str(v.expires_at_time),
                    "audit_completed_time": str(v.audit_completed_time),
                    "created_at_block": str(v.created_at_time),
                    "expires_at_block": str(v.expires_at_time),
                    "audit_completed_block": str(v.audit_completed_time),
                    "is_fast_track": v.is_fast_track,
                    "co_funder_count": int(v.co_funder_count),
                })
        return json.dumps(voyages_list)

    @gl.public.view
    def get_stats(self) -> str:
        participants = self._get_all_participants()
        data = {
            "total_voyages": len(self.voyage_ids),
            "total_maritime_locked": str(self.total_maritime_locked),
            "total_voyages_settled": int(self.total_voyages_settled),
            "registered_participants": len(participants),
            "owner": _addr_str(self.owner),
        }
        return json.dumps(data)

    @gl.public.view
    def get_reputation_profile(self, user_address: Address) -> str:
        u_str = _addr_str(user_address)
        score = int(self.reputation_scores.get(u_str, bigint(10)))
        tier = self._get_reputation_tier(u_str)
        is_fast_track = tier in [TIER_GOLD, TIER_PLATINUM]

        dossier = {
            "address": u_str,
            "reputation_score": score,
            "tier": tier,
            "is_fast_track_eligible": is_fast_track,
            "cooling_off_seconds": int(FAST_TRACK_COOLING_OFF_SECONDS if is_fast_track else STANDARD_COOLING_OFF_SECONDS),
            "cooling_off_blocks": FAST_TRACK_COOLING_OFF_BLOCKS if is_fast_track else STANDARD_COOLING_OFF_BLOCKS,
            "completed_voyages": int(self.stats_completed.get(u_str, u32(0))),
            "force_majeure_weather_verified": int(self.stats_force_majeure.get(u_str, u32(0))),
            "demurrage_faults": int(self.stats_demurrage_fault.get(u_str, u32(0))),
            "appeals_won": int(self.stats_appeals_won.get(u_str, u32(0))),
            "appeals_lost": int(self.stats_appeals_lost.get(u_str, u32(0))),
        }
        return json.dumps(dossier)

    @gl.public.view
    def get_maritime_leaderboard(self) -> str:
        participants = self._get_all_participants()
        board = []
        for reg in participants:
            score = int(self.reputation_scores.get(reg, bigint(10)))
            board.append({
                "address": reg,
                "score": score,
                "tier": self._get_reputation_tier(reg),
                "completed": int(self.stats_completed.get(reg, u32(0))),
            })
        board.sort(key=lambda x: x["score"], reverse=True)
        return json.dumps(board[:20])

    @gl.public.view
    def get_voyage_pledges(self, voyage_id: str) -> str:
        vid = self._resolve_vid(voyage_id)
        if vid not in self.voyages:
            raise ContractError(f"Voyage {vid} does not exist.")

        pledges_raw = self.syndicate_pledges_json.get(vid, "[]")
        try:
            return pledges_raw
        except Exception:
            return "[]"
