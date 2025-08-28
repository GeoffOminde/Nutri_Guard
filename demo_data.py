"""
NutriGuard Demo Data Generator
Creates sample data for demonstration and testing purposes
"""

import os
import sys
from datetime import datetime, timedelta
import json
import random

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, User, FoodItem, Donation, CropPrediction, NutritionAnalysis

class DemoDataGenerator:
    """Generate realistic demo data for NutriGuard"""
    
    def __init__(self):
        self.app = app
        self.sample_foods = [
            {
                'name': 'Organic Maize',
                'category': 'Cereals',
                'nutritional_info': {
                    'calories': 365,
                    'protein': 9.4,
                    'carbs': 74.3,
                    'fiber': 7.3,
                    'fat': 4.7
                },
                'price_per_kg': 55.00
            },
            {
                'name': 'Brown Rice',
                'category': 'Cereals',
                'nutritional_info': {
                    'calories': 370,
                    'protein': 7.9,
                    'carbs': 77.2,
                    'fiber': 3.5,
                    'fat': 2.9
                },
                'price_per_kg': 125.00
            },
            {
                'name': 'Red Kidney Beans',
                'category': 'Legumes',
                'nutritional_info': {
                    'calories': 333,
                    'protein': 23.6,
                    'carbs': 60.0,
                    'fiber': 25.0,
                    'fat': 0.8
                },
                'price_per_kg': 180.00
            },
            {
                'name': 'Sweet Potatoes',
                'category': 'Tubers',
                'nutritional_info': {
                    'calories': 86,
                    'protein': 1.6,
                    'carbs': 20.1,
                    'fiber': 3.0,
                    'fat': 0.1
                },
                'price_per_kg': 75.00
            },
            {
                'name': 'Fresh Kale',
                'category': 'Vegetables',
                'nutritional_info': {
                    'calories': 49,
                    'protein': 4.3,
                    'carbs': 8.8,
                    'fiber': 3.6,
                    'fat': 0.9
                },
                'price_per_kg': 120.00
            }
        ]
        
        self.sample_meals = [
            "Grilled chicken breast with steamed broccoli and brown rice",
            "Lentil curry with whole wheat chapati and mixed vegetables",
            "Baked salmon with quinoa and roasted sweet potatoes",
            "Vegetable stir-fry with tofu and brown rice",
            "Bean and vegetable soup with whole grain bread",
            "Grilled tilapia with sukuma wiki and ugali",
            "Chicken and vegetable stew with sweet potatoes",
            "Mixed bean salad with avocado and whole grain crackers"
        ]
        
        self.sample_locations = [
            "Nairobi, Kenya",
            "Mombasa, Kenya",
            "Kisumu, Kenya",
            "Nakuru, Kenya",
            "Eldoret, Kenya",
            "Meru, Kenya",
            "Thika, Kenya",
            "Nyeri, Kenya"
        ]
    
    def generate_all_demo_data(self):
        """Generate complete demo dataset"""
        with self.app.app_context():
            print("🌱 Generating NutriGuard demo data...")
            
            # Clear existing data
            self._clear_existing_data()
            
            # Generate users
            users = self._generate_users()
            
            # Generate food items
            self._generate_food_items(users['farmers'])
            
            # Generate nutrition analyses
            self._generate_nutrition_analyses(users['beneficiaries'])
            
            # Generate crop predictions
            self._generate_crop_predictions(users['farmers'])
            
            # Generate donations
            self._generate_donations(users['donors'])
            
            db.session.commit()
            print("✅ Demo data generation completed!")
            self._print_summary()
    
    def _clear_existing_data(self):
        """Clear existing demo data"""
        print("🧹 Clearing existing data...")
        
        # Delete in reverse order of dependencies
        NutritionAnalysis.query.delete()
        CropPrediction.query.delete()
        Donation.query.delete()
        FoodItem.query.delete()
        
        # Keep admin user, delete others
        User.query.filter(User.username != 'admin').delete()
        
        db.session.commit()
    
    def _generate_users(self):
        """Generate sample users"""
        print("👥 Generating users...")
        
        users = {
            'farmers': [],
            'donors': [],
            'beneficiaries': [],
            'admins': []
        }
        
        # Generate farmers
        farmer_names = [
            'John Kamau', 'Mary Wanjiku', 'Peter Ochieng', 'Grace Akinyi',
            'Samuel Kipchoge', 'Ruth Nyambura', 'David Mwangi', 'Sarah Chebet'
        ]
        
        for i, name in enumerate(farmer_names):
            username = f"farmer{i+1}"
            email = f"{username}@nutriguard.demo"
            location = random.choice(self.sample_locations)
            
            farmer = User(
                username=username,
                email=email,
                user_type='farmer',
                location=location,
                phone=f"25471{random.randint(1000000, 9999999)}"
            )
            farmer.set_password('demo123')
            
            db.session.add(farmer)
            users['farmers'].append(farmer)
        
        # Generate donors
        donor_names = [
            'Alice Johnson', 'Michael Brown', 'Emma Wilson', 'James Davis',
            'Olivia Taylor', 'William Anderson', 'Sophia Martinez', 'Benjamin Lee'
        ]
        
        for i, name in enumerate(donor_names):
            username = f"donor{i+1}"
            email = f"{username}@nutriguard.demo"
            
            donor = User(
                username=username,
                email=email,
                user_type='donor',
                location="Global",
                phone=f"25472{random.randint(1000000, 9999999)}"
            )
            donor.set_password('demo123')
            
            db.session.add(donor)
            users['donors'].append(donor)
        
        # Generate beneficiaries
        beneficiary_names = [
            'Jane Wanjiru', 'Paul Otieno', 'Lucy Moraa', 'Joseph Kiprotich',
            'Agnes Wambui', 'Francis Omondi', 'Catherine Njeri', 'Daniel Kipsang'
        ]
        
        for i, name in enumerate(beneficiary_names):
            username = f"beneficiary{i+1}"
            email = f"{username}@nutriguard.demo"
            location = random.choice(self.sample_locations)
            
            beneficiary = User(
                username=username,
                email=email,
                user_type='beneficiary',
                location=location,
                phone=f"25473{random.randint(1000000, 9999999)}"
            )
            beneficiary.set_password('demo123')
            
            db.session.add(beneficiary)
            users['beneficiaries'].append(beneficiary)
        
        db.session.flush()  # Get user IDs
        return users
    
    def _generate_food_items(self, farmers):
        """Generate food items from farmers"""
        print("🌾 Generating food items...")
        
        for farmer in farmers:
            # Each farmer has 2-4 food items
            num_items = random.randint(2, 4)
            selected_foods = random.sample(self.sample_foods, num_items)
            
            for food_data in selected_foods:
                food_item = FoodItem(
                    name=food_data['name'],
                    category=food_data['category'],
                    nutritional_info=food_data['nutritional_info'],
                    price_per_kg=food_data['price_per_kg'] + random.uniform(-10, 10),
                    availability=random.randint(50, 500),
                    farmer_id=farmer.id
                )
                
                db.session.add(food_item)
    
    def _generate_nutrition_analyses(self, beneficiaries):
        """Generate nutrition analyses"""
        print("🍽️ Generating nutrition analyses...")
        
        for beneficiary in beneficiaries:
            # Each beneficiary has 3-8 nutrition analyses
            num_analyses = random.randint(3, 8)
            
            for _ in range(num_analyses):
                meal = random.choice(self.sample_meals)
                
                # Generate realistic nutrition analysis
                analysis = self._generate_mock_nutrition_analysis(meal)
                
                nutrition_analysis = NutritionAnalysis(
                    user_id=beneficiary.id,
                    meal_description=meal,
                    nutrition_breakdown=analysis['macronutrients'],
                    recommendations=analysis['recommendations'],
                    deficiency_alerts=analysis['deficiencies'],
                    created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                
                db.session.add(nutrition_analysis)
    
    def _generate_mock_nutrition_analysis(self, meal):
        """Generate mock nutrition analysis data"""
        # Simple keyword-based analysis for demo
        calories = random.randint(300, 800)
        
        if 'chicken' in meal.lower() or 'salmon' in meal.lower() or 'tilapia' in meal.lower():
            protein = random.randint(25, 40)
        elif 'bean' in meal.lower() or 'lentil' in meal.lower():
            protein = random.randint(15, 25)
        else:
            protein = random.randint(8, 20)
        
        carbs = random.randint(30, 60)
        fats = random.randint(5, 25)
        
        recommendations = [
            "Great source of protein!",
            "Consider adding more vegetables",
            "Good balance of nutrients",
            "Try to include more fiber",
            "Excellent meal choice"
        ]
        
        deficiencies = []
        if protein < 20:
            deficiencies.append("Low protein content")
        if 'vegetable' not in meal.lower():
            deficiencies.append("Consider adding more vegetables")
        
        return {
            'calories': calories,
            'macronutrients': {
                'protein': protein,
                'carbohydrates': carbs,
                'fats': fats
            },
            'recommendations': random.sample(recommendations, random.randint(2, 4)),
            'deficiencies': deficiencies
        }
    
    def _generate_crop_predictions(self, farmers):
        """Generate crop predictions"""
        print("🌱 Generating crop predictions...")
        
        crops = ['maize', 'rice', 'beans', 'sweet_potato', 'wheat']
        
        for farmer in farmers:
            # Each farmer has 2-5 crop predictions
            num_predictions = random.randint(2, 5)
            
            for _ in range(num_predictions):
                crop = random.choice(crops)
                
                # Generate realistic prediction data
                prediction_data = self._generate_mock_crop_prediction(crop)
                
                crop_prediction = CropPrediction(
                    farmer_id=farmer.id,
                    crop_type=crop,
                    location=farmer.location,
                    soil_data={
                        'type': random.choice(['clay', 'sandy', 'loamy']),
                        'ph': round(random.uniform(5.5, 7.5), 1),
                        'organic_matter': random.choice(['low', 'medium', 'high'])
                    },
                    weather_data={
                        'expected_rainfall': random.randint(400, 1200),
                        'temperature_range': f"{random.randint(18, 25)}-{random.randint(28, 35)}°C"
                    },
                    ai_prediction=prediction_data,
                    confidence_score=prediction_data['confidence'] / 100,
                    created_at=datetime.now() - timedelta(days=random.randint(1, 60))
                )
                
                db.session.add(crop_prediction)
    
    def _generate_mock_crop_prediction(self, crop):
        """Generate mock crop prediction data"""
        crop_yields = {
            'maize': (3, 7),
            'rice': (4, 9),
            'beans': (1, 3),
            'sweet_potato': (10, 25),
            'wheat': (2, 5)
        }
        
        min_yield, max_yield = crop_yields.get(crop, (2, 6))
        predicted_yield = round(random.uniform(min_yield, max_yield), 1)
        
        confidence = random.randint(65, 95)
        
        risk_factors = [
            "Weather uncertainty",
            "Pest infestation risk",
            "Market price volatility",
            "Water availability",
            "Soil nutrient depletion"
        ]
        
        recommendations = [
            "Use certified seeds",
            "Apply organic fertilizer",
            "Implement drip irrigation",
            "Practice crop rotation",
            "Monitor weather patterns",
            "Use integrated pest management"
        ]
        
        return {
            'yield_prediction': f"{predicted_yield} tons/hectare",
            'confidence': confidence,
            'risk_factors': random.sample(risk_factors, random.randint(2, 4)),
            'recommendations': random.sample(recommendations, random.randint(3, 5)),
            'planting_time': random.choice([
                "March-April", "October-November", "May-June", "August-September"
            ])
        }
    
    def _generate_donations(self, donors):
        """Generate donation records"""
        print("💰 Generating donations...")
        
        purposes = [
            "Support smallholder farmers",
            "Nutrition education programs",
            "Emergency food relief",
            "Agricultural training",
            "School feeding program",
            "Community gardens",
            "Food security research",
            "Farmer equipment support"
        ]
        
        for donor in donors:
            # Each donor has 1-5 donations
            num_donations = random.randint(1, 5)
            
            for _ in range(num_donations):
                amount = random.choice([500, 1000, 2500, 5000, 10000])
                purpose = random.choice(purposes)
                status = random.choice(['completed', 'completed', 'completed', 'pending', 'failed'])
                
                donation = Donation(
                    donor_id=donor.id,
                    amount=amount,
                    currency='KES',
                    purpose=purpose,
                    status=status,
                    transaction_id=f"TXN_{random.randint(100000, 999999)}",
                    created_at=datetime.now() - timedelta(days=random.randint(1, 90))
                )
                
                db.session.add(donation)
    
    def _print_summary(self):
        """Print generation summary"""
        with self.app.app_context():
            user_count = User.query.count()
            food_count = FoodItem.query.count()
            nutrition_count = NutritionAnalysis.query.count()
            prediction_count = CropPrediction.query.count()
            donation_count = Donation.query.count()
            
            print("\n" + "="*50)
            print("📊 DEMO DATA SUMMARY")
            print("="*50)
            print(f"Users created:              {user_count}")
            print(f"Food items:                 {food_count}")
            print(f"Nutrition analyses:         {nutrition_count}")
            print(f"Crop predictions:           {prediction_count}")
            print(f"Donations:                  {donation_count}")
            print("="*50)
            print("\n🔑 Demo Login Credentials:")
            print("Username: farmer1, donor1, beneficiary1, etc.")
            print("Password: demo123")
            print("\n🌐 Access the application at: http://localhost:5000")

def main():
    """Main function to generate demo data"""
    generator = DemoDataGenerator()
    generator.generate_all_demo_data()

if __name__ == '__main__':
    main()