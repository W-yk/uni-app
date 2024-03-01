

import os
import time
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import utils  # Assuming utils.py is in the same directory for utility functions
from flask_restx  import Api, Namespace, Resource, fields


# Configure Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()
# Initialize database
db = SQLAlchemy(app)


# Define the Transaction model according to the provided schema
class Transaction(db.Model):
    transaction_hash = db.Column(db.String, primary_key=True)
    block_number = db.Column(db.Integer)
    timestamp = db.Column(db.BigInteger)
    gas_fee_in_eth = db.Column(db.Numeric)
    gas_fee_in_usd = db.Column(db.Numeric)


# Create database tables
db.create_all()

# Initialize APScheduler for background tasks
scheduler = BackgroundScheduler()
scheduler.start()


def add_txns_to_db(txns):
    """Add transactions to the database."""
    count = 0
    for txn in txns:
        # if the transaction already exists in the database, skip it
        if Transaction.query.filter_by(transaction_hash=txn["hash"]).first():
            continue
        processed_txn = utils.process_transaction(txn)
        new_txn = Transaction(**processed_txn)
        count += 1
        db.session.add(new_txn)
    db.session.commit()
    return count

def poll_live_data():
    """Function to poll live transaction data at regular intervals."""
    global last_polled_time
    print(f"Polling for live data since {last_polled_time}")
    
    now = time.time()
    
    live_transactions = utils.fetch_historical_transactions(int(last_polled_time), int(now))
    with app.app_context():
        success_count = add_txns_to_db(live_transactions)
    print(f"Added {success_count} live transactions to the database.")
    last_polled_time = now

# Initialize the last polled time
last_polled_time = time.time()

# Schedule the live data polling job to run at regular intervals (e.g., every 5 seconds)
scheduler.add_job(func=poll_live_data, trigger="interval", seconds=5)


# Initialize Swagger UI
swagger_ui_path = os.path.join(app.root_path, 'swaggerui')  # Adjust path if needed
swagger_url = '/api/docs'
api = Api(
    app,
    version='1.0',
    title='Uni API',
    doc='/api/docs',
    description='API for Uniswap transaction data'
)

# Define the namespace for grouping API endpoints
ns = Namespace('transactions', description='Transaction-related operations')



transaction_model = api.model('Transaction', {
    'transaction_hash': fields.String(required=True, description='The transaction hash'),
    'gas_fee_in_eth': fields.String(description='Gas fee in Ethereum'),
    'gas_fee_in_usd': fields.String(description='Gas fee in USD'),
    'timestamp': fields.String(description='Timestamp of the transaction'),
})


@ns.route('/transaction-fee/<transaction_hash>')
class TransactionFee(Resource):
    @ns.doc('get_transaction_fee')
    @ns.response(200, 'Transaction found',transaction_model)
    @ns.response(201, 'Transaction fetched from RPC and stored')
    @ns.response(404, 'Transaction not found')
    def get(self, transaction_hash):
        """Endpoint to retrieve the transaction fee by hash."""
        transaction = Transaction.query.filter_by(transaction_hash=transaction_hash).first()
        if transaction is None:
            # Logic to fetch from RPC and create new transaction
            transaction_data = utils.get_txn_from_rpc(transaction_hash)
            if not transaction_data:
                return {'message': 'Transaction not found'}, 404
            processed_txn = utils.process_transaction(transaction_data)
            transaction = Transaction(**processed_txn)
            db.session.add(transaction)
            db.session.commit()
            return {
                'transaction_hash': transaction.transaction_hash,
                'gas_fee_in_eth': str(transaction.gas_fee_in_eth),
                'gas_fee_in_usd': str(transaction.gas_fee_in_usd),
                'timestamp': str(transaction.timestamp),
            }, 201
        
        return {
            'transaction_hash': transaction.transaction_hash,
            'gas_fee_in_eth': str(transaction.gas_fee_in_eth),
            'gas_fee_in_usd': str(transaction.gas_fee_in_usd),
            'timestamp': str(transaction.timestamp),
        }, 200

executed_price_model = api.model('ExecutedPrice', {
    'transaction_hash': fields.String(required=True, description='The transaction hash'),
    'executed_price': fields.String(required=True, description='The executed price'),
})

@ns.route('/executed-price/<transaction_hash>')
class ExecutedPriceResource(Resource):
    @ns.doc('get_executed_price')
    @ns.response(200, 'Success', executed_price_model)
    @ns.response(404, 'Transaction not found')
    def get(self, transaction_hash):
        """Endpoint to retrieve the executed price of a transaction."""
        price = utils.get_swap_executed_price_from_txhash(transaction_hash)
        if price is None:
            return {'message': 'Get uniswap event executed price failed.'}, 404

        return {
            'transaction_hash': transaction_hash,
            'executed_price': str(price),
        }, 200
    


parser = ns.parser()
parser.add_argument('startTime', required=True, type=str, help='Start time of the transaction period')
parser.add_argument('endTime', required=True, type=str, help='End time of the transaction period')

@ns.route('/retrieve-historical-transactions')
class HistoricalTransactionsResource(Resource):
    @ns.doc('get_historical_transactions')
    @ns.expect(parser)
    @ns.response(202, 'Fetching historical transactions in progress')
    @ns.response(400, 'Invalid input data')
    def post(self):
        """Endpoint to fetch historical transactions and add them to the database."""
        data = parser.parse_args()
        start_time, end_time = data['startTime'], data['endTime']

        if not start_time or not end_time:
            return {'message': 'Both start time and end time are required.'}, 400

        def fetch_and_store_transactions():
            transactions = utils.fetch_historical_transactions(start_time, end_time)
            with app.app_context():
                success_count = add_txns_to_db(transactions)
            print(f"Added {success_count} transactions from {start_time} to {end_time} to the database.")

        print(f"Scheduling job to fetch transactions from {start_time} to {end_time}...")
        scheduler.add_job(func=fetch_and_store_transactions, trigger="date", run_date=datetime.now())

        return {'message': 'Fetching historical transactions in progress...'}, 202
    

api.add_namespace(ns)

if __name__ == '__main__':
    app.run(debug=True)