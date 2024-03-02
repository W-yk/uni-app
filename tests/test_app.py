import unittest
import requests
import time

from app import app,scheduler
import utils

class TestUniAPI(unittest.TestCase):

    def setUp(self):
        # Create a new test client for each test instance
        self.client = app.test_client()

    def tearDown(self):
        # Close the test client after each test
        self.client = None

    # Testing the '/transaction-fee/<transaction_hash>' endpoint
    def test_get_transaction_fee(self):
        transaction_hash = '0xcfc7478431fe9c2ca93c39b4d88b945b5298f229d6e28a93d5d6c71cdb1daa43'
        response = self.client.get(f"/transactions/transaction-fee/{transaction_hash}")
        self.assertIn(response.status_code, [200,201])
        data = response.json
        self.assertIn('transaction_hash', data)
        self.assertIn('gas_fee_in_eth', data)
        self.assertIn('gas_fee_in_usd', data)
        self.assertIn('timestamp', data)

    # Testing the '/executed-price/<transaction_hash>' endpoint (similar structure)
    def test_get_transaction_fee_not_found(self):
        transaction_hash = '0xcfc7478431fe9c2ca93c39b4d88b945b5298f229d6e28a93d5d6c71cdb1daa43'
        response = self.client.get(f"/transactions/executed-price/{transaction_hash}")
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('transaction_hash', data)
        self.assertIn('executed_price', data)

    # Testing the '/retrieve-historical-transactions' endpoint
    def test_retrieve_historical_transactions(self):
        start_time = '1661953600'  # Example timestamp as a string
        end_time = '1661953600'
        response = self.client.post(
            "/transactions/retrieve-historical-transactions",
            json={'startTime': start_time, 'endTime': end_time}
        )
        self.assertEqual(response.status_code, 202)

if __name__ == '__main__':
    unittest.main()