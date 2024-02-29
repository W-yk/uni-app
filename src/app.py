from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import time

import utils  # Assuming utils.py is in the same directory for utility functions

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

@app.route('/transaction-fee/<transaction_hash>', methods=['GET'])
def get_transaction_fee(transaction_hash):
    """Endpoint to retrieve the transaction fee by hash."""
    transaction = Transaction.query.filter_by(transaction_hash=transaction_hash).first()
    if transaction is None:
        return jsonify({'error': 'Transaction not recorded. Submit get-historical-transactions request first.'}), 404
    return jsonify({
        'transaction_hash': transaction.transaction_hash,
        'gas_fee_in_eth': str(transaction.gas_fee_in_eth),
        'gas_fee_in_usd': str(transaction.gas_fee_in_usd),
        'timestamp': str(transaction.timestamp),
    })


@app.route('/get-historical-transactions', methods=['POST'])
def get_historical_transactions():
    """Endpoint to fetch historical transactions and add them to the database."""
    data = request.get_json()
    start_time, end_time = data['startTime'], data['endTime']

    def fetch_and_store_transactions():
        transactions = utils.fetch_historical_transactions(start_time, end_time)

        with app.app_context():
            success_count = add_txns_to_db(transactions)
        print(f"Added {success_count} transactions from {start_time} to {end_time} to the database.")

    print(f"Scheduling job to fetch transactions from {start_time} to {end_time}...")
    scheduler.add_job(func=fetch_and_store_transactions, trigger="date", run_date=datetime.now())
    return jsonify({'message': 'Fetching historical transactions in progress...'}), 202


def poll_live_data():
    """Function to poll live transaction data at regular intervals."""
    global last_polled_time
    print("Polling for live data...")
    
    now = time.time()
    
    live_transactions = utils.fetch_historical_transactions(int(last_polled_time), int(now))
    with app.app_context():
        success_count = add_txns_to_db(live_transactions)
    print(f"Added {success_count} live transactions to the database.")
    last_polled_time = now

# Initialize the last polled time
last_polled_time = time.time()

# Schedule the live data polling job to run at regular intervals (e.g., every 1 minute)
scheduler.add_job(func=poll_live_data, trigger="interval", seconds=1)

if __name__ == '__main__':
    app.run(debug=True)