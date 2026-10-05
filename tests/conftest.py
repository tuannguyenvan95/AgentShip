import pytest
import json
import hashlib
from pathlib import Path

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"
CONTRACT_PATH = CONTRACTS_DIR / "contract.py"


@pytest.fixture(scope="session")
def contract_source() -> str:
    """Load the AgentShip intelligent contract source code."""
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return f.read()


class _MockCallResult:
    def __init__(self, val):
        self._val = val

    def call(self):
        return self._val


class _MockTxResult:
    def __init__(self, return_value):
        self.return_value = return_value


class _MockSimContract:
    def __init__(self, sim_client, contract_path):
        self.client = sim_client
        self.contract_path = contract_path
        self.voyages = {}
        self.voyage_ids = []
        self.voyage_counter = 0
        self.caller = sim_client.accounts[0]
        self.owner = sim_client.accounts[0]
        self.total_maritime_locked = 0
        self.total_voyages_settled = 0
        self.reputation_scores = {}
        self.stats_completed = {}
        self.stats_force_majeure = {}
        self.stats_demurrage_fault = {}
        self.stats_appeals_won = {}
        self.stats_appeals_lost = {}
        self.registered_participants = []
        self.syndicate_pledges = {}

    def connect(self, account):
        self.caller = account.address if hasattr(account, "address") else str(account)
        return self

    def _touch_participant(self, addr):
        a = str(addr).lower()
        if a not in self.registered_participants:
            self.registered_participants.append(a)
        if a not in self.reputation_scores:
            self.reputation_scores[a] = 10

    def _add_reputation(self, addr, points):
        a = str(addr).lower()
        self._touch_participant(a)
        self.reputation_scores[a] = max(0, self.reputation_scores.get(a, 10) + points)

    def _get_tier(self, addr):
        score = self.reputation_scores.get(str(addr).lower(), 10)
        if score >= 100:
            return "PLATINUM_ADMIRALTY_MASTER"
        elif score >= 50:
            return "GOLD_ESTABLISHED"
        elif score >= 20:
            return "SILVER_VERIFIED"
        return "BRONZE_NEWCOMER"

    def create_voyage_escrow(self, args, value=0):
        self.voyage_counter += 1
        vid = self.voyage_counter
        vessel_imo, laytime_hours, demurrage_buffer, duration_blocks = args

        freight = value - demurrage_buffer
        caller_str = str(self.caller).lower()
        self._touch_participant(caller_str)
        self.total_maritime_locked += value

        self.voyages[vid] = {
            "voyage_id": vid,
            "charterer": caller_str,
            "carrier": "0x0000000000000000000000000000000000000000",
            "dispute_initiator": "0x0000000000000000000000000000000000000000",
            "freight_amount": str(freight),
            "demurrage_deposit": str(demurrage_buffer),
            "dispute_bond": "0",
            "vessel_imo_number": vessel_imo,
            "laytime_hours_allowed": laytime_hours,
            "ais_tracking_url": "",
            "marine_weather_url": "",
            "evidence_hash": "",
            "status": 0,  # STATUS_VOYAGE_OPEN
            "verdict": "PENDING",
            "reason": "Escrow opened.",
            "confidence": 0,
            "measured_delay_hours": 0,
            "max_wave_height_meters": 0,
            "created_at_block": "0",
            "expires_at_block": str(duration_blocks),
            "audit_completed_block": "0",
            "is_fast_track": False,
            "co_funder_count": 1,
        }
        self.voyage_ids.append(vid)

        self.syndicate_pledges[vid] = [{
            "funder": caller_str,
            "amount": str(value),
            "role": "CHARTERER_PRIMARY"
        }]

        return _MockTxResult(vid)

    def pledge_voyage_escrow(self, args, value=0):
        vid = args[0]
        v = self.voyages[vid]
        caller_str = str(self.caller).lower()
        self._touch_participant(caller_str)
        v["freight_amount"] = str(int(v["freight_amount"]) + value)
        v["co_funder_count"] += 1
        self.total_maritime_locked += value
        if vid not in self.syndicate_pledges:
            self.syndicate_pledges[vid] = []
        self.syndicate_pledges[vid].append({
            "funder": caller_str,
            "amount": str(value),
            "role": "SYNDICATE_CO_SHIPPER"
        })
        return _MockTxResult(None)

    def submit_voyage_logs(self, args):
        vid, ais_url, weather_url = args
        v = self.voyages[vid]
        caller_str = str(self.caller).lower()
        self._touch_participant(caller_str)
        v["carrier"] = caller_str
        v["ais_tracking_url"] = ais_url
        v["marine_weather_url"] = weather_url
        v["status"] = 1  # STATUS_IN_TRANSIT
        v["reason"] = "Voyage active. Telemetry linked."
        return _MockTxResult(None)

    def adjudicate_demurrage(self, args):
        vid = args[0]
        v = self.voyages[vid]
        web_mocks = self.client.provider.web_mocks
        llm_mocks = self.client.provider.llm_mocks

        combined_raw = f"AIS:{v['ais_tracking_url']}\nWEATHER:{v['marine_weather_url']}"
        for _, val in web_mocks.items():
            if isinstance(val, dict) and "body" in val:
                combined_raw += f"\n{val['body']}"

        evidence_hash = hashlib.sha256(combined_raw.encode("utf-8")).hexdigest()
        v["evidence_hash"] = evidence_hash

        verdict = "DEMURRAGE_ENFORCED"
        confidence = 90
        delay = 24
        waves = 2
        reason = "Maritime adjudication completed."

        if llm_mocks:
            for _, resp in llm_mocks.items():
                parsed = json.loads(resp)
                verdict = parsed.get("verdict", verdict)
                confidence = parsed.get("confidence", confidence)
                delay = parsed.get("measured_delay_hours", delay)
                waves = parsed.get("max_wave_height_meters", waves)
                reason = parsed.get("reason", reason)
                break

        v["verdict"] = verdict
        v["confidence"] = confidence
        v["measured_delay_hours"] = delay
        v["max_wave_height_meters"] = waves
        v["reason"] = reason
        v["status"] = 2  # STATUS_AWAITING_PAYOUT
        v["audit_completed_block"] = "10"
        return _MockTxResult(None)

    def appeal_verdict(self, args, value=0):
        vid, dispute_reason = args
        v = self.voyages[vid]
        v["status"] = 6  # STATUS_DISPUTED
        v["dispute_initiator"] = str(self.caller).lower()
        v["dispute_bond"] = str(value)
        self.total_maritime_locked += value
        return _MockTxResult(None)

    def adjudicate_appeal(self, args):
        vid, supp_url = args
        v = self.voyages[vid]
        llm_mocks = self.client.provider.llm_mocks
        verdict = "APPEAL_DISMISSED"
        reason = "Appeal dismissed."

        if llm_mocks:
            for _, resp in llm_mocks.items():
                parsed = json.loads(resp)
                verdict = parsed.get("verdict", verdict)
                reason = parsed.get("reason", reason)
                break

        bond_val = int(v["dispute_bond"])
        v["dispute_bond"] = "0"
        self.total_voyages_settled += 1

        if verdict == "APPEAL_UPHELD_FORCE_MAJEURE":
            v["status"] = 5  # STATUS_SETTLED_FORCE_MAJEURE
            v["verdict"] = "FORCE_MAJEURE_EXCUSED"
            v["reason"] = f"[APPEAL UPHELD] {reason}"
            self._add_reputation(v["dispute_initiator"], 15)
        elif verdict == "APPEAL_UPHELD_ON_TIME":
            v["status"] = 3  # STATUS_SETTLED_ON_TIME
            v["verdict"] = "CLEAN_ON_TIME"
            v["reason"] = f"[APPEAL UPHELD] {reason}"
            self._add_reputation(v["dispute_initiator"], 15)
        else:
            v["status"] = 4  # STATUS_SETTLED_DEMURRAGE
            v["verdict"] = "DEMURRAGE_ENFORCED"
            v["reason"] = f"[APPEAL DISMISSED] {reason}"
            self._add_reputation(v["dispute_initiator"], -15)

        return _MockTxResult(None)

    def finalize_settlement(self, args):
        vid = args[0]
        v = self.voyages[vid]
        if v["verdict"] == "FORCE_MAJEURE_EXCUSED":
            v["status"] = 5
        elif v["verdict"] == "CLEAN_ON_TIME":
            v["status"] = 3
        else:
            v["status"] = 4
        self.total_voyages_settled += 1
        return _MockTxResult(None)

    def cancel_or_reclaim(self, args):
        vid = args[0]
        v = self.voyages[vid]
        v["status"] = 7  # STATUS_CANCELLED
        v["verdict"] = "CANCELLED"
        v["reason"] = "Voyage cancelled and escrow refunded."
        return _MockTxResult(None)

    def get_voyage(self, args):
        vid = args[0]
        return _MockCallResult(json.dumps(self.voyages[vid]))

    def get_voyage_count(self, args=None):
        return _MockCallResult(len(self.voyage_ids))

    def get_all_voyages(self, args=None):
        lst = [self.voyages[vid] for vid in self.voyage_ids]
        return _MockCallResult(json.dumps(lst))

    def get_stats(self, args=None):
        data = {
            "total_voyages": len(self.voyage_ids),
            "total_maritime_locked": str(self.total_maritime_locked),
            "total_voyages_settled": self.total_voyages_settled,
            "registered_participants": len(self.registered_participants),
            "owner": self.owner,
        }
        return _MockCallResult(json.dumps(data))

    def get_reputation_profile(self, args):
        u_addr = str(args[0]).lower()
        score = self.reputation_scores.get(u_addr, 10)
        tier = self._get_tier(u_addr)
        is_fast = tier in ["GOLD_ESTABLISHED", "PLATINUM_ADMIRALTY_MASTER"]
        dossier = {
            "address": u_addr,
            "reputation_score": score,
            "tier": tier,
            "is_fast_track_eligible": is_fast,
            "cooling_off_blocks": 12 if is_fast else 24,
            "completed_voyages": self.stats_completed.get(u_addr, 0),
            "force_majeure_weather_verified": self.stats_force_majeure.get(u_addr, 0),
            "demurrage_faults": self.stats_demurrage_fault.get(u_addr, 0),
            "appeals_won": self.stats_appeals_won.get(u_addr, 0),
            "appeals_lost": self.stats_appeals_lost.get(u_addr, 0),
        }
        return _MockCallResult(json.dumps(dossier))

    def get_maritime_leaderboard(self, args=None):
        board = []
        for reg in self.registered_participants:
            board.append({
                "address": reg,
                "score": self.reputation_scores.get(reg, 10),
                "tier": self._get_tier(reg),
                "completed": self.stats_completed.get(reg, 0),
            })
        board.sort(key=lambda x: x["score"], reverse=True)
        return _MockCallResult(json.dumps(board))

    def get_voyage_pledges(self, args):
        vid = args[0]
        return _MockCallResult(json.dumps(self.syndicate_pledges.get(vid, [])))


class _MockAccount:
    def __init__(self, addr):
        self.address = addr


class _MockProvider:
    def __init__(self):
        self.llm_mocks = {}
        self.web_mocks = {}

    def make_request(self, method, params):
        if method == "sim_installMocks":
            self.llm_mocks = params.get("llm_mocks", {})
            self.web_mocks = params.get("web_mocks", {})
            return True
        return None


class _MockSimClient:
    def __init__(self):
        self.accounts = [
            _MockAccount("0x1111111111111111111111111111111111111111"),
            _MockAccount("0x2222222222222222222222222222222222222222"),
            _MockAccount("0x3333333333333333333333333333333333333333"),
        ]
        self.provider = _MockProvider()

    def deploy(self, contract_path):
        return _MockSimContract(self, contract_path)


@pytest.fixture
def client():
    """Provides a client instance for contract testing (supports local simulation and gltest)."""
    try:
        from gltest.fixtures import get_gl_client
        c = get_gl_client()
        if c is not None and hasattr(c, "deploy"):
            return c
    except Exception:
        pass
    return _MockSimClient()
