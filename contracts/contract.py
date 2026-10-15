# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

from dataclasses import dataclass

import json
import hashlib

CANARY_TOKEN = "CANARY_AGENT_SHIP_MARITIME_V1"

# Lifecycle Statuses

STATUS_VOYAGE_OPEN = u8(0)          # Charterer funded freight & demurrage escrow

STATUS_IN_TRANSIT = u8(1)           # Carrier accepted voyage and submitted log telemetry

STATUS_AWAITING_PAYOUT = u8(2)      # AI maritime consensus rendered, cooling-off window open

STATUS_SETTLED_ON_TIME = u8(3)      # On-time delivery, 100% freight paid to carrier

STATUS_SETTLED_DEMURRAGE = u8(4)    # Demurrage enforced against charterer or carrier

STATUS_SETTLED_FORCE_MAJEURE = u8(5)# Storm / weather excused, demurrage waived

STATUS_DISPUTED = u8(6)             # Under appellate maritime arbitration

STATUS_CANCELLED = u8(7)            # Expired and reclaimed by charterer

# Reputation Trust Tiers

TIER_BRONZE = "BRONZE_NEWCOMER"             # < 20 pts (Standard 24h cooling-off)

TIER_SILVER = "SILVER_VERIFIED"             # 20 - 49 pts (Standard 24h cooling-off)

TIER_GOLD = "GOLD_ESTABLISHED"              # 50 - 99 pts (Fast-Track 12h cooling-off)

TIER_PLATINUM = "PLATINUM_ADMIRALTY_MASTER" # >= 100 pts (Fast-Track 12h cooling-off)

# Supported Deterministic Time Windows (in seconds)

STANDARD_COOLING_OFF_SECONDS = bigint(86400)      # 24 hours

FAST_TRACK_COOLING_OFF_SECONDS = bigint(43200)    # 12 hours

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

        raise ContractError("Cannot resolve sender address.")

def _pay_native(recipient: Address, amount: bigint) -> None:

    """Safely transfers native GEN tokens with canonical u256 cast and zero-value check."""

    if amount <= bigint(0):

        return

    gl.get_contract_at(recipient).emit_transfer(value=u256(int(amount)))

# Accredited Maritime Authorities and Oceanographic Meteorological Sources

# Strictly excludes public code repositories (github.com / raw.githubusercontent.com)

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

    "noaa-marine.org",

]

def _is_accredited_maritime_source(url: str) -> bool:

    """Verifies that evidence originates strictly from an accredited maritime authority domain."""

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

class SyndicateFunder:
    funder: Address
    amount: bigint
    role: str

@allow_storage

@dataclass

class MaritimeVoyage:

    voyage_id: str

    charterer: Address             # Cargo owner / Shipper

    carrier: Address               # Shipowner / Shipping Line

    dispute_initiator: Address

    freight_amount: bigint         # Base shipping freight locked

    demurrage_deposit: bigint      # Demurrage buffer deposit

    dispute_bond: bigint           # 10% appeal stake

    vessel_imo_number: str         # International Maritime Organization vessel identifier

    laytime_hours_allowed: u32     # Agreed loading/unloading hours (Laytime)

    ais_tracking_url: str          # AIS voyage position & speed telemetry endpoint

    marine_weather_url: str        # NOAA / ECMWF oceanic sea state endpoint

    appeal_evidence_url: str       # Supplemental telemetry URL locked by bonded appellant

    dispute_reason: str            # Rebuttal argument locked by bonded appellant
    evidence_hash: str             # SHA-256 snapshot of combined voyage telemetry            # Rebuttal argument locked by bonded appellant

    status: u8

    verdict: str

    original_verdict: str          # Preserved pre-appeal verdict for consistent settlement on dismissal

    reason: str

    confidence: u8

    measured_delay_hours: u32

    max_wave_height_meters: u8

    created_at_time: bigint        # Trusted Unix timestamp when voyage was created

    expires_at_time: bigint        # Trusted Unix timestamp when voyage expires

    audit_completed_time: bigint   # Trusted Unix timestamp when initial audit completed

    is_fast_track: bool
    co_funder_count: u32           # Number of syndicate co-funders contributing to freight

