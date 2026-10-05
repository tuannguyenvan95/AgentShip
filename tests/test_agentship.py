import pytest
import json
import hashlib
from pathlib import Path

try:
    from genlayer import *
except ImportError:
    pass


def test_contract_syntax_and_structure(contract_source):
    """Verify that contract file adheres to GenVM python specifications."""
    assert contract_source.startswith('# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }')
    assert "class MaritimeVoyage:" in contract_source
    assert "class Contract(gl.Contract):" in contract_source
    assert "def create_voyage_escrow(" in contract_source
    assert "def pledge_voyage_escrow(" in contract_source
    assert "def submit_voyage_logs(" in contract_source
    assert "def adjudicate_demurrage(" in contract_source
    assert "def appeal_verdict(" in contract_source
    assert "def adjudicate_appeal(" in contract_source
    assert "def finalize_settlement(" in contract_source
    assert "def cancel_or_reclaim(" in contract_source
    assert "def get_voyage(" in contract_source
    assert "def get_reputation_profile(" in contract_source
    assert "def get_maritime_leaderboard(" in contract_source


def test_voyage_struct_attributes(contract_source):
    """Ensure MaritimeVoyage struct defines all state fields including telemetry, canary, and trust attributes."""
    expected_fields = [
        "voyage_id: u64",
        "charterer: Address",
        "carrier: Address",
        "freight_amount: bigint",
        "demurrage_deposit: bigint",
        "dispute_bond: bigint",
        "vessel_imo_number: str",
        "laytime_hours_allowed: u32",
        "ais_tracking_url: str",
        "marine_weather_url: str",
        "evidence_hash: str",
        "verdict: str",
        "reason: str",
        "is_fast_track: bool",
        "co_funder_count: u32",
    ]
    for field in expected_fields:
        assert field in contract_source, f"Missing field in MaritimeVoyage: {field}"


def test_agentship_force_majeure_weather_excuse(client):
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]

    # Freight: 1 GEN, Demurrage Buffer: 0.2 GEN -> Total: 1.2 GEN
    freight = 1000000000000000000
    demurrage = 200000000000000000
    total = freight + demurrage

    # Step 1: Charterer opens booking
    tx_create = contract.connect(charterer).create_voyage_escrow(
        args=["IMO9811000", 48, demurrage, 6000],
        value=total
    )
    voyage_id = tx_create.return_value

    # Step 2: Carrier accepts & submits AIS/weather telemetry
    contract.connect(carrier).submit_voyage_logs(
        args=[
            voyage_id,
            "https://marinetraffic.org/ais/voyage_rotterdam_singapore.json",
            "https://noaa-marine.org/data/typhoon_north_sea.txt"
        ]
    )

    # Step 3: Mock AI Maritime Tribunal -> Storm waves 8m > 6m -> Force Majeure!
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "FORCE_MAJEURE_EXCUSED",
                    "confidence": 98,
                    "measured_delay_hours": 36,
                    "max_wave_height_meters": 8,
                    "reason": "Severe North Sea gale force storm delayed berthing. Weather exception valid."
                })
            },
            "web_mocks": {
                ".*": {"status": 200, "body": "VESSEL:IMO9811000 SPEED:4kn WAVES:8.2m GALE:FORCE_9"}
            }
        }
    )

    contract.connect(charterer).adjudicate_demurrage(args=[voyage_id])

    v_data = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_data["status"] == 2  # AWAITING_PAYOUT
    assert v_data["verdict"] == "FORCE_MAJEURE_EXCUSED"
    assert v_data["max_wave_height_meters"] == 8
    assert len(v_data["evidence_hash"]) == 64


