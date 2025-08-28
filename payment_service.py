"""
NutriGuard Payment Service
IntaSend payment gateway integration for secure donations and transactions
"""

import requests
import json
import hmac
import hashlib
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(Enum):
    """Payment method enumeration"""
    MPESA = "mpesa"
    CARD = "card"
    BANK = "bank"
    AIRTEL = "airtel"

@dataclass
class PaymentRequest:
    """Payment request data structure"""
    amount: float
    currency: str
    phone_number: str
    email: str
    purpose: str
    payment_method: PaymentMethod = PaymentMethod.MPESA
    callback_url: Optional[str] = None
    metadata: Optional[Dict] = None

@dataclass
class PaymentResponse:
    """Payment response data structure"""
    transaction_id: str
    status: PaymentStatus
    payment_url: Optional[str] = None
    reference: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

class IntaSendService:
    """IntaSend payment gateway service"""
    
    def __init__(self, public_key: str, secret_key: str, environment: str = "sandbox"):
        self.public_key = public_key
        self.secret_key = secret_key
        self.environment = environment
        
        # Set API endpoints based on environment
        if environment == "live":
            self.base_url = "https://payment.intasend.com/api/v1"
        else:
            self.base_url = "https://sandbox.intasend.com/api/v1"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-IntaSend-Public-API-Key': self.public_key,
        })
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            'Content-Type': 'application/json',
            'X-IntaSend-Public-API-Key': self.public_key,
            'X-IntaSend-Secret-API-Key': self.secret_key,
        }
    
    def _generate_reference(self) -> str:
        """Generate unique payment reference"""
        return f"NG_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
    
    def _validate_payment_request(self, request: PaymentRequest) -> bool:
        """Validate payment request data"""
        if request.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        if not request.phone_number:
            raise ValueError("Phone number is required")
        
        if not request.email:
            raise ValueError("Email is required")
        
        if request.currency not in ['KES', 'USD', 'EUR', 'GBP']:
            raise ValueError("Unsupported currency")
        
        return True
    
    def initiate_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """
        Initiate a payment transaction
        
        Args:
            payment_request: Payment request details
        
        Returns:
            PaymentResponse object with transaction details
        """
        try:
            # Validate request
            self._validate_payment_request(payment_request)
            
            # Generate reference
            reference = self._generate_reference()
            
            # Prepare payload
            payload = {
                "amount": payment_request.amount,
                "currency": payment_request.currency,
                "phone_number": self._format_phone_number(payment_request.phone_number),
                "email": payment_request.email,
                "api_ref": reference,
                "narrative": payment_request.purpose,
                "method": payment_request.payment_method.value,
                "callback_url": payment_request.callback_url,
            }
            
            # Add metadata if provided
            if payment_request.metadata:
                payload["metadata"] = payment_request.metadata
            
            # Make API request
            response = self.session.post(
                f"{self.base_url}/checkout/",
                headers=self._get_auth_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return PaymentResponse(
                    transaction_id=data.get("id", reference),
                    status=PaymentStatus.PENDING,
                    payment_url=data.get("payment_url"),
                    reference=reference,
                    message="Payment initiated successfully"
                )
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("message", f"HTTP {response.status_code}")
                
                logger.error(f"Payment initiation failed: {error_message}")
                return PaymentResponse(
                    transaction_id=reference,
                    status=PaymentStatus.FAILED,
                    error=error_message
                )
                
        except requests.RequestException as e:
            logger.error(f"Network error during payment initiation: {e}")
            return PaymentResponse(
                transaction_id=self._generate_reference(),
                status=PaymentStatus.FAILED,
                error="Network error occurred"
            )
        except Exception as e:
            logger.error(f"Payment initiation error: {e}")
            return PaymentResponse(
                transaction_id=self._generate_reference(),
                status=PaymentStatus.FAILED,
                error=str(e)
            )
    
    def check_payment_status(self, transaction_id: str) -> PaymentResponse:
        """
        Check the status of a payment transaction
        
        Args:
            transaction_id: Transaction ID to check
        
        Returns:
            PaymentResponse with current status
        """
        try:
            response = self.session.get(
                f"{self.base_url}/checkout/{transaction_id}/",
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                status_mapping = {
                    "PENDING": PaymentStatus.PENDING,
                    "PROCESSING": PaymentStatus.PROCESSING,
                    "COMPLETE": PaymentStatus.COMPLETED,
                    "FAILED": PaymentStatus.FAILED,
                    "CANCELLED": PaymentStatus.CANCELLED,
                }
                
                status = status_mapping.get(
                    data.get("state", "PENDING").upper(),
                    PaymentStatus.PENDING
                )
                
                return PaymentResponse(
                    transaction_id=transaction_id,
                    status=status,
                    reference=data.get("api_ref"),
                    message=data.get("narrative")
                )
            else:
                return PaymentResponse(
                    transaction_id=transaction_id,
                    status=PaymentStatus.FAILED,
                    error="Unable to retrieve payment status"
                )
                
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return PaymentResponse(
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                error="Status check failed"
            )
    
    def refund_payment(self, transaction_id: str, amount: Optional[float] = None) -> PaymentResponse:
        """
        Refund a completed payment
        
        Args:
            transaction_id: Transaction ID to refund
            amount: Amount to refund (optional, full refund if not specified)
        
        Returns:
            PaymentResponse with refund status
        """
        try:
            payload = {"transaction_id": transaction_id}
            if amount:
                payload["amount"] = amount
            
            response = self.session.post(
                f"{self.base_url}/refund/",
                headers=self._get_auth_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return PaymentResponse(
                    transaction_id=data.get("id", transaction_id),
                    status=PaymentStatus.REFUNDED,
                    reference=data.get("reference"),
                    message="Refund processed successfully"
                )
            else:
                error_data = response.json() if response.content else {}
                return PaymentResponse(
                    transaction_id=transaction_id,
                    status=PaymentStatus.FAILED,
                    error=error_data.get("message", "Refund failed")
                )
                
        except Exception as e:
            logger.error(f"Refund error: {e}")
            return PaymentResponse(
                transaction_id=transaction_id,
                status=PaymentStatus.FAILED,
                error="Refund processing failed"
            )
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for IntaSend"""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone))
        
        # Handle Kenyan numbers
        if digits_only.startswith('0'):
            digits_only = '254' + digits_only[1:]
        elif not digits_only.startswith('254'):
            digits_only = '254' + digits_only
        
        return digits_only
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature from IntaSend
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers
        
        Returns:
            True if signature is valid
        """
        try:
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

class PaymentManager:
    """High-level payment management service"""
    
    def __init__(self, intasend_service: IntaSendService):
        self.intasend = intasend_service
        self.payment_cache = {}  # In production, use Redis
    
    def process_donation(self, donor_id: int, amount: float, currency: str,
                        phone: str, email: str, purpose: str,
                        metadata: Optional[Dict] = None) -> PaymentResponse:
        """
        Process a donation payment
        
        Args:
            donor_id: ID of the donor
            amount: Donation amount
            currency: Currency code
            phone: Phone number for payment
            email: Email address
            purpose: Purpose of donation
            metadata: Additional metadata
        
        Returns:
            PaymentResponse object
        """
        # Add donor information to metadata
        donation_metadata = {
            "donor_id": donor_id,
            "donation_type": "general",
            "platform": "nutriguard",
            **(metadata or {})
        }
        
        payment_request = PaymentRequest(
            amount=amount,
            currency=currency,
            phone_number=phone,
            email=email,
            purpose=f"NutriGuard Donation: {purpose}",
            payment_method=PaymentMethod.MPESA,
            metadata=donation_metadata
        )
        
        return self.intasend.initiate_payment(payment_request)
    
    def process_marketplace_payment(self, buyer_id: int, seller_id: int,
                                  items: List[Dict], total_amount: float,
                                  currency: str, phone: str, email: str) -> PaymentResponse:
        """
        Process a marketplace payment for food items
        
        Args:
            buyer_id: ID of the buyer
            seller_id: ID of the seller
            items: List of items being purchased
            total_amount: Total payment amount
            currency: Currency code
            phone: Phone number for payment
            email: Email address
        
        Returns:
            PaymentResponse object
        """
        marketplace_metadata = {
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "items": items,
            "transaction_type": "marketplace",
            "platform": "nutriguard"
        }
        
        payment_request = PaymentRequest(
            amount=total_amount,
            currency=currency,
            phone_number=phone,
            email=email,
            purpose=f"NutriGuard Marketplace Purchase",
            payment_method=PaymentMethod.MPESA,
            metadata=marketplace_metadata
        )
        
        return self.intasend.initiate_payment(payment_request)
    
    def handle_webhook_notification(self, payload: Dict) -> bool:
        """
        Handle payment webhook notifications
        
        Args:
            payload: Webhook payload from IntaSend
        
        Returns:
            True if processed successfully
        """
        try:
            transaction_id = payload.get("id")
            status = payload.get("state")
            reference = payload.get("api_ref")
            
            if not transaction_id:
                logger.warning("Webhook missing transaction ID")
                return False
            
            # Update payment status in database
            # This would typically update your database records
            logger.info(f"Payment {transaction_id} status updated to {status}")
            
            # Send notifications based on status
            if status == "COMPLETE":
                self._send_payment_success_notification(payload)
            elif status == "FAILED":
                self._send_payment_failure_notification(payload)
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return False
    
    def _send_payment_success_notification(self, payload: Dict):
        """Send notification for successful payment"""
        # Implementation would send email/SMS notifications
        logger.info(f"Payment success notification for {payload.get('id')}")
    
    def _send_payment_failure_notification(self, payload: Dict):
        """Send notification for failed payment"""
        # Implementation would send email/SMS notifications
        logger.info(f"Payment failure notification for {payload.get('id')}")
    
    def get_payment_analytics(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get payment analytics for a date range
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
        
        Returns:
            Dictionary with payment analytics
        """
        # This would query your database for payment statistics
        # For now, return mock data
        return {
            "total_transactions": 150,
            "successful_transactions": 142,
            "failed_transactions": 8,
            "total_amount": 125000.00,
            "average_transaction": 833.33,
            "success_rate": 94.67,
            "top_payment_methods": [
                {"method": "mpesa", "count": 130, "percentage": 86.67},
                {"method": "card", "count": 15, "percentage": 10.00},
                {"method": "bank", "count": 5, "percentage": 3.33}
            ]
        }

class PaymentSecurity:
    """Payment security utilities"""
    
    @staticmethod
    def validate_amount(amount: float, min_amount: float = 1.0,
                       max_amount: float = 1000000.0) -> bool:
        """Validate payment amount"""
        return min_amount <= amount <= max_amount
    
    @staticmethod
    def detect_fraud(payment_data: Dict) -> bool:
        """Basic fraud detection"""
        # Implement fraud detection logic
        # Check for suspicious patterns, amounts, etc.
        
        amount = payment_data.get("amount", 0)
        
        # Flag very large amounts
        if amount > 100000:
            return True
        
        # Flag multiple rapid transactions (would need transaction history)
        # This is a simplified check
        return False
    
    @staticmethod
    def sanitize_payment_data(data: Dict) -> Dict:
        """Sanitize payment data for logging/storage"""
        sensitive_fields = ['phone_number', 'email', 'api_key']
        sanitized = data.copy()
        
        for field in sensitive_fields:
            if field in sanitized:
                if field == 'phone_number':
                    # Mask phone number
                    phone = sanitized[field]
                    sanitized[field] = phone[:3] + '*' * (len(phone) - 6) + phone[-3:]
                elif field == 'email':
                    # Mask email
                    email = sanitized[field]
                    username, domain = email.split('@')
                    sanitized[field] = username[:2] + '*' * (len(username) - 2) + '@' + domain
                else:
                    sanitized[field] = '[REDACTED]'
        
        return sanitized

# Factory function
def create_payment_service(config: Dict) -> Optional[PaymentManager]:
    """Create payment service instance"""
    public_key = config.get('INTASEND_PUBLIC_KEY')
    secret_key = config.get('INTASEND_SECRET_KEY')
    environment = config.get('INTASEND_ENVIRONMENT', 'sandbox')
    
    if not public_key or not secret_key:
        logger.warning("IntaSend credentials not configured")
        return None
    
    intasend_service = IntaSendService(public_key, secret_key, environment)
    return PaymentManager(intasend_service)