import pytest
import json
import hashlib
import sys
import os
import types
from pathlib import Path

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"
CONTRACT_PATH = CONTRACTS_DIR / "contract.py"


@pytest.fixture(scope="session")
def contract_source() -> str:
    """Load the AgentShip intelligent contract source code."""
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ── GENVM RUNTIME ENVIRONMENT SETUP ─────────────────────────────────
# Setup execution primitives so the SUBMITTED CONTRACT can be imported and executed directly.

class MockAddress(str):
    @property
    def as_hex(self) -> str:
        return str(self)

    def lower(self) -> str:
        return str(self).lower()


class MockBigInt(int):
    pass


class MockContractRecipient:
    def __init__(self, address, transfer_log):
        self.address = address
        self.transfer_log = transfer_log

    def emit_transfer(self, value):
        self.transfer_log.append({"to": str(self.address), "value": int(value)})


class MockReturn:
    def __init__(self, calldata):
        self.calldata = calldata


class _MockCallResult:
    def __init__(self, val):
        self._val = val

    def call(self):
        return self._val


class _MockTxResult:
    def __init__(self, return_value):
        self.return_value = return_value

    def transact(self, value=0):
        return self


class MockGL:
    class Contract:
        pass

    class public:
        @staticmethod
        def view(fn): return fn
        @staticmethod
        def write(fn): return fn

    class message:
        sender_address = MockAddress("0x1111111111111111111111111111111111111111")
        sender = MockAddress("0x1111111111111111111111111111111111111111")
        value = MockBigInt(0)

    class nondet:
        class web:
            @staticmethod
            def render(url, mode="text"):
                return ""

        @staticmethod
        def exec_prompt(prompt, response_format="json"):
            return ""

    class vm:
        Return = MockReturn

        @staticmethod
        def run_nondet(leader_fn, validator_fn):
            res = leader_fn()
            ret = MockReturn(calldata=res)
            if not validator_fn(ret):
                raise Exception("Consensus disagreement")
            return res

    def __init__(self):
        self.transfers = []
        self.message_raw = {"datetime": "2026-10-15T12:00:00+00:00"}
        self.provider = None

    def get_contract_at(self, address):
        return MockContractRecipient(address, self.transfers)

    def get_web_page(self, url):
        return self.nondet.web.render(url)

    def exec_prompt(self, prompt):
        return self.nondet.exec_prompt(prompt)


# Install genlayer into sys.modules
mock_gl_inst = MockGL()
mock_gl_mod = types.ModuleType("genlayer")
mock_gl_mod.gl = mock_gl_inst
MockGL.public.write.payable = staticmethod(lambda fn: fn)

mock_gl_mod.Address = MockAddress
mock_gl_mod.bigint = MockBigInt
for t_name in ["u8", "u16", "u32", "u64", "u128", "u256"]:
    setattr(mock_gl_mod, t_name, MockBigInt)
mock_gl_mod.TreeMap = dict
mock_gl_mod.DynArray = list
mock_gl_mod.allow_storage = lambda cls: cls

sys.modules["genlayer"] = mock_gl_mod

# Import the SUBMITTED CONTRACT directly from contracts/contract.py!
sys.path.insert(0, str(CONTRACTS_DIR))
import contract as submitted_contract_module
SubmittedContractClass = submitted_contract_module.Contract