class Contract(gl.Contract):

    """

    AgentShip: Autonomous Global Maritime Demurrage & Weather Risk Court

    Target Network: GenLayer studionet (Chain ID: 61999)

    """

    voyages: TreeMap[str, MaritimeVoyage]

    voyage_ids: DynArray[str]

    voyage_syndicates: TreeMap[str, DynArray[SyndicateFunder]]

    total_maritime_locked: bigint

    total_voyages_settled: u32

    voyage_counter: u64

    # On-Chain Dynamic Reputation Engine

    reputation_scores: TreeMap[str, bigint]

    stats_completed: TreeMap[str, u32]

    stats_force_majeure: TreeMap[str, u32]

    stats_demurrage_fault: TreeMap[str, u32]

    stats_appeals_won: TreeMap[str, u32]

    stats_appeals_lost: TreeMap[str, u32]

    registered_registry: TreeMap[str, str]

    def __init__(self):

        self.total_maritime_locked = bigint(0)

        self.total_voyages_settled = u32(0)

        self.voyage_counter = u64(0)

    def _resolve_vid(self, voyage_id) -> str:

        return str(voyage_id).strip()

    def _get_current_timestamp(self) -> bigint:

        """Derives trusted Unix timestamp from consensus context (gl.message_raw['datetime'])."""

        import calendar

        from datetime import datetime, timezone

        try:

            if hasattr(gl, "message_raw") and isinstance(gl.message_raw, dict):

                raw_val = gl.message_raw.get("datetime", "")

                if raw_val:

                    dt_str = str(raw_val).strip().replace("Z", "+00:00")

                    dt = datetime.fromisoformat(dt_str)

                    if dt.tzinfo is None:

                        dt = dt.replace(tzinfo=timezone.utc)

                    ts = calendar.timegm(dt.utctimetuple())

                    if ts > 0:

                        return bigint(ts)

        except Exception:

            pass

        return bigint(1760000000)

    # ── Reputation Management Helpers ─────────────────────────────────

    def _touch_participant(self, addr_str: str) -> None:

        if len(addr_str) < 10:

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

        return TIER_BRONZE

    def _is_fast_track_eligible(self, charterer_str: str, carrier_str: str) -> bool:

        t_charterer = self._get_reputation_tier(charterer_str)

        t_carrier = self._get_reputation_tier(carrier_str)

        return (t_charterer in [TIER_GOLD, TIER_PLATINUM]) or (t_carrier in [TIER_GOLD, TIER_PLATINUM])

    # ── Public Write Methods ──────────────────────────────────────────

    @gl.public.write.payable

    def create_voyage_escrow(

        self,

        vessel_imo: str,

        laytime_hours: u32,

        demurrage_buffer_wei: bigint,

        duration_blocks: u32

    ) -> str:

        total_deposit = bigint(gl.message.value)

        if total_deposit <= demurrage_buffer_wei or demurrage_buffer_wei <= bigint(0):

            raise ContractError("Deposit must cover both base freight and positive demurrage buffer.")

        clean_imo = str(vessel_imo).strip()

        if len(clean_imo) < 7:

            raise ContractError("Valid vessel IMO number (>= 7 chars) required.")

        freight = total_deposit - demurrage_buffer_wei

        laytime = u32(max(12, min(720, laytime_hours)))

        dur_secs = bigint(int(duration_blocks) * 3 if int(duration_blocks) > 0 else 86400 * 7)

        self.voyage_counter = self.voyage_counter + u64(1)

        voyage_id = str(self.voyage_counter)

        current_time = self._get_current_timestamp()

        expires_at = current_time + dur_secs

        charterer_addr = _get_sender()

        self._touch_participant(_addr_str(charterer_addr))

        new_voyage = MaritimeVoyage(

            voyage_id=voyage_id,

            charterer=charterer_addr,

            carrier=charterer_addr,  # Initialized safely; status 0 denotes unclaimed

            dispute_initiator=charterer_addr,

            freight_amount=freight,

            demurrage_deposit=demurrage_buffer_wei,

            dispute_bond=bigint(0),

            vessel_imo_number=clean_imo,

            laytime_hours_allowed=laytime,

            ais_tracking_url="",

            marine_weather_url="",

            appeal_evidence_url="",

            dispute_reason="",
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

        # GenVM Safe: Append directly without Python list assignment
        self.voyage_syndicates[voyage_id].append(SyndicateFunder(funder=charterer_addr, amount=freight, role="CHARTERER_PRIMARY"))

        self.total_maritime_locked = self.total_maritime_locked + total_deposit

        return voyage_id

    @gl.public.write.payable

    def pledge_voyage_escrow(self, voyage_id: str) -> None:

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
        # GenVM Safe: Append directly without Python list assignment
        self.voyage_syndicates[vid].append(SyndicateFunder(funder=funder, amount=pledge_val, role="SYNDICATE_CO_SHIPPER"))

        self.total_maritime_locked = self.total_maritime_locked + pledge_val

    @gl.public.write

    def submit_voyage_logs(

        self,

        voyage_id: str,

        ais_tracking_url: str,

        marine_weather_url: str

    ) -> None:

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

        if not (clean_ais.startswith("http://") or clean_ais.startswith("https://")):

            raise ContractError("Valid public AIS telemetry URL required.")

        if not (clean_weather.startswith("http://") or clean_weather.startswith("https://")):

            raise ContractError("Valid public oceanic weather URL required.")

        self._touch_participant(_addr_str(sender))

        v.carrier = sender

        v.ais_tracking_url = clean_ais

        v.marine_weather_url = clean_weather
        v.evidence_hash = hashlib.sha256(f"{vid}:{clean_ais}:{clean_weather}".encode("utf-8")).hexdigest()

        v.status = STATUS_IN_TRANSIT

        v.reason = "Voyage active. Telemetry linked. Ready for port arrival demurrage adjudication."

    @gl.public.write

    def adjudicate_demurrage(self, voyage_id: str) -> None:

        """Autonomous adjudication restricted strictly to voyage parties (Charterer or Carrier)."""

        vid = self._resolve_vid(voyage_id)

        if vid not in self.voyages:

            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]

        if v.status != STATUS_IN_TRANSIT:

            raise ContractError("Voyage is not in active transit monitoring status.")

        sender_str = _addr_str(_get_sender())

        # Strictly rejects global owner; only charterer or carrier can adjudicate

        if sender_str != _addr_str(v.charterer) and sender_str != _addr_str(v.carrier):

            raise ContractError("Permission Denied: Only charterer or carrier can trigger adjudication.")

        ais_url = v.ais_tracking_url

        weather_url = v.marine_weather_url

        imo = v.vessel_imo_number

        laytime = v.laytime_hours_allowed

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

            prompt = f"""You are an Autonomous Admiralty Court Demurrage Magistrate on GenLayer.

Evaluate AIS satellite tracking and oceanic weather data for vessel IMO: {imo}.

Allowed Laytime: {laytime} hours.

EVIDENCE:

{combined_payload}

RULES:

1. FORCE MAJEURE: If wave height >= 6.0m OR sustained wind >= 34 knots / gale force -> "FORCE_MAJEURE_EXCUSED".

2. CLEAN ON TIME: If actual berthing delay <= allowed laytime -> "CLEAN_ON_TIME".

3. DEMURRAGE BREACH: If delay > allowed laytime under calm sea (<6.0m waves) -> "DEMURRAGE_ENFORCED".

SECURITY CANARY: Echo "{CANARY_TOKEN}" in JSON.

Respond ONLY with valid JSON:

{{

  "canary": "{CANARY_TOKEN}",

  "verdict": "CLEAN_ON_TIME"|"DEMURRAGE_ENFORCED"|"FORCE_MAJEURE_EXCUSED",

  "confidence": <0-100>,

  "measured_delay_hours": <integer>,

  "max_wave_height_meters": <integer>,

  "reason": "<summary under 200 chars>"

}}"""

            raw_res = gl.nondet.exec_prompt(prompt, response_format="json")

            parsed = None

            if isinstance(raw_res, dict):

                parsed = raw_res

            elif isinstance(raw_res, str):

                try:

                    parsed = json.loads(raw_res.replace("```json", "").replace("```", "").strip())

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

                }

            v_raw = str(parsed.get("verdict", "DEMURRAGE_ENFORCED")).upper().strip()

            if v_raw not in {"CLEAN_ON_TIME", "DEMURRAGE_ENFORCED", "FORCE_MAJEURE_EXCUSED"}:

                v_raw = "DEMURRAGE_ENFORCED"

            return {

                "canary": CANARY_TOKEN,

                "verdict": v_raw,

                "confidence": max(0, min(100, int(parsed.get("confidence", 85)))),

                "measured_delay_hours": max(0, min(1000, int(parsed.get("measured_delay_hours", 0)))),

                "max_wave_height_meters": max(0, min(30, int(parsed.get("max_wave_height_meters", 0)))),

                "reason": str(parsed.get("reason", "Maritime analysis concluded."))[:200],

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

        adjudication_res = gl.vm.run_nondet(leader_fn, validator_fn)

        v.verdict = str(adjudication_res["verdict"])

        v.original_verdict = v.verdict

        v.reason = str(adjudication_res["reason"])

        v.confidence = u8(int(adjudication_res["confidence"]))

        v.measured_delay_hours = u32(int(adjudication_res["measured_delay_hours"]))

        v.max_wave_height_meters = u8(int(adjudication_res["max_wave_height_meters"]))

        current_time = self._get_current_timestamp()

        v.status = STATUS_AWAITING_PAYOUT

        v.audit_completed_time = current_time

        v.is_fast_track = self._is_fast_track_eligible(_addr_str(v.charterer), _addr_str(v.carrier))

    @gl.public.write.payable

    def appeal_verdict(

        self,

        voyage_id: str,

        dispute_reason: str,

        supplemental_log_url: str

    ) -> None:

        """

        Appellant locks dispute bond and registers authentic supplemental evidence URL.

        Enforces authenticated maritime source domain check at time of appeal.

        """

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

            raise ContractError("Detailed dispute justification (>= 10 chars) required.")

        clean_url = str(supplemental_log_url).strip()

        if not _is_accredited_maritime_source(clean_url):

            raise ContractError("Evidence unauthenticated: Must originate from an accredited maritime domain (NOAA, ECMWF, MarineTraffic, Port Authority).")

        v.status = STATUS_DISPUTED

        v.dispute_initiator = sender

        v.dispute_bond = staked

        v.appeal_evidence_url = clean_url

        v.dispute_reason = clean_reason

        v.reason = f"[DISPUTE by {_addr_str(sender)[:8]}]: {clean_reason} | Prior: {v.reason}"

        self.total_maritime_locked = self.total_maritime_locked + staked

    @gl.public.write

    def adjudicate_appeal(self, voyage_id: str) -> None:

        """

        Autonomous Appellate AI Court:

        1. Restricts caller strictly to charterer or carrier (no global owner allowed).

        2. Evaluates the supplemental evidence committed by the bonded appellant.

        3. Strictly verifies binding to declared vessel IMO and voyage time window.

        4. Preserves original verdict and settles original payouts when appeal is dismissed.

        """

        vid = self._resolve_vid(voyage_id)

        if vid not in self.voyages:

            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]

        if v.status != STATUS_DISPUTED:

            raise ContractError("Voyage is not in DISPUTED status.")

        sender_str = _addr_str(_get_sender())

        # Strictly enforces that only authorized voyage parties can trigger appellate adjudication

        if sender_str != _addr_str(v.charterer) and sender_str != _addr_str(v.carrier):

            raise ContractError("Permission Denied: Only charterer or carrier can adjudicate appeal.")

        evidence_url = v.appeal_evidence_url

        if not evidence_url or not _is_accredited_maritime_source(evidence_url):

            raise ContractError("Evidence source unauthenticated: Must originate from an accredited maritime domain (NOAA, ECMWF, MarineTraffic, Port Authority).")

        appellant = v.dispute_initiator

        imo = v.vessel_imo_number

        voyage_start_ts = int(v.created_at_time)

        voyage_end_ts = int(v.audit_completed_time if v.audit_completed_time > bigint(0) else v.expires_at_time)

        stored_dispute = v.dispute_reason

        orig_verdict = v.original_verdict

        def leader_fn():

            raw_supp = ""

            try:

                raw_supp = gl.nondet.web.render(evidence_url, mode="text")

            except Exception:

                pass

            if not raw_supp:

                return {

                    "canary": CANARY_TOKEN,

                    "verdict": "APPEAL_DISMISSED",

                    "reason": "Supplemental telemetry URL unreachable or 404.",

                }

            # Enforces that telemetry explicitly cites the declared vessel IMO

            if imo.lower() not in raw_supp.lower():

                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "APPEAL_DISMISSED",
                    "reason": f"Supplemental evidence rejected: Not bound to declared vessel IMO {imo}.",
                }

            raw_lower = raw_supp.lower()
            if "outside voyage period" in raw_lower or "out of period" in raw_lower or "out-of-period" in raw_lower:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "APPEAL_DISMISSED",
                    "reason": "Supplemental evidence rejected: Event falls outside declared voyage operating period.",
                }

            prompt = f"""You are the Supreme Admiralty Appellate Magistrate on GenLayer.

Evaluate appellate evidence for vessel IMO: {imo}.

VOYAGE BOUNDARIES:

- Declared Vessel IMO: {imo}

- Legitimate Operating Window: Epoch {voyage_start_ts} to {voyage_end_ts}

- Initial Pre-Appeal Verdict: {orig_verdict}

- Appellant Claim: {stored_dispute}

SUPPLEMENTAL MARITIME LOGS:

{raw_supp[:4000]}

APPELLATE EVALUATION RULES:

1. Verify that the telemetry events occurred strictly WITHIN the declared voyage window ({voyage_start_ts} to {voyage_end_ts}).

2. If evidence proves severe hurricane / Force Majeure storm within the voyage window -> "APPEAL_UPHELD_FORCE_MAJEURE".

3. If evidence proves vessel completed cargo operations on-time within laytime -> "APPEAL_UPHELD_ON_TIME".

4. If evidence is out-of-period, invalid, or fails to overcome the initial verdict -> "APPEAL_DISMISSED".

SECURITY CANARY: Echo "{CANARY_TOKEN}" in JSON.

Respond ONLY with valid JSON:

{{"canary": "{CANARY_TOKEN}", "verdict": "APPEAL_UPHELD_FORCE_MAJEURE"|"APPEAL_UPHELD_ON_TIME"|"APPEAL_DISMISSED", "reason": "<rationale under 200 chars>"}}"""

            raw_res = gl.nondet.exec_prompt(prompt, response_format="json")

            parsed = None

            if isinstance(raw_res, dict):

                parsed = raw_res

            elif isinstance(raw_res, str):

                try:

                    parsed = json.loads(raw_res.replace("```json", "").replace("```", "").strip())

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

        elif app_verdict == "APPEAL_UPHELD_ON_TIME":

            v.status = STATUS_SETTLED_ON_TIME

            v.verdict = "CLEAN_ON_TIME"

            v.reason = f"[APPEAL UPHELD] {app_reason}"

            _pay_native(v.carrier, freight_val)

            _pay_native(v.charterer, demurrage_val)

            _pay_native(appellant, bond_val)

            self._add_reputation(appellant_str, 15)

            self.stats_appeals_won[appellant_str] = self.stats_appeals_won.get(appellant_str, u32(0)) + u32(1)

        else:

            # APPEAL DISMISSED: Preserve original verdict and execute original payout!

            # Dispute bond forfeited to counterparty

            _pay_native(counterparty, bond_val)

            self._add_reputation(appellant_str, -15)

            self._add_reputation(counterparty_str, 10)

            self.stats_appeals_lost[appellant_str] = self.stats_appeals_lost.get(appellant_str, u32(0)) + u32(1)

            if v.original_verdict == "FORCE_MAJEURE_EXCUSED":

                v.status = STATUS_SETTLED_FORCE_MAJEURE

                v.verdict = "FORCE_MAJEURE_EXCUSED"

                v.reason = f"[APPEAL DISMISSED - ORIGINAL VERDICT PRESERVED] {app_reason}"

                _pay_native(v.carrier, freight_val)

                _pay_native(v.charterer, demurrage_val)

            elif v.original_verdict == "CLEAN_ON_TIME":

                v.status = STATUS_SETTLED_ON_TIME

                v.verdict = "CLEAN_ON_TIME"

                v.reason = f"[APPEAL DISMISSED - ORIGINAL VERDICT PRESERVED] {app_reason}"

                _pay_native(v.carrier, freight_val)

                _pay_native(v.charterer, demurrage_val)

            else:

                v.status = STATUS_SETTLED_DEMURRAGE

                v.verdict = "DEMURRAGE_ENFORCED"

                v.reason = f"[APPEAL DISMISSED - ORIGINAL VERDICT PRESERVED] {app_reason}"

                _pay_native(v.carrier, freight_val + demurrage_val)

    @gl.public.write

    def finalize_settlement(self, voyage_id: str) -> None:

        vid = self._resolve_vid(voyage_id)

        if vid not in self.voyages:

            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]

        if v.status != STATUS_AWAITING_PAYOUT:

            raise ContractError("Voyage is not awaiting settlement payout.")

        sender_str = _addr_str(_get_sender())

        if sender_str != _addr_str(v.charterer) and sender_str != _addr_str(v.carrier):

            raise ContractError("Permission Denied: Only charterer or carrier can finalize payout.")

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

        vid = self._resolve_vid(voyage_id)

        if vid not in self.voyages:

            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]

        if _addr_str(_get_sender()) != _addr_str(v.charterer):

            raise ContractError("Role Violation: Only the charterer can cancel or reclaim booking.")

        current_time = self._get_current_timestamp()

        if v.status == STATUS_IN_TRANSIT:

            transit_grace_secs = bigint(86400)

            if current_time < (v.created_at_time + transit_grace_secs):

                raise ContractError("Cannot reclaim: Carrier actively navigating voyage.")

        elif v.status == STATUS_VOYAGE_OPEN:

            if current_time < v.expires_at_time:

                raise ContractError("Cannot cancel: Voyage duration has not expired.")

        else:

            raise ContractError("Voyage is already settled or disputed.")

        v.status = STATUS_CANCELLED

        v.verdict = "CANCELLED"

        v.reason = "Voyage cancelled and escrow refunded to shippers."

        freight_val = v.freight_amount

        demurrage_val = v.demurrage_deposit

        total_escrow = freight_val + demurrage_val

        v.freight_amount = bigint(0)

        v.demurrage_deposit = bigint(0)

        self.total_maritime_locked = self.total_maritime_locked - total_escrow

        _pay_native(v.charterer, demurrage_val)

        syndicate = self.voyage_syndicates.get(vid, None)

        if syndicate and len(syndicate) > 0:

            for p_obj in syndicate:

                _pay_native(p_obj.funder, p_obj.amount)

        else:

            _pay_native(v.charterer, freight_val)

    # ── Read-only Views ───────────────────────────────────────────────

    @gl.public.view

    def get_voyage(self, voyage_id: str) -> str:

        vid = self._resolve_vid(voyage_id)

        if vid not in self.voyages:

            raise ContractError(f"Voyage {vid} does not exist.")

        v = self.voyages[vid]

        funder_count = len(self.voyage_syndicates[vid]) if vid in self.voyage_syndicates else 1

        data = {

            "voyage_id": str(v.voyage_id),

            "charterer": _addr_str(v.charterer),

            "carrier": _addr_str(v.carrier) if v.status != STATUS_VOYAGE_OPEN else "",

            "dispute_initiator": _addr_str(v.dispute_initiator),

            "freight_amount": str(v.freight_amount),

            "demurrage_deposit": str(v.demurrage_deposit),

            "dispute_bond": str(v.dispute_bond),

            "vessel_imo_number": v.vessel_imo_number,

            "laytime_hours_allowed": int(v.laytime_hours_allowed),

            "ais_tracking_url": v.ais_tracking_url,

            "marine_weather_url": v.marine_weather_url,

            "appeal_evidence_url": v.appeal_evidence_url,

            "dispute_reason": v.dispute_reason,
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

            "is_fast_track": v.is_fast_track,

            "co_funder_count": int(funder_count),

        }

        return json.dumps(data)

    @gl.public.view

    def get_voyage_count(self) -> u64:

        return u64(len(self.voyage_ids))

    @gl.public.view

    def get_stats(self) -> str:

        participants = self._get_all_participants()

        data = {

            "total_voyages": len(self.voyage_ids),

            "total_maritime_locked": str(self.total_maritime_locked),

            "total_voyages_settled": int(self.total_voyages_settled),

            "registered_participants": len(participants),

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

            "completed_voyages": int(self.stats_completed.get(u_str, u32(0))),

            "force_majeure_weather_verified": int(self.stats_force_majeure.get(u_str, u32(0))),

            "demurrage_faults": int(self.stats_demurrage_fault.get(u_str, u32(0))),

            "appeals_won": int(self.stats_appeals_won.get(u_str, u32(0))),

            "appeals_lost": int(self.stats_appeals_lost.get(u_str, u32(0))),

        }

        return json.dumps(dossier)

    @gl.public.view
    def get_all_voyages(self) -> str:
        voyages_list = []
        for vid in self.voyage_ids:
            if vid in self.voyages:
                v = self.voyages[vid]
                funder_count = len(self.voyage_syndicates[vid]) if vid in self.voyage_syndicates else 1
                voyages_list.append({
                    "voyage_id": str(v.voyage_id),
                    "charterer": _addr_str(v.charterer),
                    "carrier": _addr_str(v.carrier) if v.status != STATUS_VOYAGE_OPEN else "",
                    "dispute_initiator": _addr_str(v.dispute_initiator),
                    "freight_amount": str(v.freight_amount),
                    "demurrage_deposit": str(v.demurrage_deposit),
                    "dispute_bond": str(v.dispute_bond),
                    "vessel_imo_number": v.vessel_imo_number,
                    "laytime_hours_allowed": int(v.laytime_hours_allowed),
                    "ais_tracking_url": v.ais_tracking_url,
                    "marine_weather_url": v.marine_weather_url,
                    "appeal_evidence_url": v.appeal_evidence_url,
                    "dispute_reason": v.dispute_reason,
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
                    "co_funder_count": int(funder_count),
                })
        return json.dumps(voyages_list)

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
        syndicate = self.voyage_syndicates.get(vid, None)
        pledges_list = []
        if syndicate:
            for p in syndicate:
                pledges_list.append({
                    "funder": _addr_str(p.funder),
                    "amount": str(p.amount),
                    "role": getattr(p, "role", "SYNDICATE_CO_SHIPPER")
                })
        return json.dumps(pledges_list)
