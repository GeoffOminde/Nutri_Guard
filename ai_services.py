"""
NutriGuard AI Services
Advanced AI integration for nutrition analysis and crop prediction
"""

import openai
import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
import hashlib
import time

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

class NutritionAnalyzer:
    """Advanced nutrition analysis using OpenAI GPT models"""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 3600  # 1 hour
    
    def analyze_meal(self, meal_description: str, user_profile: Optional[Dict] = None) -> Dict:
        """
        Analyze nutritional content of a meal with personalized recommendations
        
        Args:
            meal_description: Description of the meal
            user_profile: User's nutritional profile (age, weight, activity level, etc.)
        
        Returns:
            Detailed nutrition analysis
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(meal_description, user_profile)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            # Create personalized prompt
            prompt = self._create_nutrition_prompt(meal_description, user_profile)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional nutritionist AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            result = self._parse_nutrition_response(response.choices[0].message.content)
            
            # Cache the result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Nutrition analysis failed: {e}")
            raise AIServiceError(f"Nutrition analysis failed: {str(e)}")
    
    def _create_nutrition_prompt(self, meal_description: str, user_profile: Optional[Dict]) -> str:
        """Create a comprehensive prompt for nutrition analysis"""
        
        base_prompt = f"""
        Analyze the nutritional content of this meal: "{meal_description}"
        
        Provide a comprehensive analysis including:
        1. Estimated calories
        2. Macronutrients (protein, carbohydrates, fats) in grams
        3. Key vitamins and minerals
        4. Fiber content
        5. Sodium content
        6. Sugar content
        7. Nutritional quality score (1-10)
        8. Potential nutritional deficiencies
        9. Health recommendations
        10. Portion size assessment
        """
        
        if user_profile:
            profile_info = f"""
            
            User Profile:
            - Age: {user_profile.get('age', 'Not specified')}
            - Gender: {user_profile.get('gender', 'Not specified')}
            - Weight: {user_profile.get('weight_kg', 'Not specified')} kg
            - Height: {user_profile.get('height_cm', 'Not specified')} cm
            - Activity Level: {user_profile.get('activity_level', 'moderate')}
            - Dietary Restrictions: {user_profile.get('dietary_restrictions', 'None')}
            - Health Conditions: {user_profile.get('health_conditions', 'None')}
            
            Provide personalized recommendations based on this profile.
            """
            base_prompt += profile_info
        
        base_prompt += """
        
        Format your response as JSON with this structure:
        {
            "calories": number,
            "macronutrients": {
                "protein": number,
                "carbohydrates": number,
                "fats": number,
                "fiber": number
            },
            "micronutrients": {
                "vitamin_c": "amount",
                "iron": "amount",
                "calcium": "amount"
            },
            "sodium_mg": number,
            "sugar_g": number,
            "nutritional_score": number,
            "deficiencies": ["list of potential deficiencies"],
            "recommendations": ["list of personalized recommendations"],
            "portion_assessment": "assessment of portion size",
            "health_benefits": ["list of health benefits"],
            "concerns": ["list of health concerns if any"]
        }
        """
        
        return base_prompt
    
    def _parse_nutrition_response(self, response_text: str) -> Dict:
        """Parse and validate the AI response"""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            
            result = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['calories', 'macronutrients', 'nutritional_score']
            for field in required_fields:
                if field not in result:
                    result[field] = self._get_default_value(field)
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse AI response: {e}")
            return self._get_fallback_analysis()
    
    def _get_default_value(self, field: str):
        """Get default values for missing fields"""
        defaults = {
            'calories': 0,
            'macronutrients': {'protein': 0, 'carbohydrates': 0, 'fats': 0},
            'nutritional_score': 5,
            'deficiencies': [],
            'recommendations': ['Consult a nutritionist for detailed analysis']
        }
        return defaults.get(field, None)
    
    def _get_fallback_analysis(self) -> Dict:
        """Fallback analysis when AI fails"""
        return {
            'calories': 0,
            'macronutrients': {'protein': 0, 'carbohydrates': 0, 'fats': 0},
            'nutritional_score': 5,
            'deficiencies': ['Unable to analyze'],
            'recommendations': ['Please try again or consult a nutritionist'],
            'error': 'Analysis temporarily unavailable'
        }
    
    def _generate_cache_key(self, meal_description: str, user_profile: Optional[Dict]) -> str:
        """Generate cache key for the analysis"""
        key_data = meal_description
        if user_profile:
            key_data += str(sorted(user_profile.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get result from cache if not expired"""
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache the analysis result"""
        self.cache[cache_key] = (result, time.time())

class CropPredictor:
    """Advanced crop yield prediction using AI and agricultural data"""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.cache = {}
        self.cache_ttl = 7200  # 2 hours
        
        # Crop knowledge base
        self.crop_data = {
            'maize': {
                'optimal_ph': (6.0, 7.0),
                'optimal_rainfall': (500, 1200),
                'growing_season': 120,
                'yield_range': (2, 8)  # tons per hectare
            },
            'rice': {
                'optimal_ph': (5.5, 7.0),
                'optimal_rainfall': (1000, 2000),
                'growing_season': 150,
                'yield_range': (3, 10)
            },
            'wheat': {
                'optimal_ph': (6.0, 7.5),
                'optimal_rainfall': (300, 800),
                'growing_season': 180,
                'yield_range': (2, 6)
            },
            'beans': {
                'optimal_ph': (6.0, 7.0),
                'optimal_rainfall': (400, 800),
                'growing_season': 90,
                'yield_range': (1, 3)
            },
            'sweet_potato': {
                'optimal_ph': (5.8, 6.2),
                'optimal_rainfall': (600, 1000),
                'growing_season': 120,
                'yield_range': (8, 25)
            }
        }
    
    def predict_yield(self, crop_type: str, location: str, soil_data: Dict, 
                     weather_data: Dict, farm_size: float = 1.0) -> Dict:
        """
        Predict crop yield based on environmental conditions
        
        Args:
            crop_type: Type of crop to predict
            location: Geographic location
            soil_data: Soil conditions (pH, type, organic matter)
            weather_data: Weather conditions (rainfall, temperature)
            farm_size: Farm size in hectares
        
        Returns:
            Yield prediction with confidence score and recommendations
        """
        try:
            # Check cache
            cache_key = self._generate_prediction_cache_key(
                crop_type, location, soil_data, weather_data
            )
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
            
            # Get baseline prediction from crop data
            baseline_prediction = self._get_baseline_prediction(
                crop_type, soil_data, weather_data
            )
            
            # Enhance with AI analysis
            ai_analysis = self._get_ai_crop_analysis(
                crop_type, location, soil_data, weather_data
            )
            
            # Combine predictions
            result = self._combine_predictions(
                baseline_prediction, ai_analysis, farm_size
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Crop prediction failed: {e}")
            raise AIServiceError(f"Crop prediction failed: {str(e)}")
    
    def _get_baseline_prediction(self, crop_type: str, soil_data: Dict, 
                                weather_data: Dict) -> Dict:
        """Get baseline prediction using agricultural knowledge"""
        
        if crop_type not in self.crop_data:
            return self._get_generic_prediction()
        
        crop_info = self.crop_data[crop_type]
        
        # Calculate suitability scores
        ph_score = self._calculate_ph_suitability(
            soil_data.get('ph', 6.5), crop_info['optimal_ph']
        )
        
        rainfall_score = self._calculate_rainfall_suitability(
            weather_data.get('expected_rainfall', 800), crop_info['optimal_rainfall']
        )
        
        # Overall suitability
        overall_score = (ph_score + rainfall_score) / 2
        
        # Predict yield based on suitability
        min_yield, max_yield = crop_info['yield_range']
        predicted_yield = min_yield + (max_yield - min_yield) * overall_score
        
        return {
            'predicted_yield_tons_per_hectare': round(predicted_yield, 2),
            'confidence': round(overall_score * 100, 1),
            'ph_suitability': round(ph_score * 100, 1),
            'rainfall_suitability': round(rainfall_score * 100, 1),
            'growing_season_days': crop_info['growing_season']
        }
    
    def _get_ai_crop_analysis(self, crop_type: str, location: str, 
                             soil_data: Dict, weather_data: Dict) -> Dict:
        """Get AI-enhanced crop analysis"""
        
        prompt = f"""
        As an agricultural AI expert, analyze the crop growing conditions for {crop_type} in {location}.
        
        Soil Conditions:
        - Type: {soil_data.get('type', 'Unknown')}
        - pH: {soil_data.get('ph', 'Unknown')}
        - Organic Matter: {soil_data.get('organic_matter', 'Unknown')}
        
        Weather Conditions:
        - Expected Rainfall: {weather_data.get('expected_rainfall', 'Unknown')} mm
        - Temperature Range: {weather_data.get('temperature_range', 'Unknown')}
        
        Provide analysis including:
        1. Yield prediction (tons per hectare)
        2. Risk factors and challenges
        3. Optimization recommendations
        4. Best planting time
        5. Confidence score (0-100)
        
        Format response as JSON:
        {{
            "ai_yield_prediction": number,
            "risk_factors": ["list of risks"],
            "recommendations": ["optimization tips"],
            "planting_time": "recommended time",
            "confidence": number,
            "market_considerations": ["market insights"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert agricultural AI consultant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return self._parse_ai_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            return self._get_fallback_ai_analysis()
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse AI response for crop analysis"""
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            return json.loads(json_str)
        except:
            return self._get_fallback_ai_analysis()
    
    def _get_fallback_ai_analysis(self) -> Dict:
        """Fallback AI analysis when AI fails"""
        return {
            'ai_yield_prediction': 0,
            'risk_factors': ['Weather uncertainty', 'Soil conditions'],
            'recommendations': ['Consult local agricultural extension officer'],
            'planting_time': 'Follow local seasonal patterns',
            'confidence': 50,
            'market_considerations': ['Monitor local market prices']
        }
    
    def _combine_predictions(self, baseline: Dict, ai_analysis: Dict, 
                           farm_size: float) -> Dict:
        """Combine baseline and AI predictions"""
        
        # Weight the predictions (70% baseline, 30% AI)
        baseline_yield = baseline.get('predicted_yield_tons_per_hectare', 0)
        ai_yield = ai_analysis.get('ai_yield_prediction', baseline_yield)
        
        combined_yield = (0.7 * baseline_yield) + (0.3 * ai_yield)
        
        # Calculate total production
        total_production = combined_yield * farm_size
        
        # Combine confidence scores
        baseline_confidence = baseline.get('confidence', 50)
        ai_confidence = ai_analysis.get('confidence', 50)
        combined_confidence = (baseline_confidence + ai_confidence) / 2
        
        return {
            'yield_per_hectare': round(combined_yield, 2),
            'total_production_tons': round(total_production, 2),
            'confidence_score': round(combined_confidence, 1),
            'farm_size_hectares': farm_size,
            'risk_factors': ai_analysis.get('risk_factors', []),
            'recommendations': ai_analysis.get('recommendations', []),
            'planting_time': ai_analysis.get('planting_time', 'Consult local experts'),
            'market_considerations': ai_analysis.get('market_considerations', []),
            'baseline_analysis': baseline,
            'prediction_date': datetime.now().isoformat()
        }
    
    def _calculate_ph_suitability(self, actual_ph: float, optimal_range: Tuple[float, float]) -> float:
        """Calculate pH suitability score (0-1)"""
        min_ph, max_ph = optimal_range
        
        if min_ph <= actual_ph <= max_ph:
            return 1.0
        elif actual_ph < min_ph:
            # Penalize low pH
            return max(0, 1 - (min_ph - actual_ph) / 2)
        else:
            # Penalize high pH
            return max(0, 1 - (actual_ph - max_ph) / 2)
    
    def _calculate_rainfall_suitability(self, actual_rainfall: float, 
                                      optimal_range: Tuple[float, float]) -> float:
        """Calculate rainfall suitability score (0-1)"""
        min_rainfall, max_rainfall = optimal_range
        
        if min_rainfall <= actual_rainfall <= max_rainfall:
            return 1.0
        elif actual_rainfall < min_rainfall:
            return max(0, actual_rainfall / min_rainfall)
        else:
            # Too much rain is also problematic
            excess = actual_rainfall - max_rainfall
            return max(0, 1 - (excess / max_rainfall))
    
    def _get_generic_prediction(self) -> Dict:
        """Generic prediction for unknown crops"""
        return {
            'predicted_yield_tons_per_hectare': 2.0,
            'confidence': 30.0,
            'ph_suitability': 50.0,
            'rainfall_suitability': 50.0,
            'growing_season_days': 120
        }
    
    def _generate_prediction_cache_key(self, crop_type: str, location: str, 
                                     soil_data: Dict, weather_data: Dict) -> str:
        """Generate cache key for prediction"""
        key_data = f"{crop_type}_{location}_{str(sorted(soil_data.items()))}_{str(sorted(weather_data.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get prediction from cache if not expired"""
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache the prediction result"""
        self.cache[cache_key] = (result, time.time())

class HuggingFaceService:
    """Alternative AI service using Hugging Face models"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models"
    
    def analyze_text(self, text: str, model: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """Analyze text using Hugging Face models"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = requests.post(
            f"{self.base_url}/{model}",
            headers=headers,
            json={"inputs": text}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise AIServiceError(f"Hugging Face API error: {response.status_code}")

# Factory function to create AI services
def create_ai_services(config: Dict) -> Tuple[NutritionAnalyzer, CropPredictor, Optional[HuggingFaceService]]:
    """Create AI service instances based on configuration"""
    
    nutrition_analyzer = None
    crop_predictor = None
    hf_service = None
    
    if config.get('OPENAI_API_KEY'):
        nutrition_analyzer = NutritionAnalyzer(config['OPENAI_API_KEY'])
        crop_predictor = CropPredictor(config['OPENAI_API_KEY'])
    
    if config.get('HUGGINGFACE_API_KEY'):
        hf_service = HuggingFaceService(config['HUGGINGFACE_API_KEY'])
    
    return nutrition_analyzer, crop_predictor, hf_service