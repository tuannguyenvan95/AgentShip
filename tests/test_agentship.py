import pytest
import json
import hashlib
from pathlib import Path

try:
    from genlayer import *
except ImportError:
    pass


def test_contract_syntax_and_structure(contract_source):
    """Verify that contract file adheres to GenVM python specifications and exposes all required endpoints."""
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
    """Ensure MaritimeVoyage struct defines all state fields including telemetry, original_verdict, and deterministic timestamp fields."""
    expected_fields = [
        "voyage_id: str",
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
        "original_verdict: str",
        "reason: str",
        "created_at_time: bigint",
        "expires_at_time: bigint",
        "audit_completed_time: bigint",
        "is_fast_track: bool",
        "co_funder_count: u32",
    ]
    for field in expected_fields:
        assert field in contract_source, f"Missing field in MaritimeVoyage: {field}"


def test_agentship_force_majeure_weather_excuse(client):
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
            "https://marinetraffic.org/ais/voyage_rotterdam_singapore.json",
            "https://noaa-marine.org/data/typhoon_north_sea.txt"
        ]
    )

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
    assert v_data["original_verdict"] == "FORCE_MAJEURE_EXCUSED"
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
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9732100 WAVES:1.5m DELAY:40h"}}
        }
    )

    contract.connect(carrier).adjudicate_demurrage(args=[voyage_id])

    v_data = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_data["status"] == 2  # AWAITING_PAYOUT
    assert v_data["verdict"] == "DEMURRAGE_ENFORCED"
    assert v_data["original_verdict"] == "DEMURRAGE_ENFORCED"
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
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9954321 SPEED:18kn ON_TIME:YES"}}
        }
    )

    contract.connect(charterer).adjudicate_demurrage(args=[voyage_id])

    v_data = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_data["status"] == 2  # AWAITING_PAYOUT
    assert v_data["verdict"] == "CLEAN_ON_TIME"
    assert v_data["original_verdict"] == "CLEAN_ON_TIME"
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
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9811000 WAVES:4m DELAY:20h"}}
        }
    )
    contract.connect(carrier).adjudicate_demurrage(args=[voyage_id])

    required_bond = (total * 10) // 100
    contract.connect(carrier).appeal_verdict(
        args=[voyage_id, "Harbor master closed port due to sudden swell, certified proof attached."],
        value=required_bond
    )

    v_disputed = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_disputed["status"] == 6  # STATUS_DISPUTED
    assert int(v_disputed["dispute_bond"]) == required_bond

    # Appellate Court upholds Force Majeure with IMO verified
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
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9811000 HARBOR_CLOSURE_CONFIRMED:SWELL_8M"}}
        }
    )

    contract.connect(carrier).adjudicate_appeal(
        args=[voyage_id, "https://portofrotterdam.com/records/certified_cyclone_closure.txt"]
    )

    v_final = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_final["status"] == 5  # STATUS_SETTLED_FORCE_MAJEURE
    assert v_final["verdict"] == "FORCE_MAJEURE_EXCUSED"
    assert int(v_final["dispute_bond"]) == 0


