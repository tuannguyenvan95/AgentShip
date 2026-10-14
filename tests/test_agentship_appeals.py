import pytest
import json
try:
    from genlayer import *
except ImportError:
    pass


def test_appeal_dismissed_preserves_original_verdict_and_payout(client):
    """Proves that a dismissed appeal preserves the original ruling and forfeits the bond to counterparty."""
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]

    freight = 1000000000000000000
    demurrage = 200000000000000000
    total = freight + demurrage

    # 1. Charterer creates voyage
    tx = contract.connect(charterer).create_voyage_escrow(
        args=["IMO9876543", 24, demurrage, 100],
        value=total
    )
    vid = str(tx.return_value)

    # 2. Carrier submits logs
    contract.connect(carrier).submit_voyage_logs(
        args=[
            vid,
            "https://marine-ais.org/voyage.json",
            "https://marine-weather.org/buoy.json"
        ]
    )

    # 3. First adjudication renders FORCE_MAJEURE_EXCUSED
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
                    "reason": "Severe gale force sea state."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "IMO9876543 SPEED:5kn WAVES:7m"}}
        }
    )
    contract.connect(charterer).adjudicate_demurrage(args=[vid])

    v_before = json.loads(contract.get_voyage(args=[vid]).call())
    assert v_before["verdict"] == "FORCE_MAJEURE_EXCUSED"
    assert v_before["original_verdict"] == "FORCE_MAJEURE_EXCUSED"

    # 4. Charterer appeals claiming demurrage with 10% bond
    contract.connect(charterer).appeal_verdict(
        args=[vid, "Charterer claims ship delayed due to engine malfunction, not weather."],
        value=120000000000000000  # 10% of 1.2 GEN
    )

    # 5. Appellate court dismisses appeal because evidence lacks merit
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "APPEAL_DISMISSED",
                    "reason": "Supplemental harbor logs confirm weather closure."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "IMO9876543 HARBOR_LOG: PORT_CLOSED_BY_HARBORMASTER"}}
        }
    )
    contract.connect(carrier).adjudicate_appeal(
        args=[vid, "https://harbor-authority.org/imo9876543_log.txt"]
    )

    # 6. Verify status preserves FORCE_MAJEURE_EXCUSED, not demurrage
    v_after = json.loads(contract.get_voyage(args=[vid]).call())
    assert v_after["status"] == 5  # STATUS_SETTLED_FORCE_MAJEURE
    assert v_after["verdict"] == "FORCE_MAJEURE_EXCUSED"
    assert v_after["freight_amount"] == "0"
    assert v_after["demurrage_deposit"] == "0"
    assert v_after["dispute_bond"] == "0"


def test_appeal_rejects_unbound_vessel_evidence(client):
    """Proves that supplemental evidence without the declared vessel IMO is dismissed."""
    contract = client.deploy("contracts/contract.py")
    charterer = client.accounts[0]
    carrier = client.accounts[1]

    tx = contract.connect(charterer).create_voyage_escrow(
        args=["IMO1234567", 24, 200000000000000000, 100],
        value=1200000000000000000
    )
    vid = str(tx.return_value)

    contract.connect(carrier).submit_voyage_logs(
        args=[vid, "https://ais.org/log.json", "https://weather.org/log.json"]
    )

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_SHIP_MARITIME_V1",
                    "verdict": "DEMURRAGE_ENFORCED",
                    "confidence": 90,
                    "measured_delay_hours": 40,
                    "max_wave_height_meters": 2,
                    "reason": "Calm seas delay."
                })
            },
            "web_mocks": {".*": {"status": 200, "body": "IMO1234567 CALM"}}
        }
    )
    contract.connect(carrier).adjudicate_demurrage(args=[vid])

    # Carrier appeals
    contract.connect(carrier).appeal_verdict(
        args=[vid, "Carrier submits logs from another ship."],
        value=120000000000000000
    )

    # Web returns log for unrelated IMO9999999
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {".*": {"status": 200, "body": "LOGS FOR VESSEL IMO9999999 - UNRELATED CARRIER"}}
        }
    )

    # Appeal is automatically dismissed due to IMO mismatch
    contract.connect(charterer).adjudicate_appeal(
        args=[vid, "https://fake-marine.org/unrelated_ship.txt"]
    )

    v_after = json.loads(contract.get_voyage(args=[vid]).call())
    assert v_after["status"] == 4  # STATUS_SETTLED_DEMURRAGE preserved
    assert "Not bound to declared vessel IMO" in v_after["reason"]
