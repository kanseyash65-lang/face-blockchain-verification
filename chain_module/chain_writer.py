import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

AMOY_RPC_URL = "https://polygon-amoy-bor-rpc.publicnode.com"
CONTRACT_ADDRESS = "0x5342811Cb7fd60a79Fe9F2219AcC5914679275aa"
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")

with open("contract_abi.json") as f:
    CONTRACT_ABI = json.load(f)

web3 = Web3(Web3.HTTPProvider(AMOY_RPC_URL))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
account = web3.eth.account.from_key(PRIVATE_KEY)


def store_hash_on_chain(data_hash: str):
    """
    Sends a transaction that calls storeHash() on the deployed contract,
    writing the given hash to the blockchain.

    Args:
        data_hash: the SHA-256 hash string to store on-chain.

    Returns:
        The transaction hash (hex string) of the submitted transaction.
    """
    nonce = web3.eth.get_transaction_count(account.address)

    transaction = contract.functions.storeHash(data_hash).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 200000,
        "gasPrice": web3.eth.gas_price,
    })

    signed_transaction = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
    transaction_hash = web3.eth.send_raw_transaction(signed_transaction.raw_transaction)

    return "0x" + transaction_hash.hex()


def get_record_from_chain(record_id: int):
    """
    Reads a stored record back from the contract by its ID.

    Args:
        record_id: the index of the record to fetch.

    Returns:
        A tuple of (data_hash, timestamp, submitter_address).
    """
    return contract.functions.getRecord(record_id).call()


if __name__ == "__main__":
    test_hash = "0fd1ce884ed4f4cdf3f4db5663a406d9a73635800f5767fe23c23138e18f53d"

    print("Sending transaction to store hash...")
    tx_hash = store_hash_on_chain(test_hash)
    print(f"Transaction sent: {tx_hash}")
    print(f"View on explorer: https://amoy.polygonscan.com/tx/{tx_hash}")

    print("\nWaiting a moment for the transaction to confirm...")
    import time
    time.sleep(10)

    record_count = contract.functions.getRecordCount().call()
    latest_record_id = record_count - 1

    stored_hash, timestamp, submitter = get_record_from_chain(latest_record_id)
    print(f"\nRecord #{latest_record_id} read back from chain:")
    print(f"  Hash: {stored_hash}")
    print(f"  Timestamp: {timestamp}")
    print(f"  Submitter: {submitter}")
    print(f"\nMatches original hash: {stored_hash == test_hash}")