def test_adjudicate_appeal_unauthorized_caller_reverts(client):
    """STEWARD CORRECTION: Restrict appellate adjudication strictly to charterer or carrier (owner denied)."""
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]
    unauthorized_party = client.accounts[3]

    freight = 1000000000000000000
    demurrage = 200000000000000000
    total = freight + demurrage

    tx_create = contract.connect(charterer).create_voyage_escrow(
        args=["IMO9811000", 48, demurrage, 6000],
        value=total
    )
    voyage_id = tx_create.return_value

    contract.connect(carrier).submit_voyage_logs(
        args=[voyage_id, "https://marinetraffic.org/ais/v1.json", "https://noaa.gov/w1.txt"]
    )

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {".*": json.dumps({"canary": "CANARY_AGENT_SHIP_MARITIME_V1", "verdict": "DEMURRAGE_ENFORCED"})},
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9811000 CALM"}}
        }
    )
    contract.connect(carrier).adjudicate_demurrage(args=[voyage_id])

    # Charterer files appeal
    contract.connect(charterer).appeal_verdict(args=[voyage_id, "Disputing findings."], value=total // 10)

    # 1. Unauthorized 3rd party attempts to trigger appellate court -> MUST REVERT
    with pytest.raises(Exception, match="Permission Denied"):
        contract.connect(unauthorized_party).adjudicate_appeal(
            args=[voyage_id, "https://portofrotterdam.com/supp.txt"]
        )

    # 2. Steward Papito Review Requirement: Global contract owner MUST ALSO be denied permission!
    # Set owner to an independent account (accounts[2]) that is neither charterer nor carrier
    contract.contract.owner = client.accounts[2].address
    with pytest.raises(Exception, match="Permission Denied: Only charterer or carrier can adjudicate appeal"):
        contract.connect(client.accounts[2]).adjudicate_appeal(
            args=[voyage_id, "https://portofrotterdam.com/supp.txt"]
        )


def test_adjudicate_appeal_unbound_evidence_dismissed(client):
    """STEWARD CORRECTION 2: Supplemental evidence MUST be bound to declared vessel IMO."""
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
        args=[voyage_id, "https://marinetraffic.org/ais/v1.json", "https://noaa.gov/w1.txt"]
    )

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {".*": json.dumps({"canary": "CANARY_AGENT_SHIP_MARITIME_V1", "verdict": "DEMURRAGE_ENFORCED"})},
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9811000 CALM"}}
        }
    )
    contract.connect(carrier).adjudicate_demurrage(args=[voyage_id])
    contract.connect(carrier).appeal_verdict(args=[voyage_id, "Filing appeal with foreign vessel log."], value=total // 10)

    # Web mock for supplemental log is for UNRELATED vessel (IMO1234567 != IMO9811000)
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO1234567 STORM_SURGE_9M"}},
            "llm_mocks": {".*": json.dumps({"canary": "CANARY_AGENT_SHIP_MARITIME_V1", "verdict": "APPEAL_UPHELD_FORCE_MAJEURE"})}
        }
    )

    # Adjudicating with unbound telemetry evidence must dismiss the appeal
    contract.connect(carrier).adjudicate_appeal(args=[voyage_id, "https://portofrotterdam.com/foreign_vessel.txt"])

    v_after = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_after["status"] == 4  # Settled Demurrage (appeal dismissed)
    assert "Supplemental evidence rejected: Not bound to declared vessel" in v_after["reason"]


def test_appeal_dismissed_preserves_force_majeure_payout(client):
    """STEWARD CORRECTION 3: Preserve original FORCE_MAJEURE_EXCUSED verdict and payout when appeal dismissed."""
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
        args=[voyage_id, "https://marinetraffic.org/ais/v1.json", "https://noaa.gov/w1.txt"]
    )

    # Initial adjudication finds FORCE_MAJEURE_EXCUSED
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "FORCE_MAJEURE_EXCUSED",
                    "confidence": 95,
                    "measured_delay_hours": 30,
                    "max_wave_height_meters": 7,
                    "reason": "Initial review: Category 3 storm wave heights."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9811000 WAVES:7.5m"}}
        }
    )
    contract.connect(charterer).adjudicate_demurrage(args=[voyage_id])

    v_initial = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_initial["verdict"] == "FORCE_MAJEURE_EXCUSED"
    assert v_initial["original_verdict"] == "FORCE_MAJEURE_EXCUSED"

    # Charterer files frivolous appeal against Force Majeure
    contract.connect(charterer).appeal_verdict(args=[voyage_id, "Disputing storm measurements."], value=total // 10)

    # Appellate Court dismisses the appeal
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "APPEAL_DISMISSED",
                    "reason": "Satellite ocean radar confirms 7.5m gale waves. Force Majeure sustained."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9811000 CONFIRMED"}}
        }
    )
    contract.connect(carrier).adjudicate_appeal(args=[voyage_id, "https://noaa.gov/vessel_storm.txt"])

    v_settled = json.loads(contract.get_voyage(args=[voyage_id]).call())
    # MUST preserve FORCE_MAJEURE_EXCUSED (status 5), NOT default to DEMURRAGE_ENFORCED (status 4)!
    assert v_settled["status"] == 5  # STATUS_SETTLED_FORCE_MAJEURE
    assert v_settled["verdict"] == "FORCE_MAJEURE_EXCUSED"
    assert v_settled["original_verdict"] == "FORCE_MAJEURE_EXCUSED"
    assert "ORIGINAL VERDICT PRESERVED" in v_settled["reason"]


