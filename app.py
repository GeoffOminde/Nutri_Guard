#!/usr/bin/env python3
"""
NutriGuard - SDG 2 Zero Hunger Application
A comprehensive food security platform with AI-powered insights
"""

import os
import json
import uuid
import jwt
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Flask-Limiter (v3+) – init with key_func, then call init_app(app)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Make PyMySQL behave like MySQLdb so existing "mysql://..." URIs work on Windows
import pymysql
pymysql.install_as_MySQLdb()

# Optional external services
import requests
import openai

# -----------------------------------------------------------------------------
# App & Config
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Keep your original mysql:// URI – install_as_MySQLdb() makes it work on Windows
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'mysql+pymysql://root:password@localhost/nutriguard'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -----------------------------------------------------------------------------
# Extensions
# -----------------------------------------------------------------------------
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Configure Limiter; set LIMITER_STORAGE_URI env (e.g., redis://localhost:6379) for prod
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.environ.get("LIMITER_STORAGE_URI")  # None = in-memory (dev)
)
limiter.init_app(app)

# -----------------------------------------------------------------------------
# Logging & External Keys
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = os.environ.get('OPENAI_API_KEY')

INTASEND_PUBLIC_KEY = os.environ.get('INTASEND_PUBLIC_KEY')
INTASEND_SECRET_KEY = os.environ.get('INTASEND_SECRET_KEY')
INTASEND_BASE_URL = "https://sandbox.intasend.com/api/v1/"

# -----------------------------------------------------------------------------
# Database Models
# -----------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum('farmer', 'donor', 'beneficiary', 'admin'), default='beneficiary')
    location = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class FoodItem(db.Model):
    __tablename__ = 'food_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    nutritional_info = db.Column(db.JSON)
    price_per_kg = db.Column(db.Numeric(10, 2))
    availability = db.Column(db.Integer, default=0)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Donation(db.Model):
    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='KES')
    purpose = db.Column(db.String(255))
    status = db.Column(db.Enum('pending', 'completed', 'failed'), default='pending')
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CropPrediction(db.Model):
    __tablename__ = 'crop_predictions'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    soil_data = db.Column(db.JSON)
    weather_data = db.Column(db.JSON)
    ai_prediction = db.Column(db.JSON)
    confidence_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NutritionAnalysis(db.Model):
    __tablename__ = 'nutrition_analysis'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meal_description = db.Column(db.Text, nullable=False)
    nutrition_breakdown = db.Column(db.JSON)
    recommendations = db.Column(db.JSON)
    deficiency_alerts = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------------------------------------------------------------
# Security Decorators
# -----------------------------------------------------------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except Exception:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.user_type != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

# -----------------------------------------------------------------------------
# AI Service
# -----------------------------------------------------------------------------
class AIService:
    @staticmethod
    def analyze_nutrition(meal_description):
        """Use OpenAI to analyze nutritional content of meals"""
        try:
            prompt = f"""
            Analyze the nutritional content of this meal: "{meal_description}"
            Provide a detailed breakdown including:
            1. Estimated calories
            2. Macronutrients (protein, carbs, fats)
            3. Key vitamins and minerals
            4. Nutritional deficiencies or concerns
            5. Recommendations for improvement
            Format your response as JSON with the following structure:
            {{
                "calories": 0,
                "macronutrients": {{"protein": "0 g", "carbs": "0 g", "fats": "0 g"}},
                "vitamins": {{"vitamin_c": "0 mg", "iron": "0 mg"}},
                "deficiencies": [],
                "recommendations": [],
                "health_score": 5
            }}
            """
            # Legacy ChatCompletion; update if you move to the new API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"AI nutrition analysis failed: {e}")
            return {"error": "Analysis failed", "health_score": 5}

    @staticmethod
    def predict_crop_yield(crop_type, location, soil_data, weather_data):
        """Use AI to predict crop yields"""
        try:
            prompt = f"""
            As an agricultural AI expert, predict the crop yield for:
            - Crop: {crop_type}
            - Location: {location}
            - Soil data: {soil_data}
            - Weather data: {weather_data}
            Provide predictions including:
            1. Expected yield per hectare
            2. Best planting time
            3. Risk factors
            4. Optimization recommendations
            5. Confidence score (0-100)
            Format as JSON:
            {{
                "yield_prediction": "0 tons/hectare",
                "planting_time": "Month/season",
                "risk_factors": [],
                "recommendations": [],
                "confidence": 0
            }}
            """
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.2
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"AI crop prediction failed: {e}")
            return {"error": "Prediction failed", "confidence": 0}

