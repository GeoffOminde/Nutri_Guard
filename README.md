# NutriGuard - SDG 2 Zero Hunger Initiative

![NutriGuard Logo](https://img.shields.io/badge/SDG-2%20Zero%20Hunger-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.3+-red)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

A comprehensive food security platform leveraging AI technology to address SDG 2 (Zero Hunger) through innovative nutrition analysis, crop prediction, and community support systems.

## 🌟 Features

### 🤖 AI-Powered Solutions
- **Nutrition Analysis**: Advanced AI-driven meal analysis using OpenAI GPT models
- **Crop Yield Prediction**: Machine learning-based agricultural forecasting
- **Personalized Recommendations**: Tailored advice based on user profiles
- **Real-time Analytics**: Comprehensive food security insights

### 💳 Secure Payment Integration
- **IntaSend Gateway**: Seamless mobile money and card payments
- **Donation Platform**: Support food security initiatives
- **Marketplace**: Direct farmer-to-consumer transactions
- **Multi-currency Support**: KES, USD, EUR, GBP

### 🔐 Enterprise Security
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Protection against abuse and attacks
- **Input Validation**: Comprehensive data sanitization
- **CSRF Protection**: Cross-site request forgery prevention
- **SQL Injection Prevention**: Parameterized queries and ORM

### 📱 Modern UI/UX
- **Responsive Design**: Mobile-first approach
- **Progressive Web App**: Offline capabilities
- **Accessibility**: WCAG 2.1 compliant
- **Real-time Updates**: WebSocket integration
- **Multi-language Support**: Internationalization ready

## 🏗️ Architecture

### Technology Stack
- **Backend**: Python 3.8+, Flask 2.3+
- **Database**: MySQL 8.0+ with Redis caching
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **AI Services**: OpenAI GPT-3.5/4, Hugging Face Transformers
- **Payment**: IntaSend API integration
- **Deployment**: Gunicorn, Nginx, Docker (optional)

### System Requirements
- Python 3.8 or higher
- MySQL 8.0 or higher
- Redis 6.0+ (recommended)
- 2GB RAM minimum (4GB recommended)
- 10GB disk space

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/nutriguard.git
cd nutriguard
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Create MySQL database
mysql -u root -p
CREATE DATABASE nutriguard;
exit

# Run database schema
mysql -u root -p nutriguard < database_setup.sql
```

### 4. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 5. Run the Application
```bash
# Development mode
python app.py

# Production mode
gunicorn --config gunicorn.conf.py app:app
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | Yes | - |
| `DATABASE_URL` | MySQL connection string | Yes | - |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `INTASEND_PUBLIC_KEY` | IntaSend public key | Yes | - |
| `INTASEND_SECRET_KEY` | IntaSend secret key | Yes | - |
| `REDIS_URL` | Redis connection string | No | `redis://localhost:6379/0` |
| `FLASK_ENV` | Environment mode | No | `development` |

### Database Configuration
```python
# Example DATABASE_URL formats
mysql://username:password@localhost/nutriguard
mysql://user:pass@hostname:3306/dbname
```

### API Keys Setup
1. **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/)
2. **IntaSend**: Register at [IntaSend](https://intasend.com/) and get your keys
3. **Hugging Face** (optional): Get token from [Hugging Face](https://huggingface.co/)

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python test_suite.py

# Run specific test class
python -m unittest test_suite.TestAuthentication

# Run with coverage
pip install coverage
coverage run test_suite.py
coverage report
```

### Test Categories
- **Authentication Tests**: User registration, login, JWT tokens
- **AI Service Tests**: Nutrition analysis, crop prediction
- **Payment Tests**: IntaSend integration, donation processing
- **Security Tests**: Input validation, rate limiting
- **API Tests**: Endpoint functionality, error handling

## 📊 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/register
Content-Type: application/json

{
    "username": "farmer1",
    "email": "farmer@example.com",
    "password": "securepassword",
    "user_type": "farmer",
    "location": "Nairobi, Kenya",
    "phone": "254712345678"
}
```

#### Login
```http
POST /api/login
Content-Type: application/json

{
    "username": "farmer1",
    "password": "securepassword"
}
```

### AI Services

#### Nutrition Analysis
```http
POST /api/nutrition/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
    "meal_description": "Grilled chicken with steamed vegetables and brown rice"
}
```

#### Crop Prediction
```http
POST /api/crops/predict
Authorization: Bearer <token>
Content-Type: application/json

{
    "crop_type": "maize",
    "location": "Nairobi, Kenya",
    "soil_data": {
        "type": "loamy",
        "ph": 6.5,
        "organic_matter": "high"
    },
    "weather_data": {
        "expected_rainfall": 800,
        "temperature_range": "20-30°C"
    }
}
```

### Payment Endpoints

#### Initiate Donation
```http
POST /api/donate
Authorization: Bearer <token>
Content-Type: application/json

{
    "amount": 1000,
    "phone_number": "254712345678",
    "purpose": "Support smallholder farmers"
}
```

## 🔧 Deployment

### Automated Deployment
```bash
# Run deployment script
python deploy.py --environment production

# Or for development
python deploy.py --environment development
```

### Manual Production Setup

#### 1. Web Server (Nginx)
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/nutriguard/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 2. SSL Certificate (Let's Encrypt)
```bash
sudo certbot --nginx -d yourdomain.com
```

#### 3. Systemd Service
```bash
sudo cp nutriguard.service /etc/systemd/system/
sudo systemctl enable nutriguard
sudo systemctl start nutriguard
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

## 📈 Monitoring and Analytics

### Health Checks
- `/health` - Application health status
- `/metrics` - Prometheus metrics (if enabled)
- Database connection monitoring
- Redis connection status

### Logging
- Application logs: `logs/app.log`
- Access logs: `logs/access.log`
- Error logs: `logs/error.log`
- Deployment logs: `deployment.log`

### Performance Monitoring
- Response time tracking
- Database query performance
- AI service latency
- Payment processing metrics

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Make your changes
5. Run tests: `python test_suite.py`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Add unit tests for new features
- Update documentation as needed
- Use type hints where appropriate

### Testing Guidelines
- Maintain >90% test coverage
- Write both unit and integration tests
- Mock external API calls
- Test error conditions
- Validate security measures

## 🔒 Security

### Security Measures Implemented
- **Authentication**: JWT tokens with expiration
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive sanitization
- **SQL Injection**: Parameterized queries
- **XSS Protection**: Content Security Policy
- **CSRF Protection**: Token validation
- **Rate Limiting**: Request throttling
- **HTTPS Enforcement**: SSL/TLS encryption

### Security Best Practices
- Regular dependency updates
- Security header implementation
- Secure cookie configuration
- Password strength requirements
- Session management
- Audit logging

## 📚 Documentation

### Additional Resources
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Security Guidelines](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)
- [FAQ](docs/faq.md)

### SDG 2 Alignment
NutriGuard directly supports UN Sustainable Development Goal 2 (Zero Hunger) by:
- Improving nutrition through AI-powered meal analysis
- Supporting smallholder farmers with crop prediction
- Facilitating food access through marketplace integration
- Enabling community support through donation platform
- Promoting sustainable agriculture practices

## 🌍 Impact Metrics

### Key Performance Indicators
- Users registered and active
- Nutrition analyses completed
- Crop predictions generated
- Donations processed
- Farmers supported
- Lives impacted

### Success Stories
- Improved crop yields for smallholder farmers
- Better nutrition awareness in communities
- Successful donation campaigns
- Marketplace transaction growth

## 📞 Support

### Getting Help
- **Documentation**: Check this README and docs folder
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Email**: contact@nutriguard.com (if applicable)

### Community
- Join our community discussions
- Follow us on social media
- Contribute to the project
- Share your success stories

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **UN SDG 2**: Zero Hunger initiative inspiration
- **OpenAI**: AI-powered nutrition analysis
- **IntaSend**: Payment processing partnership
- **Flask Community**: Web framework support
- **Contributors**: All developers who contributed to this project

---

**Built with ❤️ for SDG 2 Zero Hunger Initiative**

*"Technology for a hunger-free world"*