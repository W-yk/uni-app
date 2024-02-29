from src import db

class Transaction(db.Model):
    transaction_hash = db.Column(db.String, primary_key=True)
    block_number = db.Column(db.Integer)
    timestamp = db.Column(db.BigInteger)
    gas_fee_in_eth = db.Column(db.Numeric)
    gas_fee_in_usd = db.Column(db.Numeric)