class DeployedContractWrapper:
    """Executes behavioral tests directly against the SUBMITTED CONTRACT class (SubmittedContractClass)."""
    def __init__(self, contract_inst, client):
        self.contract = contract_inst
        self.client = client
        self.current_caller = client.accounts[0]

    def connect(self, account):
        self.current_caller = account
        return self

    def advance_time(self, seconds: int):
        from datetime import datetime, timezone, timedelta
        dt_str = str(mock_gl_inst.message_raw.get("datetime", "2026-10-15T12:00:00+00:00"))
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        new_dt = dt + timedelta(seconds=seconds)
        mock_gl_inst.message_raw["datetime"] = new_dt.isoformat()

    def _prepare_call(self, value=0):
        addr_str = self.current_caller.address if hasattr(self.current_caller, "address") else str(self.current_caller)
        mock_gl_inst.message.sender_address = MockAddress(addr_str)
        mock_gl_inst.message.sender = MockAddress(addr_str)
        mock_gl_inst.message.value = MockBigInt(value)

        # Wire client provider mocks into gl.nondet
        if hasattr(self.client, "provider"):
            web_mocks = getattr(self.client.provider, "web_mocks", {})
            llm_mocks = getattr(self.client.provider, "llm_mocks", {})

            def mock_render(url, mode="text"):
                for pat, val in web_mocks.items():
                    if pat == ".*" or pat in url or url in pat:
                        return val.get("body", "") if isinstance(val, dict) else str(val)
                return f"TELEMETRY: {url}"

            def mock_exec_prompt(prompt, response_format="json"):
                for pat, val in llm_mocks.items():
                    return val
                return json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "CLEAN_ON_TIME",
                    "confidence": 95,
                    "measured_delay_hours": 0,
                    "max_wave_height_meters": 1,
                    "reason": "Default telemetry verification successful."
                })

            mock_gl_inst.nondet.web.render = staticmethod(mock_render)
            mock_gl_inst.nondet.exec_prompt = staticmethod(mock_exec_prompt)

    def create_voyage_escrow(self, args, value=0):
        def _exec(val):
            self._prepare_call(val)
            v_imo, laytime, demurrage_buf, dur_blocks = args
            return self.contract.create_voyage_escrow(
                str(v_imo),
                MockBigInt(laytime),
                MockBigInt(demurrage_buf),
                MockBigInt(dur_blocks)
            )

        if value > 0:
            ret = _exec(value)
            return _MockTxResult(ret)

        class _LazyTx:
            def __init__(self, exec_fn):
                self.exec_fn = exec_fn
            def transact(self, value=0):
                ret = self.exec_fn(value)
                return _MockTxResult(ret)
            @property
            def return_value(self):
                return self.transact(0).return_value
        return _LazyTx(_exec)

    def pledge_voyage_escrow(self, args, value=0):
        self._prepare_call(value)
        vid = str(args[0])
        ret = self.contract.pledge_voyage_escrow(vid)
        return _MockTxResult(ret)

    def submit_voyage_logs(self, args):
        self._prepare_call(0)
        vid, ais_url, weather_url = args
        ret = self.contract.submit_voyage_logs(str(vid), str(ais_url), str(weather_url))
        return _MockTxResult(ret)

    def adjudicate_demurrage(self, args):
        self._prepare_call(0)
        vid = str(args[0])
        ret = self.contract.adjudicate_demurrage(str(vid))
        return _MockTxResult(ret)

    def appeal_verdict(self, args, value=0):
        def _exec(val):
            self._prepare_call(val)
            vid = str(args[0])
            dispute_reason = str(args[1]) if len(args) > 1 else "Dispute justification for appeal."
            supp_url = str(args[2]) if len(args) > 2 else "https://noaa.gov/telemetry_proof.txt"
            return self.contract.appeal_verdict(vid, dispute_reason, supp_url)

        if value > 0:
            ret = _exec(value)
            return _MockTxResult(ret)

        class _LazyTx:
            def __init__(self, exec_fn):
                self.exec_fn = exec_fn
            def transact(self, value=0):
                ret = self.exec_fn(value)
                return _MockTxResult(ret)
            @property
            def return_value(self):
                return self.transact(0).return_value
        return _LazyTx(_exec)

    def adjudicate_appeal(self, args):
        self._prepare_call(0)
        vid = str(args[0])
        if len(args) > 1 and str(args[1]).strip():
            supp_url = str(args[1]).strip()
            v = self.contract.voyages.get(vid)
            if v:
                v.appeal_evidence_url = supp_url
        ret = self.contract.adjudicate_appeal(vid)
        return _MockTxResult(ret)

    def finalize_settlement(self, args):
        self._prepare_call(0)
        vid = str(args[0])
        ret = self.contract.finalize_settlement(str(vid))
        return _MockTxResult(ret)

    def cancel_or_reclaim(self, args):
        self._prepare_call(0)
        vid = str(args[0])
        ret = self.contract.cancel_or_reclaim(str(vid))
        return _MockTxResult(ret)

    def get_voyage(self, args):
        vid = str(args[0])
        return _MockCallResult(self.contract.get_voyage(vid))

    def get_voyage_count(self, args=None):
        return _MockCallResult(int(self.contract.get_voyage_count()))

    def get_all_voyages(self, args=None):
        return _MockCallResult(self.contract.get_all_voyages())

    def get_stats(self, args=None):
        return _MockCallResult(self.contract.get_stats())

    def get_reputation_profile(self, args):
        u_addr = args[0]
        return _MockCallResult(self.contract.get_reputation_profile(MockAddress(str(u_addr))))

    def get_maritime_leaderboard(self, args=None):
        return _MockCallResult(self.contract.get_maritime_leaderboard())

    def get_voyage_pledges(self, args):
        vid = str(args[0])
        return _MockCallResult(self.contract.get_voyage_pledges(vid))


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


class _SimClient:
    def __init__(self):
        self.accounts = [
            _MockAccount("0x1111111111111111111111111111111111111111"),
            _MockAccount("0x2222222222222222222222222222222222222222"),
            _MockAccount("0x3333333333333333333333333333333333333333"),
            _MockAccount("0x4444444444444444444444444444444444444444"),
        ]
        self.provider = _MockProvider()

    def deploy(self, contract_path):
        inst = SubmittedContractClass()
        # Initialize GenVM storage structures
        inst.voyages = {}
        inst.voyage_ids = []
        inst.voyage_syndicates = {}
        inst.reputation_scores = {}
        inst.stats_completed = {}
        inst.stats_force_majeure = {}
        inst.stats_demurrage_fault = {}
        inst.stats_appeals_won = {}
        inst.stats_appeals_lost = {}
        inst.registered_registry = {}
        return DeployedContractWrapper(inst, self)


@pytest.fixture
def client():
    """Provides a client instance for executing behavioral tests against the SUBMITTED CONTRACT directly."""
    return _SimClient()


@pytest.fixture
def contract(client):
    return client.deploy("contracts/contract.py")


@pytest.fixture
def charterer(client):
    return client.accounts[0]


@pytest.fixture
def carrier(client):
    return client.accounts[1]


@pytest.fixture
def stranger(client):
    return client.accounts[3]
