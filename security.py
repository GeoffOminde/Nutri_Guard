"""
NutriGuard Security Module
Advanced security features and middleware
"""

import hashlib
import hmac
import secrets
import time
import jwt
from functools import wraps
from flask import request, jsonify, current_app, g
from werkzeug.security import safe_str_cmp
import logging
import re

logger = logging.getLogger(__name__)

class SecurityManager:
    """Centralized security management"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security features with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Initialize rate limiting storage
        self.init_rate_limiting(app)
    
    def init_rate_limiting(self, app):
        """Initialize rate limiting with Redis"""
        try:
            import redis
            self.redis_client = redis.from_url(app.config.get('RATELIMIT_STORAGE_URL'))
            self.redis_client.ping()  # Test connection
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
            self.redis_client = None
    
    def before_request(self):
        """Security checks before each request"""
        # Check for suspicious patterns
        if self.is_suspicious_request():
            logger.warning(f"Suspicious request from {request.remote_addr}: {request.url}")
            return jsonify({'error': 'Request blocked'}), 403
        
        # Validate content type for POST requests
        if request.method == 'POST' and request.content_type:
            if not request.content_type.startswith(('application/json', 'multipart/form-data')):
                return jsonify({'error': 'Invalid content type'}), 400
    
    def after_request(self, response):
        """Add security headers to response"""
        headers = current_app.config.get('SECURITY_HEADERS', {})
        for header, value in headers.items():
            response.headers[header] = value
        
        return response
    
    def is_suspicious_request(self):
        """Check for suspicious request patterns"""
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS attempts
            r'union\s+select',  # SQL injection
            r'drop\s+table',  # SQL injection
            r'exec\s*\(',  # Code injection
            r'\.\./',  # Path traversal
        ]
        
        # Check URL and parameters
        full_url = request.url.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, full_url, re.IGNORECASE):
                return True
        
        # Check request data
        if request.data:
            try:
                data = request.data.decode('utf-8').lower()
                for pattern in suspicious_patterns:
                    if re.search(pattern, data, re.IGNORECASE):
                        return True
            except UnicodeDecodeError:
                pass
        
        return False

class TokenManager:
    """JWT token management with enhanced security"""
    
    @staticmethod
    def generate_token(user_id, expires_in=3600):
        """Generate secure JWT token"""
        payload = {
            'user_id': user_id,
            'exp': time.time() + expires_in,
            'iat': time.time(),
            'jti': secrets.token_hex(16),  # Unique token ID
        }
        
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def revoke_token(jti):
        """Revoke token by adding to blacklist"""
        # In production, store in Redis or database
        # For now, we'll use a simple in-memory store
        if not hasattr(g, 'revoked_tokens'):
            g.revoked_tokens = set()
        g.revoked_tokens.add(jti)
    
    @staticmethod
    def is_token_revoked(jti):
        """Check if token is revoked"""
        revoked_tokens = getattr(g, 'revoked_tokens', set())
        return jti in revoked_tokens

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
    
    def is_rate_limited(self, key, limit=100, window=3600):
        """Check if request should be rate limited"""
        if not self.redis_client:
            return False
        
        try:
            current_time = int(time.time())
            pipeline = self.redis_client.pipeline()
            
            # Sliding window rate limiting
            pipeline.zremrangebyscore(key, 0, current_time - window)
            pipeline.zcard(key)
            pipeline.zadd(key, {str(current_time): current_time})
            pipeline.expire(key, window)
            
            results = pipeline.execute()
            request_count = results[1]
            
            return request_count >= limit
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return False
    
    def get_rate_limit_key(self, identifier, endpoint=None):
        """Generate rate limit key"""
        base_key = f"rate_limit:{identifier}"
        if endpoint:
            base_key += f":{endpoint}"
        return base_key

class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        return len(digits_only) >= 10 and len(digits_only) <= 15
    
    @staticmethod
    def sanitize_string(text, max_length=1000):
        """Sanitize string input"""
        if not isinstance(text, str):
            return ""
        
        # Remove potential XSS characters
        text = re.sub(r'[<>"\']', '', text)
        
        # Limit length
        text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        return True, "Password is strong"

class CryptoUtils:
    """Cryptographic utilities"""
    
    @staticmethod
    def generate_salt():
        """Generate cryptographic salt"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = CryptoUtils.generate_salt()
        
        # Use PBKDF2 for password hashing
        key = hashlib.pbkdf2_hmac('sha256', 
                                  password.encode('utf-8'), 
                                  salt.encode('utf-8'), 
                                  100000)  # 100,000 iterations
        
        return salt + key.hex()
    
    @staticmethod
    def verify_password(password, hashed_password):
        """Verify password against hash"""
        try:
            salt = hashed_password[:64]  # First 64 chars are salt
            key = hashed_password[64:]   # Rest is the key
            
            new_key = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
            
            return safe_str_cmp(key, new_key.hex())
        except Exception:
            return False
    
    @staticmethod
    def generate_csrf_token():
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token, expected_token):
        """Verify CSRF token"""
        return safe_str_cmp(token, expected_token)

# Security decorators
def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
        except IndexError:
            return jsonify({'error': 'Invalid token format'}), 401
        
        payload = TokenManager.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Check if token is revoked
        if TokenManager.is_token_revoked(payload.get('jti')):
            return jsonify({'error': 'Token has been revoked'}), 401
        
        g.current_user_id = payload['user_id']
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(required_role):
    """Decorator to require specific user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would need to be implemented with user role checking
            # For now, we'll just pass through
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(requests_per_hour=100):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user identifier
            user_id = getattr(g, 'current_user_id', request.remote_addr)
            
            # Create rate limiter
            limiter = RateLimiter()
            key = limiter.get_rate_limit_key(user_id, f.__name__)
            
            if limiter.is_rate_limited(key, requests_per_hour, 3600):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json_input(required_fields=None):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'JSON data required'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
            
            # Sanitize string inputs
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = InputValidator.sanitize_string(value)
            
            request.validated_json = data
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Security middleware
class SecurityMiddleware:
    """WSGI middleware for additional security"""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        # Add security checks here if needed
        return self.app(environ, start_response)