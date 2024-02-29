# from flask import Flask
# from app.routes import bp as api_bp
# from flask_sqlalchemy import SQLAlchemy
# from flask_apscheduler import APScheduler

# from .services import schedule_tasks

# app = Flask(__name__)

# # ... other app configuration ...

# # Initialize APScheduler with your app
# scheduler = APScheduler(app=app)

# # Call schedule_tasks at initialization
# schedule_tasks()

# db = SQLAlchemy()

# def create_app():
#     app = Flask(__name__)
#     app.register_blueprint(api_bp)
#     app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
#     db.init_app(app)

#     with app.app_context():
#         db.create_all()

#     return app


# from flask import Blueprint, request, jsonify
# from .services import record_historical_transactions, get_transaction_fee
# from .models import db

# bp = Blueprint('api', __name__, url_prefix='/api')

# @bp.route('/record-historical', methods=['POST'])
# def record_historical():
#     data = request.get_json()
#     start_time = data.get('start_time')
#     end_time = data.get('end_time')
    
#     # Validate input
#     if not start_time or not end_time:
#         return jsonify({'error': 'Invalid request, start_time and end_time are required.'}), 400

#     try:
#         # Attempt to record the historical transactions based on the provided timestamps
#         record_historical_transactions(start_time, end_time)
#         return jsonify({'status': 'Batch job initiated'}), 202
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @bp.route('/transaction-fee/<transaction_hash>', methods=['GET'])
# def transaction_fee(transaction_hash):
#     # Validate hash input
#     if not transaction_hash:
#         return jsonify({'error': 'Invalid request, transaction_hash is required.'}), 400

#     try:
#         # Retrieve the transaction fee details for the specified transaction hash
#         fee_details = get_transaction_fee(transaction_hash)
#         if fee_details:
#             return jsonify(fee_details), 200
#         else:
#             return jsonify({'error': 'Transaction not found.'}), 404
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500