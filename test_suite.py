"""
NutriGuard Test Suite
Comprehensive testing for all application components
"""

import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import application modules
from app import app, db, User, FoodItem, Donation, CropPrediction, NutritionAnalysis
from ai_services import NutritionAnalyzer, CropPredictor
from payment_service import IntaSendService, PaymentRequest, PaymentMethod
from security import TokenManager, InputValidator, CryptoUtils

class TestConfig:
    """Test configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False
    OPENAI_API_KEY = 'test-openai-key'
    INTASEND_PUBLIC_KEY = 'test-public-key'
    INTASEND_SECRET_KEY = 'test-secret-key'

class BaseTestCase(unittest.TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        """Set up test environment"""
        app.config.from_object(TestConfig)
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create tables
        db.create_all()
        
        # Create test user
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            user_type='beneficiary'
        )
        self.test_user.set_password('testpassword')
        db.session.add(self.test_user)
        db.session.commit()
        
        # Generate auth token
        self.auth_token = TokenManager.generate_token(self.test_user.id)
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def get_auth_headers(self):
        """Get authentication headers for requests"""
        return {'Authorization': f'Bearer {self.auth_token}'}

class TestAuthentication(BaseTestCase):
    """Test authentication functionality"""
    
    def test_user_registration(self):
        """Test user registration"""
        response = self.app.post('/api/register', 
            json={
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'newpassword123',
                'user_type': 'farmer'
            })
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertEqual(data['user']['username'], 'newuser')
    
    def test_user_registration_duplicate_username(self):
        """Test registration with duplicate username"""
        response = self.app.post('/api/register',
            json={
                'username': 'testuser',  # Already exists
                'email': 'another@example.com',
                'password': 'password123',
                'user_type': 'donor'
            })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Username already exists', data['error'])
    
    def test_user_login(self):
        """Test user login"""
        response = self.app.post('/api/login',
            json={
                'username': 'testuser',
                'password': 'testpassword'
            })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertEqual(data['user']['username'], 'testuser')
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.app.post('/api/login',
            json={
                'username': 'testuser',
                'password': 'wrongpassword'
            })
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('Invalid credentials', data['error'])

class TestNutritionAnalysis(BaseTestCase):
    """Test nutrition analysis functionality"""
    
    @patch('ai_services.openai.ChatCompletion.create')
    def test_nutrition_analysis(self, mock_openai):
        """Test nutrition analysis with mocked OpenAI response"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "calories": 350,
            "macronutrients": {"protein": 25, "carbs": 30, "fats": 15},
            "health_score": 8,
            "deficiencies": [],
            "recommendations": ["Great balanced meal!"]
        })
        mock_openai.return_value = mock_response
        
        response = self.app.post('/api/nutrition/analyze',
            headers=self.get_auth_headers(),
            json={'meal_description': 'Grilled chicken with vegetables'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('analysis', data)
        self.assertEqual(data['analysis']['calories'], 350)
    
    def test_nutrition_analysis_unauthorized(self):
        """Test nutrition analysis without authentication"""
        response = self.app.post('/api/nutrition/analyze',
            json={'meal_description': 'Test meal'})
        
        self.assertEqual(response.status_code, 401)

class TestCropPrediction(BaseTestCase):
    """Test crop prediction functionality"""
    
    def setUp(self):
        """Set up farmer user for crop tests"""
        super().setUp()
        # Create farmer user
        self.farmer = User(
            username='farmer1',
            email='farmer@example.com',
            user_type='farmer'
        )
        self.farmer.set_password('farmerpass')
        db.session.add(self.farmer)
        db.session.commit()
        
        self.farmer_token = TokenManager.generate_token(self.farmer.id)
    
    def get_farmer_auth_headers(self):
        """Get farmer authentication headers"""
        return {'Authorization': f'Bearer {self.farmer_token}'}
    
    @patch('ai_services.openai.ChatCompletion.create')
    def test_crop_prediction(self, mock_openai):
        """Test crop yield prediction"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "ai_yield_prediction": 5.5,
            "risk_factors": ["Weather uncertainty"],
            "recommendations": ["Use quality seeds"],
            "planting_time": "March-April",
            "confidence": 75
        })
        mock_openai.return_value = mock_response
        
        response = self.app.post('/api/crops/predict',
            headers=self.get_farmer_auth_headers(),
            json={
                'crop_type': 'maize',
                'location': 'Nairobi, Kenya',
                'soil_data': {'type': 'loamy', 'ph': 6.5},
                'weather_data': {'expected_rainfall': 800}
            })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('prediction', data)
    
    def test_crop_prediction_non_farmer(self):
        """Test crop prediction access for non-farmers"""
        response = self.app.post('/api/crops/predict',
            headers=self.get_auth_headers(),  # Regular user, not farmer
            json={
                'crop_type': 'maize',
                'location': 'Nairobi',
                'soil_data': {'type': 'clay'}
            })
        
        self.assertEqual(response.status_code, 403)

class TestPaymentIntegration(BaseTestCase):
    """Test payment integration"""
    
    def setUp(self):
        """Set up donor user for payment tests"""
        super().setUp()
        # Create donor user
        self.donor = User(
            username='donor1',
            email='donor@example.com',
            user_type='donor'
        )
        self.donor.set_password('donorpass')
        db.session.add(self.donor)
        db.session.commit()
        
        self.donor_token = TokenManager.generate_token(self.donor.id)
    
    def get_donor_auth_headers(self):
        """Get donor authentication headers"""
        return {'Authorization': f'Bearer {self.donor_token}'}
    
    @patch('payment_service.requests.Session.post')
    def test_donation_initiation(self, mock_post):
        """Test donation initiation"""
        # Mock IntaSend response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'test-transaction-id',
            'payment_url': 'https://test-payment-url.com'
        }
        mock_post.return_value = mock_response
        
        response = self.app.post('/api/donate',
            headers=self.get_donor_auth_headers(),
            json={
                'amount': 1000,
                'phone_number': '254712345678',
                'purpose': 'Support farmers'
            })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('payment_url', data)

class TestSecurity(unittest.TestCase):
    """Test security features"""
    
    def test_token_generation_and_verification(self):
        """Test JWT token generation and verification"""
        user_id = 123
        token = TokenManager.generate_token(user_id)
        
        self.assertIsNotNone(token)
        
        # Verify token
        with app.app_context():
            payload = TokenManager.verify_token(token)
            self.assertIsNotNone(payload)
            self.assertEqual(payload['user_id'], user_id)
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = CryptoUtils.hash_password(password)
        
        self.assertNotEqual(password, hashed)
        self.assertTrue(CryptoUtils.verify_password(password, hashed))
        self.assertFalse(CryptoUtils.verify_password("wrongpassword", hashed))
    
    def test_input_validation(self):
        """Test input validation functions"""
        # Email validation
        self.assertTrue(InputValidator.validate_email("test@example.com"))
        self.assertFalse(InputValidator.validate_email("invalid-email"))
        
        # Phone validation
        self.assertTrue(InputValidator.validate_phone("254712345678"))
        self.assertFalse(InputValidator.validate_phone("123"))
        
        # Password strength
        strong, msg = InputValidator.validate_password_strength("StrongPass123")
        self.assertTrue(strong)
        
        weak, msg = InputValidator.validate_password_strength("weak")
        self.assertFalse(weak)

class TestAIServices(unittest.TestCase):
    """Test AI service components"""
    
    def setUp(self):
        """Set up AI services"""
        self.nutrition_analyzer = NutritionAnalyzer("test-api-key")
        self.crop_predictor = CropPredictor("test-api-key")
    
    def test_nutrition_cache_key_generation(self):
        """Test nutrition analysis cache key generation"""
        key1 = self.nutrition_analyzer._generate_cache_key("chicken rice", {"age": 25})
        key2 = self.nutrition_analyzer._generate_cache_key("chicken rice", {"age": 25})
        key3 = self.nutrition_analyzer._generate_cache_key("chicken rice", {"age": 30})
        
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)
    
    def test_crop_suitability_calculations(self):
        """Test crop suitability calculations"""
        # Test pH suitability
        ph_score = self.crop_predictor._calculate_ph_suitability(6.5, (6.0, 7.0))
        self.assertEqual(ph_score, 1.0)  # Perfect pH
        
        ph_score_low = self.crop_predictor._calculate_ph_suitability(5.0, (6.0, 7.0))
        self.assertLess(ph_score_low, 1.0)  # Below optimal
        
        # Test rainfall suitability
        rain_score = self.crop_predictor._calculate_rainfall_suitability(800, (500, 1200))
        self.assertEqual(rain_score, 1.0)  # Within optimal range

class TestDashboard(BaseTestCase):
    """Test dashboard functionality"""
    
    def test_dashboard_access_authenticated(self):
        """Test dashboard access with authentication"""
        response = self.app.get('/api/dashboard',
            headers=self.get_auth_headers())
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
    
    def test_dashboard_access_unauthenticated(self):
        """Test dashboard access without authentication"""
        response = self.app.get('/api/dashboard')
        
        self.assertEqual(response.status_code, 401)

class TestDataModels(BaseTestCase):
    """Test database models"""
    
    def test_user_model(self):
        """Test User model functionality"""
        user = User(
            username='modeltest',
            email='model@test.com',
            user_type='farmer'
        )
        user.set_password('testpass123')
        
        db.session.add(user)
        db.session.commit()
        
        # Test password verification
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.check_password('wrongpass'))
        
        # Test user retrieval
        retrieved_user = User.query.filter_by(username='modeltest').first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, 'model@test.com')
    
    def test_food_item_model(self):
        """Test FoodItem model"""
        food_item = FoodItem(
            name='Test Maize',
            category='Cereals',
            nutritional_info={'calories': 365, 'protein': 9.4},
            price_per_kg=50.00
        )
        
        db.session.add(food_item)
        db.session.commit()
        
        retrieved_item = FoodItem.query.filter_by(name='Test Maize').first()
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.category, 'Cereals')

class TestErrorHandling(BaseTestCase):
    """Test error handling"""
    
    def test_404_error(self):
        """Test 404 error handling"""
        response = self.app.get('/api/nonexistent')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_invalid_json(self):
        """Test invalid JSON handling"""
        response = self.app.post('/api/register',
            data='invalid json',
            content_type='application/json')
        
        self.assertEqual(response.status_code, 400)

class TestRateLimiting(BaseTestCase):
    """Test rate limiting functionality"""
    
    def test_login_rate_limiting(self):
        """Test rate limiting on login endpoint"""
        # This would require Redis setup for full testing
        # For now, just test that the endpoint exists
        response = self.app.post('/api/login',
            json={'username': 'test', 'password': 'test'})
        
        # Should get 401 for invalid credentials, not rate limit error
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestAuthentication,
        TestNutritionAnalysis,
        TestCropPrediction,
        TestPaymentIntegration,
        TestSecurity,
        TestAIServices,
        TestDashboard,
        TestDataModels,
        TestErrorHandling,
        TestRateLimiting
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")