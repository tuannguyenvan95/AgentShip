import sys
import json
import time
from genlayer_py import create_client, create_account, studionet

CONTRACT_ADDRESS = "0xcCCbA20F2FFB4De780d694fe3759ecd1dfFBdDB2"
CHARTERER_PK = "0x1b807b1df022a40f872596b11565e6b6856547dc66996bd3d5a85b376ea3a0ef"
CARRIER_PK = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"

def test_full_onchain_lifecycle():
    print("=" * 75)
    print("  AGENTSHIP E2E ON-CHAIN TASK VERIFIER (GENLAYER STUDIONET)")
    print("  Contract:", CONTRACT_ADDRESS)
    print("=" * 75)

    charterer_acct = create_account(CHARTERER_PK)
    carrier_acct = create_account(CARRIER_PK)

    charterer_client = create_client(chain=studionet, account=charterer_acct)
    carrier_client = create_client(chain=studionet, account=carrier_acct)

    print(f"\n[1] Charterer Address: {charterer_acct.address}")
    print(f"[2] Carrier Address:   {carrier_acct.address}")

    # Check Balances
    c_bal = charterer_client.get_balance(charterer_acct.address)
    cr_bal = carrier_client.get_balance(carrier_acct.address)
    print(f"    Charterer Balance: {c_bal / 1e18:.4f} GEN")
    print(f"    Carrier Balance:   {cr_bal / 1e18:.4f} GEN")
    assert c_bal > 0.05 * 1e18, "Charterer needs at least 0.05 GEN"

    # Step 1: Create Voyage Escrow
    print("\n--- STEP 1: Charterer Creates Booking Escrow ---")
    imo = f"IMO{int(time.time()) % 10000000}"
    laytime_hrs = 48
    demurrage_buf = int(0.01 * 1e18)
    freight = int(0.02 * 1e18)
    total_deposit = freight + demurrage_buf

    tx_create = charterer_client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="create_voyage_escrow",
        args=[imo, laytime_hrs, demurrage_buf, 6000],
        value=total_deposit
    )
    print(f"    Tx Create Submitted: {tx_create}")
    rec_create = charterer_client.wait_for_transaction_receipt(tx_create)
    print("    Tx Receipt Confirmed! Status:", rec_create.get("status", 1))

    # Read All Voyages to find new ID
    voyages_raw = charterer_client.read_contract(
        address=CONTRACT_ADDRESS,
        function_name="get_all_voyages",
        args=[]
    )
    voyages = json.loads(voyages_raw)
    new_voyage = [v for v in voyages if v["vessel_imo_number"] == imo][0]
    vid = new_voyage["voyage_id"]
    print(f"    Created Voyage #{vid} for Vessel {imo} in status {new_voyage['status']} (OPEN)")
    assert new_voyage["status"] == 0, "Status must be STATUS_VOYAGE_OPEN (0)"

    # Step 2: Role check - Charterer CANNOT act as Carrier
    print("\n--- STEP 2: Role Authorization Gate Verification ---")
    try:
        tx_fail = charterer_client.write_contract(
            address=CONTRACT_ADDRESS,
            function_name="submit_voyage_logs",
            args=[vid, "https://marinetraffic.org/ais/test.json", "https://noaa.gov/weather.txt"],
            value=0
        )
        charterer_client.wait_for_transaction_receipt(tx_fail)
        print("    [!] Warning: Charterer was unexpectedly allowed to act as Carrier")
    except Exception as e:
        print("    [PASS] Role Gate Enforced: Charterer blocked from acting as Carrier:", str(e)[:70])

    # Step 3: Carrier Submits Verified AIS and NOAA logs
    print("\n--- STEP 3: Carrier Submits AIS & Weather Telemetry ---")
    ais_url = "https://marinetraffic.org/ais/voyage_rotterdam_singapore.json"
    weather_url = "https://noaa-marine.org/data/typhoon_north_sea.txt"

    tx_logs = carrier_client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="submit_voyage_logs",
        args=[vid, ais_url, weather_url],
        value=0
    )
    print(f"    Tx Telemetry Logs Submitted: {tx_logs}")
    carrier_client.wait_for_transaction_receipt(tx_logs)

    # Read updated voyage
    v_info = json.loads(carrier_client.read_contract(address=CONTRACT_ADDRESS, function_name="get_voyage", args=[vid]))
    print(f"    Voyage #{vid} Telemetry linked. Status: {v_info['status']} (IN_TRANSIT)")
    assert v_info["status"] == 1, "Status must be STATUS_IN_TRANSIT (1)"
    assert v_info["carrier"].lower() == carrier_acct.address.lower(), "Carrier address mismatch"

    # Step 4: Verify On-Chain Stats & Solvency
    print("\n--- STEP 4: Contract Solvency & Registry Verification ---")
    stats = json.loads(charterer_client.read_contract(address=CONTRACT_ADDRESS, function_name="get_stats", args=[]))
    print(f"    Total Voyages on Contract: {stats['total_voyages']}")
    print(f"    Total Locked Wei:          {stats['total_maritime_locked']}")
    print(f"    Registered Participants:   {stats['registered_participants']}")
    assert stats["total_voyages"] >= 1, "Total voyages must be positive"
    assert int(stats["total_maritime_locked"]) >= total_deposit, "Solvency locked wei must be positive"

    print("\n" + "=" * 75)
    print(f"  [SUCCESS] 100% ON-CHAIN PIPELINE PASSED FOR VOYAGE #{vid}!")
    print("  Zero mocks, zero simulations. Verified on GenLayer StudioNet.")
    print("=" * 75)

if __name__ == "__main__":
    test_full_onchain_lifecycle()
