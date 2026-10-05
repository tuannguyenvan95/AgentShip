import json
import time
from genlayer_py import create_client, create_account, studionet

PK = "0x1b807b1df022a40f872596b11565e6b6856547dc66996bd3d5a85b376ea3a0ef"
CONTRACT_ADDRESS = "0x133f95019925c8fAC02BE0bD1b86F947AA50F13F"

def main():
    print("=" * 70, flush=True)
    print("  SEEDING AGENTSHIP ON-CHAIN DEMO VOYAGES (GENLAYER STUDIONET)  ", flush=True)
    print("=" * 70, flush=True)

    acct = create_account(PK)
    client = create_client(chain=studionet, account=acct)

    bal = client.get_balance(acct.address)
    print(f"[+] Deployer Address : {acct.address} (Balance: {bal / 1e18} GEN)", flush=True)

    # 1. Submit logs for Voyage 1 (Carrier role from secondary account or deployer if open)
    # Notice: Role restriction in contract: "Role Violation: Charterer cannot act as vessel carrier."
    # So we need a different account for carrier!
    # Let's derive or use a second test key:
    carrier_pk = "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"
    carrier_acct = create_account(carrier_pk)
    carrier_client = create_client(chain=studionet, account=carrier_acct)

    # Transfer a tiny bit of GEN to carrier for gas if needed
    carrier_bal = client.get_balance(carrier_acct.address)
    print(f"[+] Carrier Address: {carrier_acct.address} (Balance: {carrier_bal / 1e18} GEN)", flush=True)
    if carrier_bal < 0.01 * 1e18:
        print("[*] Funding carrier account with 0.05 GEN...", flush=True)
        funding_tx = client.send_transaction(to=carrier_acct.address, value=int(0.05 * 1e18))
        client.wait_for_transaction_receipt(funding_tx)

    print("\n[*] Carrier submitting AIS & Marine Weather logs for Voyage #1...", flush=True)
    tx_logs = carrier_client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="submit_voyage_logs",
        args=[
            1,
            "https://marinetraffic.org/ais/voyage_rotterdam_singapore.json",
            "https://noaa-marine.org/data/typhoon_north_sea.txt"
        ],
        value=0
    )
    print(f"[+] Logs Tx Hash: {tx_logs}", flush=True)
    carrier_client.wait_for_transaction_receipt(tx_logs)
    print("[+] Voyage #1 logs linked! Status is now IN_TRANSIT.", flush=True)

    # 2. Create Voyage Escrow 2 (Open Booking with Syndicate co-funding)
    print("\n[*] Creating Voyage #2: IMO9732100 (Evergreen Pacific Route)", flush=True)
    demurrage_buf2 = int(0.01 * 1e18)
    total_deposit2 = int(0.03 * 1e18)
    tx2 = client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="create_voyage_escrow",
        args=["IMO9732100", 36, demurrage_buf2, 6000],
        value=total_deposit2
    )
    print(f"[+] Voyage #2 Tx Hash: {tx2}", flush=True)
    client.wait_for_transaction_receipt(tx2)
    print("[+] Voyage #2 Escrow opened!", flush=True)

    # 3. Read final stats and all voyages
    stats = client.read_contract(address=CONTRACT_ADDRESS, function_name="get_stats", args=[])
    print(f"\n[+] Live On-Chain Stats: {stats}", flush=True)
    all_voyages = client.read_contract(address=CONTRACT_ADDRESS, function_name="get_all_voyages", args=[])
    print(f"[+] Live Voyages: {all_voyages}", flush=True)

if __name__ == "__main__":
    main()