# -----------------------------------------------------------------------------
# Payment Service
# -----------------------------------------------------------------------------
class PaymentService:
    @staticmethod
    def initiate_payment(amount, currency, phone_number, email, purpose):
        """Initiate IntaSend payment"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-IntaSend-Public-API-Key': INTASEND_PUBLIC_KEY,
                'X-IntaSend-Secret-API-Key': INTASEND_SECRET_KEY
            }
            payload = {
                'amount': float(amount),
                'currency': currency,
                'phone_number': phone_number,
                'email': email,
                'api_ref': str(uuid.uuid4()),
                'narrative': purpose
            }
            response = requests.post(
                f"{INTASEND_BASE_URL}checkout/",
                headers=headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Payment initiation failed: {response.text}")
                return {"error": "Payment initiation failed"}
        except Exception as e:
            logger.error(f"Payment service error: {e}")
            return {"error": "Payment service unavailable"}

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    try:
        data = request.get_json() or {}
        required_fields = ['username', 'email', 'password', 'user_type']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400

        user = User(
            username=data['username'],
            email=data['email'],
            user_type=data['user_type'],
            location=data.get('location', ''),
            phone=data.get('phone', '')
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type
            }
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500


@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    try:
        data = request.get_json() or {}
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password required'}), 400

        user = User.query.filter_by(username=data['username']).first()
        if user and user.check_password(data['password']):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(days=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'user_type': user.user_type
                }
            }), 200

        return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@app.route('/api/nutrition/analyze', methods=['POST'])
@token_required
def analyze_nutrition(current_user):
    try:
        data = request.get_json() or {}
        meal_description = data.get('meal_description')
        if not meal_description:
            return jsonify({'error': 'Meal description required'}), 400

        analysis = AIService.analyze_nutrition(meal_description)

        nutrition_analysis = NutritionAnalysis(
            user_id=current_user.id,
            meal_description=meal_description,
            nutrition_breakdown=analysis.get('macronutrients', {}),
            recommendations=analysis.get('recommendations', []),
            deficiency_alerts=analysis.get('deficiencies', [])
        )
        db.session.add(nutrition_analysis)
        db.session.commit()

        return jsonify({'analysis': analysis, 'id': nutrition_analysis.id}), 200

    except Exception as e:
        logger.error(f"Nutrition analysis error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Analysis failed'}), 500


@app.route('/api/crops/predict', methods=['POST'])
@token_required
def predict_crop_yield(current_user):
    try:
        if current_user.user_type != 'farmer':
            return jsonify({'error': 'Farmer access required'}), 403

        data = request.get_json() or {}
        required_fields = ['crop_type', 'location', 'soil_data']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        prediction = AIService.predict_crop_yield(
            data['crop_type'],
            data['location'],
            data['soil_data'],
            data.get('weather_data', {})
        )

        crop_prediction = CropPrediction(
            farmer_id=current_user.id,
            crop_type=data['crop_type'],
            location=data['location'],
            soil_data=data['soil_data'],
            weather_data=data.get('weather_data', {}),
            ai_prediction=prediction,
            confidence_score=(prediction.get('confidence', 0) or 0) / 100.0
        )
        db.session.add(crop_prediction)
        db.session.commit()

        return jsonify({'prediction': prediction, 'id': crop_prediction.id}), 200

    except Exception as e:
        logger.error(f"Crop prediction error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Prediction failed'}), 500


@app.route('/api/donate', methods=['POST'])
@token_required
def initiate_donation(current_user):
    try:
        data = request.get_json() or {}
        required_fields = ['amount', 'phone_number', 'purpose']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        payment_response = PaymentService.initiate_payment(
            data['amount'],
            data.get('currency', 'KES'),
            data['phone_number'],
            current_user.email,
            data['purpose']
        )

        if 'error' not in payment_response:
            donation = Donation(
                donor_id=current_user.id,
                amount=data['amount'],
                currency=data.get('currency', 'KES'),
                purpose=data['purpose'],
                transaction_id=payment_response.get('id')
            )
            db.session.add(donation)
            db.session.commit()

            return jsonify({
                'message': 'Donation initiated successfully',
                'payment_url': payment_response.get('payment_url'),
                'donation_id': donation.id
            }), 200

        return jsonify({'error': payment_response['error']}), 400

    except Exception as e:
        logger.error(f"Donation error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Donation failed'}), 500


@app.route('/api/dashboard')
@token_required
def dashboard(current_user):
    try:
        dashboard_data = {
            'user': {
                'username': current_user.username,
                'user_type': current_user.user_type,
                'location': current_user.location
            }
        }

        if current_user.user_type == 'farmer':
            predictions = (CropPrediction.query
                           .filter_by(farmer_id=current_user.id)
                           .order_by(CropPrediction.created_at.desc())
                           .limit(5).all())
            dashboard_data['recent_predictions'] = [
                {
                    'crop_type': p.crop_type,
                    'confidence': p.confidence_score,
                    'created_at': p.created_at.isoformat()
                } for p in predictions
            ]

        elif current_user.user_type == 'donor':
            donations = Donation.query.filter_by(donor_id=current_user.id).all()
            total_donated = sum(
                (d.amount for d in donations if d.status == 'completed'),
                start=0
            )
            # total_donated may be Decimal; cast to float for JSON
            dashboard_data['total_donated'] = float(total_donated)
            dashboard_data['donation_count'] = len(donations)

        else:  # beneficiary
            analyses = (NutritionAnalysis.query
                        .filter_by(user_id=current_user.id)
                        .order_by(NutritionAnalysis.created_at.desc())
                        .limit(5).all())
            dashboard_data['recent_analyses'] = [
                {
                    'meal_description': a.meal_description,
                    'created_at': a.created_at.isoformat()
                } for a in analyses
            ]

        return jsonify(dashboard_data), 200

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({'error': 'Dashboard data unavailable'}), 500

# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# -----------------------------------------------------------------------------
# DB Init (wrapped in app context)
# -----------------------------------------------------------------------------
def init_db():
    """Initialize database tables"""
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    # ✅ FIX: Ensure DB operations run inside an application context
    with app.app_context():
        init_db()

    # Disable Flask reloader to prevent double initialization
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

