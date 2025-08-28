"""
NutriGuard Deployment Script
Automated deployment and setup for production environment
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import mysql.connector
from mysql.connector import Error
import redis
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DeploymentManager:
    """Manages the deployment process"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_installed = False
        self.database_setup = False
        self.redis_setup = False
        
    def deploy(self, environment='production'):
        """Main deployment function"""
        logger.info(f"Starting NutriGuard deployment for {environment}")
        
        try:
            # Step 1: Check system requirements
            self.check_system_requirements()
            
            # Step 2: Install Python dependencies
            self.install_dependencies()
            
            # Step 3: Setup database
            self.setup_database()
            
            # Step 4: Setup Redis (if available)
            self.setup_redis()
            
            # Step 5: Configure environment
            self.setup_environment(environment)
            
            # Step 6: Run tests
            if environment != 'production':
                self.run_tests()
            
            # Step 7: Setup web server (production only)
            if environment == 'production':
                self.setup_web_server()
            
            # Step 8: Final verification
            self.verify_deployment()
            
            logger.info("Deployment completed successfully!")
            self.print_deployment_summary()
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            sys.exit(1)
    
    def check_system_requirements(self):
        """Check if system meets requirements"""
        logger.info("Checking system requirements...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 8:
            raise RuntimeError("Python 3.8+ is required")
        logger.info(f"Python version: {python_version.major}.{python_version.minor}")
        
        # Check if pip is available
        try:
            subprocess.run(['pip', '--version'], check=True, capture_output=True)
            logger.info("pip is available")
        except subprocess.CalledProcessError:
            raise RuntimeError("pip is not available")
        
        # Check if MySQL is available
        try:
            result = subprocess.run(['mysql', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("MySQL is available")
            else:
                logger.warning("MySQL client not found - database setup may require manual configuration")
        except FileNotFoundError:
            logger.warning("MySQL client not found - database setup may require manual configuration")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        logger.info("Installing Python dependencies...")
        
        requirements_file = self.project_root / 'requirements.txt'
        if not requirements_file.exists():
            raise FileNotFoundError("requirements.txt not found")
        
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], check=True, capture_output=True)
            
            self.requirements_installed = True
            logger.info("Dependencies installed successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            raise
    
    def setup_database(self):
        """Setup MySQL database"""
        logger.info("Setting up database...")
        
        # Load database configuration
        db_config = self.get_database_config()
        
        if not db_config:
            logger.warning("Database configuration not found - skipping database setup")
            return
        
        try:
            # Connect to MySQL server (without database)
            connection = mysql.connector.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=db_config['password']
            )
            
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
            logger.info(f"Database '{db_config['database']}' created/verified")
            
            cursor.close()
            connection.close()
            
            # Run database schema setup
            schema_file = self.project_root / 'database_setup.sql'
            if schema_file.exists():
                self.run_sql_file(str(schema_file), db_config)
                logger.info("Database schema applied successfully")
            
            self.database_setup = True
            
        except Error as e:
            logger.error(f"Database setup failed: {e}")
            logger.warning("Database setup failed - manual configuration required")
    
    def get_database_config(self):
        """Get database configuration from environment or defaults"""
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Parse DATABASE_URL (format: mysql://user:password@host/database)
            try:
                from urllib.parse import urlparse
                parsed = urlparse(database_url)
                return {
                    'host': parsed.hostname or 'localhost',
                    'user': parsed.username or 'root',
                    'password': parsed.password or '',
                    'database': parsed.path.lstrip('/') or 'nutriguard'
                }
            except Exception:
                pass
        
        # Default configuration
        return {
            'host': 'localhost',
            'user': 'root',
            'password': os.environ.get('MYSQL_PASSWORD', ''),
            'database': 'nutriguard'
        }
    
    def run_sql_file(self, file_path, db_config):
        """Run SQL file against database"""
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            
            with open(file_path, 'r') as file:
                sql_commands = file.read().split(';')
                
                for command in sql_commands:
                    command = command.strip()
                    if command:
                        cursor.execute(command)
            
            connection.commit()
            cursor.close()
            connection.close()
            
        except Error as e:
            logger.error(f"Failed to execute SQL file: {e}")
            raise
    
    def setup_redis(self):
        """Setup Redis for caching and sessions"""
        logger.info("Setting up Redis...")
        
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            # Test Redis connection
            r = redis.from_url(redis_url)
            r.ping()
            
            logger.info("Redis connection successful")
            self.redis_setup = True
            
        except Exception as e:
            logger.warning(f"Redis setup failed: {e}")
            logger.warning("Redis not available - some features may be limited")
    
    def setup_environment(self, environment):
        """Setup environment configuration"""
        logger.info(f"Setting up {environment} environment...")
        
        env_file = self.project_root / '.env'
        env_example = self.project_root / '.env.example'
        
        if not env_file.exists() and env_example.exists():
            logger.info("Creating .env file from example...")
            import shutil
            shutil.copy2(env_example, env_file)
            logger.warning("Please update .env file with your actual configuration values")
        
        # Set Flask environment
        os.environ['FLASK_ENV'] = environment
        
        if environment == 'production':
            os.environ['FLASK_DEBUG'] = 'False'
        else:
            os.environ['FLASK_DEBUG'] = 'True'
    
    def run_tests(self):
        """Run test suite"""
        logger.info("Running tests...")
        
        test_file = self.project_root / 'test_suite.py'
        if not test_file.exists():
            logger.warning("Test suite not found - skipping tests")
            return
        
        try:
            result = subprocess.run([
                sys.executable, str(test_file)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("Tests passed successfully")
            else:
                logger.warning("Some tests failed - check test output")
                logger.warning(result.stdout)
                
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
    
    def setup_web_server(self):
        """Setup production web server (Gunicorn)"""
        logger.info("Setting up production web server...")
        
        # Create Gunicorn configuration
        gunicorn_config = self.project_root / 'gunicorn.conf.py'
        
        if not gunicorn_config.exists():
            self.create_gunicorn_config(gunicorn_config)
        
        # Create systemd service file (Linux)
        if sys.platform.startswith('linux'):
            self.create_systemd_service()
        
        logger.info("Web server configuration created")
    
    def create_gunicorn_config(self, config_path):
        """Create Gunicorn configuration file"""
        config_content = """
# Gunicorn configuration for NutriGuard
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "nutriguard"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Preload application
preload_app = True
"""
        
        with open(config_path, 'w') as f:
            f.write(config_content.strip())
    
    def create_systemd_service(self):
        """Create systemd service file for Linux systems"""
        service_content = f"""
[Unit]
Description=NutriGuard - SDG 2 Zero Hunger Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
RuntimeDirectory=nutriguard
WorkingDirectory={self.project_root}
Environment=PATH={sys.executable}
ExecStart={sys.executable} -m gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
        
        service_file = '/etc/systemd/system/nutriguard.service'
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content.strip())
            
            logger.info(f"Systemd service file created: {service_file}")
            logger.info("To enable and start the service, run:")
            logger.info("sudo systemctl enable nutriguard")
            logger.info("sudo systemctl start nutriguard")
            
        except PermissionError:
            logger.warning("Cannot create systemd service file - insufficient permissions")
            logger.info("Manual service setup required")
    
    def verify_deployment(self):
        """Verify deployment is working"""
        logger.info("Verifying deployment...")
        
        # Check if application starts
        try:
            from app import app
            
            # Test application context
            with app.app_context():
                logger.info("Application context created successfully")
            
            # Check database connection
            if self.database_setup:
                try:
                    from app import db
                    with app.app_context():
                        db.engine.execute('SELECT 1')
                    logger.info("Database connection verified")
                except Exception as e:
                    logger.warning(f"Database connection test failed: {e}")
            
            # Check Redis connection
            if self.redis_setup:
                try:
                    import redis
                    r = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
                    r.ping()
                    logger.info("Redis connection verified")
                except Exception as e:
                    logger.warning(f"Redis connection test failed: {e}")
            
        except Exception as e:
            logger.error(f"Application verification failed: {e}")
            raise
    
    def print_deployment_summary(self):
        """Print deployment summary"""
        print("\n" + "="*60)
        print("NUTRIGUARD DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"Deployment completed at: {datetime.now()}")
        print(f"Project root: {self.project_root}")
        print(f"Python dependencies: {'✓' if self.requirements_installed else '✗'}")
        print(f"Database setup: {'✓' if self.database_setup else '✗'}")
        print(f"Redis setup: {'✓' if self.redis_setup else '✗'}")
        print("\nNext steps:")
        print("1. Update .env file with your configuration")
        print("2. Configure your web server (nginx recommended)")
        print("3. Set up SSL certificates")
        print("4. Configure monitoring and logging")
        print("5. Set up backup procedures")
        print("\nTo start the application:")
        print("  Development: python app.py")
        print("  Production:  gunicorn --config gunicorn.conf.py app:app")
        print("="*60)

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NutriGuard Deployment Script')
    parser.add_argument(
        '--environment', 
        choices=['development', 'production', 'testing'],
        default='production',
        help='Deployment environment'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip running tests'
    )
    
    args = parser.parse_args()
    
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Run deployment
    deployer = DeploymentManager()
    deployer.deploy(args.environment)

if __name__ == '__main__':
    main()