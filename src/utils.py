import os
import time
import requests
from web3 import Web3
from eth_abi import decode

# Global constants
ETHERSCAN_API_KEY = os.environ.get('ETHERSCAN_API_KEY')
UNI_CONTRACT_ADDRESS = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
USDC_CONTRACT_ADDRESS = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"
BINANCE_BASE_URL = "https://api.binance.com/api/v3"
ALCHEMY_RPC_URL = f"https://eth-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_API_KEY')}"

w3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))

def fetch_token_transactions(contract_address,address, page=1, offset=100,
                             startblock=0, endblock=27025780, sort='asc'):
    """
    Fetch token transactions for a specified contract address from Etherscan.
    """
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": contract_address,
        "address": address,
        "page": page,
        "offset": offset,
        "startblock": startblock,
        "endblock": endblock,
        "sort": sort,
        "apikey": ETHERSCAN_API_KEY,
    }
    response = requests.get(ETHERSCAN_BASE_URL, params=params)
    return response.json() if response.ok else {"error": "Failed to fetch data from Etherscan."}

def fetch_klines(symbol, interval, start_time=None, end_time=None, limit=500):
    """
    Fetch candlestick/kline data for a symbol from Binance.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": limit,
    }
    BINANCE_BASE_URL = "https://api.binance.com/api/v3"
    response = requests.get(BINANCE_BASE_URL+"/klines", params=params)
    return response.json() if response.ok else {"error": "Failed to fetch data from Binance."}

def get_block_number_by_timestamp(timestamp):
    """
    Fetch the block number closest to a given timestamp from Etherscan.
    """
    params = {
        "module": "block",
        "action": "getblocknobytime",
        "timestamp": timestamp,
        "closest": "before",
        "apikey": ETHERSCAN_API_KEY,
    }
    response = requests.get(ETHERSCAN_BASE_URL, params=params)
    return response.json() if response.ok else {"error": "Failed to fetch data from Etherscan."}

def fetch_historical_transactions(start_time, end_time, max_retries=5):
    """
    Fetch historical transactions for a defined time range from Etherscan.
    """
    transactions = []
    page, offset = 1, 1000
    start_blk, end_blk = (get_block_number_by_timestamp(t)["result"] for t in (start_time, end_time))
    retries = 0  # Initialize retries counter

    while True:
        response = fetch_token_transactions(USDC_CONTRACT_ADDRESS, UNI_CONTRACT_ADDRESS, page=page,
                                            startblock=start_blk, endblock=end_blk, offset=offset)

        # Check for the existence of an error or a limit message in the response
        if not response or response['message'] not in  ["OK",'No transactions found']:
            if retries < max_retries:
                time.sleep(1)  # wait before retrying
                retries += 1  # increment retries counter
                continue
            else:
                print("Max retries reached. Exiting.")
                print("error response: ",response)
                break 

        transactions.extend(response["result"])
        # Check if the last page of transactions has been reached
        if len(response["result"]) < offset:
            break  # Exit the loop if fewer transactions than the offset are returned
        page += 1
        retries = 0  # Reset retries counter after a successful fetch
        
    return transactions
def get_eth_price_for_timestamp(timestamp):
    """
    Fetch the price of ETH at a specific timestamp from Binance.
    """
    unix_timestamp = int(timestamp * 1000)
    response = fetch_klines("ETHUSDT", "1s", start_time=unix_timestamp-1000, end_time=unix_timestamp, limit=2)
    return float(response[-1][4]) if response else 0

def calculate_transaction_fee_eth(gas_used, gas_price):
    """
    Calculate the transaction fee in ETH.
    """
    return gas_used * (gas_price / 1e18)

def process_transaction(transaction):
    """
    Process transaction data from Etherscan API and calculates the transaction fee in both ETH and USD.
    """
    transaction_hash = transaction["hash"]
    block_number = transaction["blockNumber"]
    timestamp = transaction["timeStamp"]
    gas_used = int(transaction["gasUsed"])
    gas_price = int(transaction["gasPrice"])

    fee_eth = calculate_transaction_fee_eth(gas_used, gas_price)
    price = float(get_eth_price_for_timestamp(int(timestamp)))
    fee_usd = fee_eth * price
    return {
        "transaction_hash": transaction_hash,
        "block_number": block_number,
        "timestamp": timestamp,
        "gas_fee_in_eth": fee_eth,
        "gas_fee_in_usd": fee_usd,
    }


def get_txn_from_rpc(txn_hash):
    """
    Fetch transaction data from an Ethereum node using web3.py.
    """
    try:
        txn = w3.eth.get_transaction(txn_hash)
    except Exception as e:
        print(f"Error fetching transaction data: {e}")
        return None
    txn_receipt  = w3.eth.wait_for_transaction_receipt(txn_hash, timeout=1)
    block = w3.eth.get_block(txn_receipt['blockNumber'])
    txn = dict(**txn_receipt)
    txn['timeStamp']= block['timestamp']
    txn['hash']=txn_receipt['transactionHash'].hex()
    txn['gasPrice']=txn_receipt['effectiveGasPrice']
    
    return txn

def get_swap_executed_price_from_txhash(txhash):
    """
    Fetch the transaction receipt and calculate executed price.
    """
    uniswap_v2_swap_signature = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
    uniswap_v2_swap_input_types = [ "int256", "int256", "uint160", "uint128", "int24"]

    # Retrieve the transaction receipt
    try:
        receipt = w3.eth.wait_for_transaction_receipt(txhash, timeout=1)
    except Exception as e:
        print(f"Error fetching transaction receipt: {e}")
        return None
    logs = receipt.logs

    # Loop through the logs
    for log in logs:
        # Check if the event signature matches the Uniswap V2 swap event
        if log.topics[0].hex() == uniswap_v2_swap_signature and log.address.lower()==UNI_CONTRACT_ADDRESS:
            # Decode the event data
            usdc_amount_change, weth_amount_change, _, _, _ = decode(uniswap_v2_swap_input_types, bytes.fromhex(log.data.hex()[2:]))
            # Calculate the price 6 decimals for USDC and 18 decimals for WETH
            price = abs(usdc_amount_change / 1e6 / (weth_amount_change / 1e18))
            return price

    # If no matching event is found, return None
    return None