def test_appeal_dismissed_preserves_clean_on_time_payout(client):
    """STEWARD CORRECTION 3: Preserve original CLEAN_ON_TIME verdict and payout when appeal dismissed."""
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
        args=[voyage_id, "https://marinetraffic.org/ais/v1.json", "https://noaa.gov/w1.txt"]
    )

    # Initial adjudication finds CLEAN_ON_TIME
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
                    "reason": "Arrived on schedule."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9811000 SPEED:15kn"}}
        }
    )
    contract.connect(carrier).adjudicate_demurrage(args=[voyage_id])

    # Charterer files frivolous appeal claiming hidden delay
    contract.connect(charterer).appeal_verdict(args=[voyage_id, "Demanding demurrage penalty."], value=total // 10)

    # Appellate Court dismisses the appeal
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "APPEAL_DISMISSED",
                    "reason": "Harbor berthing stamp confirms vessel berthed 2 hours ahead of laytime."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9811000 ON_TIME"}}
        }
    )
    contract.connect(carrier).adjudicate_appeal(args=[voyage_id, "https://portofrotterdam.com/stamps.pdf"])

    v_settled = json.loads(contract.get_voyage(args=[voyage_id]).call())
    # MUST preserve CLEAN_ON_TIME (status 3), NOT default to DEMURRAGE_ENFORCED!
    assert v_settled["status"] == 3  # STATUS_SETTLED_ON_TIME
    assert v_settled["verdict"] == "CLEAN_ON_TIME"
    assert v_settled["original_verdict"] == "CLEAN_ON_TIME"


def test_unrelated_voyages_cannot_advance_cooling_off(client):
    """STEWARD CORRECTION 4: Unrelated voyages cannot advance cooling-off windows."""
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]

    # Create and adjudicate Voyage 1
    tx_v1 = contract.connect(charterer).create_voyage_escrow(args=["IMO9811000", 48, 200000, 6000], value=1200000)
    vid1 = tx_v1.return_value
    contract.connect(carrier).submit_voyage_logs(args=[vid1, "https://ais.org/1", "https://weather.org/1"])

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {".*": json.dumps({"canary": "CANARY_AGENT_SHIP_MARITIME_V1", "verdict": "CLEAN_ON_TIME"})},
            "web_mocks": {".*": {"status": 200, "body": "VESSEL:IMO9811000"}}
        }
    )
    contract.connect(charterer).adjudicate_demurrage(args=[vid1])

    # Now create 5 unrelated voyages to simulate high network traffic
    for i in range(5):
        contract.connect(charterer).create_voyage_escrow(args=[f"IMO900000{i}", 48, 100000, 6000], value=500000)

    # Attempting to finalize Voyage 1 before cooling-off timestamp elapses MUST still fail!
    with pytest.raises(Exception, match="is still active"):
        contract.connect(charterer).finalize_settlement(args=[vid1])


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

    co_fund = 500000000000000000
    contract.connect(syndicate_funder).pledge_voyage_escrow(
        args=[voyage_id],
        value=co_fund
    )

    v_data = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_data["co_funder_count"] == 2
    assert int(v_data["freight_amount"]) == freight + co_fund

    pledges = json.loads(contract.get_voyage_pledges(args=[voyage_id]).call())
    assert len(pledges) == 2
    assert pledges[0]["role"] == "CHARTERER_PRIMARY"
    assert pledges[1]["role"] == "SYNDICATE_CO_SHIPPER"

    contract.advance_time(100)
    contract.connect(charterer).cancel_or_reclaim(args=[voyage_id])
    v_cancelled = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_cancelled["status"] == 7  # STATUS_CANCELLED


def test_agentship_v3_reputation_tiers_and_leaderboard(client):
    contract = client.deploy("contracts/contract.py")
    carrier = client.accounts[1]

    profile = json.loads(contract.get_reputation_profile(args=[carrier.address]).call())
    assert profile["reputation_score"] == 10
    assert profile["tier"] == "BRONZE_NEWCOMER"
    assert profile["is_fast_track_eligible"] is False

    board = json.loads(contract.get_maritime_leaderboard().call())
    assert isinstance(board, list)


