-- NutriGuard Database Setup
-- SDG 2 Zero Hunger Application Database Schema

CREATE DATABASE IF NOT EXISTS nutriguard;
USE nutriguard;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type ENUM('farmer', 'donor', 'beneficiary', 'admin') DEFAULT 'beneficiary',
    location VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_user_type (user_type)
);

-- Food items table
CREATE TABLE IF NOT EXISTS food_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    nutritional_info JSON,
    price_per_kg DECIMAL(10, 2),
    availability INT DEFAULT 0,
    farmer_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_category (category),
    INDEX idx_farmer (farmer_id)
);

-- Donations table
CREATE TABLE IF NOT EXISTS donations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'KES',
    purpose VARCHAR(255),
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    transaction_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_donor (donor_id),
    INDEX idx_status (status),
    INDEX idx_transaction (transaction_id)
);

-- Crop predictions table
CREATE TABLE IF NOT EXISTS crop_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    crop_type VARCHAR(100) NOT NULL,
    location VARCHAR(255) NOT NULL,
    soil_data JSON,
    weather_data JSON,
    ai_prediction JSON,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_farmer (farmer_id),
    INDEX idx_crop_type (crop_type),
    INDEX idx_location (location)
);

-- Nutrition analysis table
CREATE TABLE IF NOT EXISTS nutrition_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    meal_description TEXT NOT NULL,
    nutrition_breakdown JSON,
    recommendations JSON,
    deficiency_alerts JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_created_at (created_at)
);

-- Food security alerts table
CREATE TABLE IF NOT EXISTS food_security_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region VARCHAR(255) NOT NULL,
    alert_type ENUM('shortage', 'price_spike', 'weather_warning', 'disease_outbreak') NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    description TEXT,
    affected_crops JSON,
    recommendations JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_region (region),
    INDEX idx_alert_type (alert_type),
    INDEX idx_severity (severity),
    INDEX idx_active (is_active)
);

-- Market prices table
CREATE TABLE IF NOT EXISTS market_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    food_item_id INT NOT NULL,
    market_location VARCHAR(255) NOT NULL,
    price_per_kg DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'KES',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100),
    FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE CASCADE,
    INDEX idx_food_item (food_item_id),
    INDEX idx_location (market_location),
    INDEX idx_recorded_at (recorded_at)
);

-- User nutrition profiles
CREATE TABLE IF NOT EXISTS user_nutrition_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    age INT,
    gender ENUM('male', 'female', 'other'),
    weight_kg DECIMAL(5, 2),
    height_cm INT,
    activity_level ENUM('sedentary', 'light', 'moderate', 'active', 'very_active') DEFAULT 'moderate',
    dietary_restrictions JSON,
    health_conditions JSON,
    daily_calorie_target INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_profile (user_id)
);

-- Insert default admin user
INSERT INTO users (username, email, password_hash, user_type, is_verified) 
VALUES ('admin', 'admin@nutriguard.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFgxuIznpSWi/EW', 'admin', TRUE)
ON DUPLICATE KEY UPDATE username=username;

-- Insert sample food items
INSERT INTO food_items (name, category, nutritional_info, price_per_kg) VALUES
('Maize', 'Cereals', '{"calories": 365, "protein": 9.4, "carbs": 74.3, "fiber": 7.3}', 50.00),
('Rice', 'Cereals', '{"calories": 365, "protein": 7.1, "carbs": 80.0, "fiber": 1.3}', 120.00),
('Beans', 'Legumes', '{"calories": 347, "protein": 21.6, "carbs": 63.0, "fiber": 16.0}', 150.00),
('Sweet Potato', 'Tubers', '{"calories": 86, "protein": 1.6, "carbs": 20.1, "fiber": 3.0}', 80.00),
('Kale', 'Vegetables', '{"calories": 49, "protein": 4.3, "carbs": 8.8, "fiber": 3.6}', 100.00)
ON DUPLICATE KEY UPDATE name=name;

-- Create indexes for performance
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_donations_created_at ON donations(created_at);
CREATE INDEX idx_crop_predictions_created_at ON crop_predictions(created_at);
CREATE INDEX idx_nutrition_analysis_created_at ON nutrition_analysis(created_at);

-- Create views for reporting
CREATE OR REPLACE VIEW donation_summary AS
SELECT 
    u.username,
    u.email,
    COUNT(d.id) as donation_count,
    SUM(CASE WHEN d.status = 'completed' THEN d.amount ELSE 0 END) as total_donated,
    MAX(d.created_at) as last_donation
FROM users u
LEFT JOIN donations d ON u.id = d.donor_id
WHERE u.user_type = 'donor'
GROUP BY u.id, u.username, u.email;

CREATE OR REPLACE VIEW nutrition_insights AS
SELECT 
    u.username,
    COUNT(na.id) as analysis_count,
    AVG(JSON_EXTRACT(na.nutrition_breakdown, '$.protein')) as avg_protein,
    MAX(na.created_at) as last_analysis
FROM users u
LEFT JOIN nutrition_analysis na ON u.id = na.user_id
GROUP BY u.id, u.username;

-- Enable event scheduler for automated tasks
SET GLOBAL event_scheduler = ON;

-- Create event to clean old data
DELIMITER $$
CREATE EVENT IF NOT EXISTS cleanup_old_data
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    -- Delete old nutrition analyses older than 1 year
    DELETE FROM nutrition_analysis WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
    
    -- Delete failed donations older than 30 days
    DELETE FROM donations WHERE status = 'failed' AND created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Archive old market prices
    DELETE FROM market_prices WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);
END$$
DELIMITER ;

-- Grant permissions (adjust as needed for production)
-- CREATE USER 'nutriguard_app'@'localhost' IDENTIFIED BY 'secure_password_here';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON nutriguard.* TO 'nutriguard_app'@'localhost';
-- FLUSH PRIVILEGES;