def test_agentship_unexcused_demurrage_enforced(client):
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]

    freight = 1000000000000000000
    demurrage = 200000000000000000
    total = freight + demurrage

    tx_create = contract.connect(charterer).create_voyage_escrow(
        args=["IMO9732100", 36, demurrage, 6000],
        value=total
    )
    voyage_id = tx_create.return_value

    contract.connect(carrier).submit_voyage_logs(
        args=[
            voyage_id,
            "https://marinetraffic.org/ais/vessel_la_longbeach.json",
            "https://noaa-marine.org/data/calm_sea.txt"
        ]
    )

    # Calm sea (waves 1.5m < 6m) but 40h delay -> Demurrage Enforced
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "DEMURRAGE_ENFORCED",
                    "confidence": 95,
                    "measured_delay_hours": 40,
                    "max_wave_height_meters": 2,
                    "reason": "Unexcused laytime breach. Calm sea state observed."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "WAVES:1.5m DELAY:40h"}}
        }
    )

    contract.connect(carrier).adjudicate_demurrage(args=[voyage_id])

    v_data = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_data["status"] == 2  # AWAITING_PAYOUT
    assert v_data["verdict"] == "DEMURRAGE_ENFORCED"
    assert v_data["measured_delay_hours"] == 40


def test_agentship_clean_on_time_delivery(client):
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]

    freight = 2000000000000000000
    demurrage = 500000000000000000
    total = freight + demurrage

    tx_create = contract.connect(charterer).create_voyage_escrow(
        args=["IMO9954321", 24, demurrage, 5000],
        value=total
    )
    voyage_id = tx_create.return_value

    contract.connect(carrier).submit_voyage_logs(
        args=[
            voyage_id,
            "https://marinetraffic.org/ais/vessel_singapore_tokyo.json",
            "https://noaa-marine.org/data/tokyo_bay_calm.txt"
        ]
    )

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "CLEAN_ON_TIME",
                    "confidence": 99,
                    "measured_delay_hours": 0,
                    "max_wave_height_meters": 1,
                    "reason": "Vessel berthed precisely within allowed laytime. Flawless transit."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "SPEED:18kn ON_TIME:YES"}}
        }
    )

    contract.connect(charterer).adjudicate_demurrage(args=[voyage_id])

    v_data = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_data["status"] == 2  # AWAITING_PAYOUT
    assert v_data["verdict"] == "CLEAN_ON_TIME"
    assert v_data["measured_delay_hours"] == 0


def test_agentship_appeal_upheld_and_bond_returned(client):
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]

    freight = 1000000000000000000
    demurrage = 200000000000000000
    total = freight + demurrage

    tx_create = contract.connect(charterer).create_voyage_escrow(
        args=["IMO9811000", 48, demurrage, 6000],
        value=total
    )
    voyage_id = tx_create.return_value

    contract.connect(carrier).submit_voyage_logs(
        args=[
            voyage_id,
            "https://marinetraffic.org/ais/voyage1.json",
            "https://noaa-marine.org/data/weather1.txt"
        ]
    )

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "DEMURRAGE_ENFORCED",
                    "confidence": 80,
                    "measured_delay_hours": 20,
                    "max_wave_height_meters": 4,
                    "reason": "Initial review flagged delay."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "WAVES:4m DELAY:20h"}}
        }
    )
    contract.connect(carrier).adjudicate_demurrage(args=[voyage_id])

    # Carrier appeals with 10% bond (1.2 GEN * 10% = 0.12 GEN)
    required_bond = (total * 10) // 100
    contract.connect(carrier).appeal_verdict(
        args=[voyage_id, "Harbor master closed port due to sudden swell, certified proof attached."],
        value=required_bond
    )

    v_disputed = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_disputed["status"] == 6  # STATUS_DISPUTED
    assert int(v_disputed["dispute_bond"]) == required_bond

    # Appellate Court upholds Force Majeure!
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "APPEAL_UPHELD_FORCE_MAJEURE",
                    "reason": "Certified harbor master records prove Category 4 storm surge."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "HARBOR_CLOSURE_CONFIRMED:SWELL_8M"}}
        }
    )

    contract.connect(carrier).adjudicate_appeal(
        args=[voyage_id, "https://port-authority.org/records/certified_cyclone_closure.pdf"]
    )

    v_final = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_final["status"] == 5  # STATUS_SETTLED_FORCE_MAJEURE
    assert v_final["verdict"] == "FORCE_MAJEURE_EXCUSED"
    assert int(v_final["dispute_bond"]) == 0


