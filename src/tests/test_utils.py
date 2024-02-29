import unittest
from unittest.mock import patch
import sys
import time
# Assuming the script is named `crypto_api.py`
from src.utils import (
    UNI_CONTRACT_ADDRESS,
    USDC_CONTRACT_ADDRESS,
    fetch_token_transactions,
    fetch_klines,
    get_block_number_by_timestamp,
    fetch_historical_transactions,
    get_eth_price_for_timestamp,
    calculate_transaction_fee_eth,
    process_transaction,
)

class TestCryptoAPI(unittest.TestCase):

    def test_fetch_token_transactions(self):
        res = fetch_token_transactions(USDC_CONTRACT_ADDRESS,UNI_CONTRACT_ADDRESS,1,10,0,999999999)
        self.assertGreater(len(res['result'], 0))

    def test_fetch_historical_transactions(self):
        res = fetch_historical_transactions(1709197799, 1809197799)
        self.assertGreater(len(res, 0))
        
    def test_fetch_token_transactions(self):
        res = fetch_token_transactions(USDC_CONTRACT_ADDRESS,UNI_CONTRACT_ADDRESS,1,10,0,999999999)
        self.assertGreater(len(res, 0))
        
    def test_fetch_klines(self):
        res = fetch_klines('ETHUSDT',"1s",0,99999999999999999)
        self.assertGreater(len(res), 0)

    def test_calculate_transaction_fee_eth(self):
        gas_used = 50000
        gas_price = 1000000000  # 1 Gwei
        expected_fee_eth = 0.00005  # 50,000 gas * 1 Gwei / 1e18 to convert wei to eth
        self.assertAlmostEqual(calculate_transaction_fee_eth(gas_used, gas_price), expected_fee_eth)

    @patch('crypto_api.get_eth_price_for_timestamp')
    @patch('crypto_api.calculate_transaction_fee_eth')
    def test_process_transaction(self, mock_calculate_fee, mock_get_price):
        mock_calculate_fee.return_value = 0.01  # mock fee in ETH
        mock_get_price.return_value = 2000  # mock ETH price in USD
        transaction = {
            "hash": "0xhash",
            "blockNumber": "1234",
            "timeStamp": "1609459200",  # mock timestamp
            "gasUsed": "100000",
            "gasPrice": "1000000000",
        }
        expected_result = {
            "transaction_hash": "0xhash",
            "block_number": "1234",
            "timestamp": "1609459200",
            "gas_fee_in_eth": 0.01,
            "gas_fee_in_usd": 20,
        }
        result = process_transaction(transaction)
        self.assertEqual(result, expected_result)