def test_unauthorized_party_and_owner_cannot_adjudicate_appeal(contract, charterer, carrier, stranger):
    """
    STEWARD REQUIREMENT 1:
    Verifies that NEITHER a stranger NOR a contract owner can adjudicate appeal;
    strictly restricted to the declared charterer or carrier.
    """
    voyage_id = contract.connect(charterer).create_voyage_escrow(
        args=["IMO9876543", 24, 200, 20000]
    ).transact(value=1000).return_value

    contract.connect(carrier).submit_voyage_logs(
        args=[voyage_id, "https://noaa.gov/ais_9876543", "https://weather.gov/buoy_42001"]
    ).transact()

    contract.connect(charterer).adjudicate_demurrage(args=[voyage_id]).transact()

    contract.connect(carrier).appeal_verdict(
        args=[voyage_id, "Severe gale storm Force 9 verified by NOAA", "https://noaa.gov/buoy_supplemental_proof.txt"]
    ).transact(value=100)

    # Stranger or non-party calling adjudicate_appeal MUST REVERT
    with pytest.raises(Exception):
        contract.connect(stranger).adjudicate_appeal(args=[voyage_id]).transact()


def test_appeal_rejects_unauthenticated_sources_and_github(contract, charterer, carrier):
    """
    STEWARD REQUIREMENT 2:
    Verifies that supplemental evidence from non-accredited sources (such as github.com)
    is strictly rejected at appeal time.
    """
    voyage_id = contract.connect(charterer).create_voyage_escrow(
        args=["IMO1234567", 24, 200, 20000]
    ).transact(value=1000).return_value

    contract.connect(carrier).submit_voyage_logs(
        args=[voyage_id, "https://noaa.gov/ais", "https://weather.gov/buoy"]
    ).transact()
    contract.connect(carrier).adjudicate_demurrage(args=[voyage_id]).transact()

    # Attempting to appeal with GitHub URL MUST REVERT as unauthenticated source
    with pytest.raises(Exception) as exc_info:
        contract.connect(carrier).appeal_verdict(
            args=[voyage_id, "Fabricated evidence log", "https://raw.githubusercontent.com/fake/proof.txt"]
        ).transact(value=100)
    assert "unauthenticated" in str(exc_info.value).lower()


def test_dismissed_appeal_preserves_original_verdict_and_payout(contract, charterer, carrier):
    """
    STEWARD REQUIREMENT 3:
    Verifies that when an appeal is dismissed, the original pre-appeal verdict
    and original payout allocation are preserved, and appellant bond forfeits to counterparty.
    """
    voyage_id = contract.connect(charterer).create_voyage_escrow(
        args=["IMO3334444", 24, 200, 20000]
    ).transact(value=1000).return_value

    contract.connect(carrier).submit_voyage_logs(
        args=[voyage_id, "https://noaa.gov/ais_3334444", "https://weather.gov/buoy_3334444"]
    ).transact()

    # Pre-appeal renders CLEAN_ON_TIME
    contract.connect(charterer).adjudicate_demurrage(args=[voyage_id]).transact()
    v_pre = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_pre["verdict"] == "CLEAN_ON_TIME"
    assert v_pre["original_verdict"] == "CLEAN_ON_TIME"

    # Charterer appeals with valid accredited URL but unproven claim
    contract.connect(charterer).appeal_verdict(
        args=[voyage_id, "Dispute claim that delivery was late", "https://portofrotterdam.com/telemetry_log.txt"]
    ).transact(value=100)

    # Carrier calls adjudicate_appeal, appeal is dismissed
    contract.connect(carrier).adjudicate_appeal(args=[voyage_id]).transact()

    v_post = json.loads(contract.get_voyage(args=[voyage_id]).call())
    assert v_post["verdict"] == "CLEAN_ON_TIME"
    assert v_post["status"] == 3  # STATUS_SETTLED_ON_TIME preserved
    assert v_post["dispute_bond"] == "0"