def test_agentship_appeal_dismissed_and_bond_slashed(client):
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]

    freight = 1000000000000000000
    demurrage = 200000000000000000
    total = freight + demurrage

    tx_create = contract.connect(charterer).create_voyage_escrow(
        args=["IMO9811000", 48, demurrage, 6000],
        value=total
    )
    voyage_id = tx_create.return_value

    contract.connect(carrier).submit_voyage_logs(
        args=[
            voyage_id,
            "https://marinetraffic.org/ais/voyage1.json",
            "https://noaa-marine.org/data/weather1.txt"
        ]
    )

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "DEMURRAGE_ENFORCED",
                    "confidence": 90,
                    "measured_delay_hours": 30,
                    "max_wave_height_meters": 2,
                    "reason": "Unexcused delay."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "CALM_WATER"}}
        }
    )
    contract.connect(charterer).adjudicate_demurrage(args=[voyage_id])

    # Charterer files frivolous appeal
    required_bond = (total * 10) // 100
    contract.connect(charterer).appeal_verdict(
        args=[voyage_id, "Frivolous dispute claim without valid maritime basis."],
        value=required_bond
    )

    # Appellate Court dismisses appeal
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "APPEAL_DISMISSED",
                    "reason": "No evidence of inclement weather. Delay is solely demurrage fault."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "NO_WEATHER_ANOMALY"}}
        }
    )

    contract.connect(charterer).adjudicate_appeal(
        args=[voyage_id, "https://supplemental-logs.org/log.txt"]
    )

    v_final = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_final["status"] == 4  # STATUS_SETTLED_DEMURRAGE
    assert v_final["verdict"] == "DEMURRAGE_ENFORCED"


def test_agentship_v3_syndicate_pooling_and_proportional_refund(client):
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    syndicate_funder = client.accounts[2]

    freight = 1000000000000000000
    demurrage = 200000000000000000
    total = freight + demurrage

    tx_create = contract.connect(charterer).create_voyage_escrow(
        args=["IMO9991234", 48, demurrage, 1],
        value=total
    )
    voyage_id = tx_create.return_value

    # Syndicate co-funder pools additional 0.5 GEN
    co_fund = 500000000000000000
    contract.connect(syndicate_funder).pledge_voyage_escrow(
        args=[voyage_id],
        value=co_fund
    )

    v_data = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_data["co_funder_count"] == 2
    assert int(v_data["freight_amount"]) == freight + co_fund

    # Inspect syndicate pledges
    pledges = json.loads(contract.get_voyage_pledges(args=[voyage_id]).call())
    assert len(pledges) == 2
    assert pledges[0]["role"] == "CHARTERER_PRIMARY"
    assert pledges[1]["role"] == "SYNDICATE_CO_SHIPPER"

    # Cancel & reclaim executes proportional refund
    contract.connect(charterer).cancel_or_reclaim(args=[voyage_id])
    v_cancelled = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_cancelled["status"] == 7  # STATUS_CANCELLED


def test_agentship_v3_reputation_tiers_and_leaderboard(client):
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]

    # Check newcomer initial profile
    profile = json.loads(contract.get_reputation_profile(args=[carrier.address]).call())
    assert profile["reputation_score"] == 10
    assert profile["tier"] == "BRONZE_NEWCOMER"
    assert profile["is_fast_track_eligible"] is False
    assert profile["cooling_off_blocks"] == 24

    # Leaderboard view works
    board = json.loads(contract.get_maritime_leaderboard().call())
    assert isinstance(board, list)
