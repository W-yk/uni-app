import os
import time
import requests

# Global constants
ETHERSCAN_API_KEY = os.environ.get('ETHERSCAN_API_KEY')
UNI_CONTRACT_ADDRESS = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
USDC_CONTRACT_ADDRESS = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"
BINANCE_BASE_URL = "https://api.binance.com/api/v3"

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

def fetch_historical_transactions(start_time, end_time):
    """
    Fetch historical transactions for a defined time range from Etherscan.
    """
    transactions = []
    page, offset = 1, 1000
    start_blk, end_blk = (get_block_number_by_timestamp(t)["result"] for t in (start_time, end_time))

    while True:
        response = fetch_token_transactions(USDC_CONTRACT_ADDRESS,UNI_CONTRACT_ADDRESS, page=page,
                                            startblock=start_blk, endblock=end_blk, offset=offset)
        
        # Retry if the response contains an error or a limit message
        if "error" in response or "limit" in response['result']:
            time.sleep(1)
            continue

        transactions.extend(response["result"])
        if len(response["result"]) < offset:
            break
        page += 1
        
    return transactions

def get_eth_price_for_timestamp(timestamp):
    """
    Fetch the price of ETH at a specific timestamp from Binance.
    """
    response = fetch_klines("ETHUSDT", "1m", start_time=timestamp, end_time=timestamp + 1, limit=1)
    return response[0][4] if not "error" in response else response

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
    fee_usd = fee_eth * float(get_eth_price_for_timestamp(int(timestamp)))
    return {
        "transaction_hash": transaction_hash,
        "block_number": block_number,
        "timestamp": timestamp,
        "gas_fee_in_eth": fee_eth,
        "gas_fee_in_usd": fee_usd,
    }