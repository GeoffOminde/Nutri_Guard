/**
 * NutriGuard - SDG 2 Zero Hunger Application
 * Advanced JavaScript functionality with security and performance optimizations
 */

class NutriGuardApp {
    constructor() {
        this.API_BASE = '/api';
        this.currentUser = null;
        this.authToken = localStorage.getItem('authToken');
        this.isLoading = false;
        
        // Initialize application
        this.init();
    }

    async init() {
        try {
            // Show loading screen
            this.showLoadingScreen();
            
            // Initialize components
            await this.initializeComponents();
            
            // Check authentication
            if (this.authToken) {
                await this.validateToken();
            }
            
            // Hide loading screen
            setTimeout(() => this.hideLoadingScreen(), 2000);
            
        } catch (error) {
            console.error('Application initialization failed:', error);
            this.showNotification('Failed to initialize application', 'error');
        }
    }

    async initializeComponents() {
        // Initialize navigation
        this.initNavigation();
        
        // Initialize typewriter effect
        this.initTypewriter();
        
        // Initialize counter animations
        this.initCounters();
        
        // Initialize form handlers
        this.initForms();
        
        // Initialize modal handlers
        this.initModals();
        
        // Initialize scroll effects
        this.initScrollEffects();
        
        // Initialize dashboard
        this.initDashboard();
    }

    // Loading Screen Management
    showLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.style.display = 'flex';
        }
    }

    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.style.opacity = '0';
            loadingScreen.style.visibility = 'hidden';
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }
    }

    // Navigation
    initNavigation() {
        const hamburger = document.getElementById('hamburger');
        const navMenu = document.getElementById('nav-menu');
        const navLinks = document.querySelectorAll('.nav-link');

        // Mobile menu toggle
        if (hamburger) {
            hamburger.addEventListener('click', () => {
                navMenu.classList.toggle('active');
                hamburger.classList.toggle('active');
            });
        }

        // Smooth scrolling for navigation links
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                this.scrollToSection(targetId);
                
                // Update active link
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
                
                // Close mobile menu
                if (navMenu.classList.contains('active')) {
                    navMenu.classList.remove('active');
                    hamburger.classList.remove('active');
                }
            });
        });

        // Navbar scroll effect
        window.addEventListener('scroll', () => {
            const navbar = document.getElementById('navbar');
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    scrollToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            const offsetTop = section.offsetTop - 70; // Account for navbar height
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    }

    // Typewriter Effect
    initTypewriter() {
        const typewriter = document.getElementById('typewriter');
        if (!typewriter) return;

        const words = ['AI Technology', 'Smart Farming', 'Community Support', 'Data Analytics'];
        let wordIndex = 0;
        let charIndex = 0;
        let isDeleting = false;

        const type = () => {
            const currentWord = words[wordIndex];
            
            if (isDeleting) {
                typewriter.textContent = currentWord.substring(0, charIndex - 1);
                charIndex--;
            } else {
                typewriter.textContent = currentWord.substring(0, charIndex + 1);
                charIndex++;
            }

            let typeSpeed = isDeleting ? 50 : 100;

            if (!isDeleting && charIndex === currentWord.length) {
                typeSpeed = 2000; // Pause at end
                isDeleting = true;
            } else if (isDeleting && charIndex === 0) {
                isDeleting = false;
                wordIndex = (wordIndex + 1) % words.length;
                typeSpeed = 500;
            }

            setTimeout(type, typeSpeed);
        };

        type();
    }

    // Counter Animations
    initCounters() {
        const counters = document.querySelectorAll('.stat-number, #metric-users, #metric-donations, #metric-analyses');
        
        const observerOptions = {
            threshold: 0.5,
            rootMargin: '0px 0px -100px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        counters.forEach(counter => observer.observe(counter));
    }

    animateCounter(element) {
        const target = parseInt(element.getAttribute('data-target')) || 
                      parseInt(element.textContent.replace(/[^0-9]/g, '')) || 1000;
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }

            if (element.id === 'metric-donations') {
                element.textContent = `$${Math.floor(current).toLocaleString()}`;
            } else {
                element.textContent = Math.floor(current).toLocaleString();
            }
        }, 16);
    }

    // Form Handlers
    initForms() {
        // Login form
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Register form
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // Donation form
        const donationForm = document.getElementById('donationForm');
        if (donationForm) {
            donationForm.addEventListener('submit', (e) => this.handleDonation(e));
        }

        // Nutrition analyzer
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzeNutrition());
        }

        // Crop predictor
        const cropForm = document.getElementById('cropForm');
        if (cropForm) {
            cropForm.addEventListener('submit', (e) => this.predictCrop(e));
        }
    }

    // Authentication
    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        if (!username || !password) {
            this.showNotification('Please fill in all fields', 'error');
            return;
        }

        try {
            this.setLoading(true);
            
            const response = await fetch(`${this.API_BASE}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.authToken = data.token;
                this.currentUser = data.user;
                localStorage.setItem('authToken', this.authToken);
                
                this.showNotification('Login successful!', 'success');
                this.closeModal('loginModal');
                this.updateUIForLoggedInUser();
                await this.loadDashboard();
            } else {
                this.showNotification(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const userType = document.getElementById('userType').value;
        const location = document.getElementById('registerLocation').value;
        const phone = document.getElementById('registerPhone').value;

        if (!username || !email || !password || !userType) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        if (!this.validateEmail(email)) {
            this.showNotification('Please enter a valid email address', 'error');
            return;
        }

        if (password.length < 6) {
            this.showNotification('Password must be at least 6 characters long', 'error');
            return;
        }

        try {
            this.setLoading(true);
            
            const response = await fetch(`${this.API_BASE}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    user_type: userType,
                    location,
                    phone
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.authToken = data.token;
                this.currentUser = data.user;
                localStorage.setItem('authToken', this.authToken);
                
                this.showNotification('Registration successful!', 'success');
                this.closeModal('registerModal');
                this.updateUIForLoggedInUser();
                await this.loadDashboard();
            } else {
                this.showNotification(data.error || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async validateToken() {
        try {
            const response = await fetch(`${this.API_BASE}/dashboard`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                this.updateUIForLoggedInUser();
                await this.loadDashboard();
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Token validation error:', error);
            this.logout();
        }
    }

    logout() {
        this.authToken = null;
        this.currentUser = null;
        localStorage.removeItem('authToken');
        this.updateUIForLoggedOutUser();
        this.showNotification('You have been logged out', 'info');
    }

    updateUIForLoggedInUser() {
        const navAuth = document.querySelector('.nav-auth');
        if (navAuth && this.currentUser) {
            navAuth.innerHTML = `
                <span class="user-greeting">Welcome, ${this.currentUser.username}</span>
                <button class="btn-secondary" onclick="app.logout()">Logout</button>
            `;
        }
    }

    updateUIForLoggedOutUser() {
        const navAuth = document.querySelector('.nav-auth');
        if (navAuth) {
            navAuth.innerHTML = `
                <button class="btn-secondary" onclick="openModal('loginModal')">Login</button>
                <button class="btn-primary" onclick="openModal('registerModal')">Register</button>
            `;
        }

        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent) {
            dashboardContent.innerHTML = `
                <div class="dashboard-login-prompt">
                    <i class="fas fa-lock"></i>
                    <h3>Access Your Dashboard</h3>
                    <p>Login to view personalized insights and manage your activities</p>
                    <button class="btn-primary" onclick="openModal('loginModal')">Login to Continue</button>
                </div>
            `;
        }
    }

    // Dashboard
    initDashboard() {
        if (this.currentUser) {
            this.loadDashboard();
        }
    }

    async loadDashboard() {
        if (!this.authToken) return;

        try {
            const response = await fetch(`${this.API_BASE}/dashboard`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderDashboard(data);
            } else {
                console.error('Dashboard load failed');
            }
        } catch (error) {
            console.error('Dashboard error:', error);
        }
    }

    renderDashboard(data) {
        const dashboardContent = document.getElementById('dashboard-content');
        if (!dashboardContent) return;

        let dashboardHTML = `
            <div class="dashboard-welcome">
                <h3>Welcome back, ${data.user.username}!</h3>
                <p>User Type: ${data.user.user_type.charAt(0).toUpperCase() + data.user.user_type.slice(1)}</p>
            </div>
        `;

        if (data.user.user_type === 'farmer') {
            dashboardHTML += `
                <div class="dashboard-section">
                    <h4>Recent Crop Predictions</h4>
                    <div class="predictions-grid">
                        ${data.recent_predictions ? data.recent_predictions.map(p => `
                            <div class="prediction-card">
                                <h5>${p.crop_type}</h5>
                                <p>Confidence: ${Math.round(p.confidence * 100)}%</p>
                                <small>${new Date(p.created_at).toLocaleDateString()}</small>
                            </div>
                        `).join('') : '<p>No predictions yet. Try our crop predictor!</p>'}
                    </div>
                </div>
            `;
        } else if (data.user.user_type === 'donor') {
            dashboardHTML += `
                <div class="dashboard-section">
                    <h4>Donation Summary</h4>
                    <div class="donation-stats">
                        <div class="stat-card">
                            <h5>Total Donated</h5>
                            <p class="stat-value">$${data.total_donated || 0}</p>
                        </div>
                        <div class="stat-card">
                            <h5>Donations Made</h5>
                            <p class="stat-value">${data.donation_count || 0}</p>
                        </div>
                    </div>
                </div>
            `;
        } else {
            dashboardHTML += `
                <div class="dashboard-section">
                    <h4>Recent Nutrition Analyses</h4>
                    <div class="analyses-grid">
                        ${data.recent_analyses ? data.recent_analyses.map(a => `
                            <div class="analysis-card">
                                <p>${a.meal_description.substring(0, 50)}...</p>
                                <small>${new Date(a.created_at).toLocaleDateString()}</small>
                            </div>
                        `).join('') : '<p>No analyses yet. Try our nutrition analyzer!</p>'}
                    </div>
                </div>
            `;
        }

        dashboardContent.innerHTML = dashboardHTML;
    }

    // AI Features
    async analyzeNutrition() {
        if (!this.authToken) {
            this.showNotification('Please login to use this feature', 'warning');
            this.openModal('loginModal');
            return;
        }

        const mealDescription = document.getElementById('mealDescription').value;
        if (!mealDescription.trim()) {
            this.showNotification('Please describe your meal', 'error');
            return;
        }

        try {
            this.setButtonLoading('analyzeBtn', true);
            
            const response = await fetch(`${this.API_BASE}/nutrition/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify({ meal_description: mealDescription })
            });

            const data = await response.json();

            if (response.ok) {
                this.displayNutritionResults(data.analysis);
                this.showNotification('Nutrition analysis complete!', 'success');
            } else {
                this.showNotification(data.error || 'Analysis failed', 'error');
            }
        } catch (error) {
            console.error('Nutrition analysis error:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            this.setButtonLoading('analyzeBtn', false);
        }
    }

    displayNutritionResults(analysis) {
        const resultsDiv = document.getElementById('nutritionResults');
        if (!resultsDiv) return;

        const resultsHTML = `
            <div class="nutrition-overview">
                <div class="nutrition-score">
                    <h4>Health Score: ${analysis.health_score}/10</h4>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${analysis.health_score * 10}%"></div>
                    </div>
                </div>
                <div class="nutrition-calories">
                    <h5>Estimated Calories: ${analysis.calories || 'N/A'}</h5>
                </div>
            </div>
            
            <div class="nutrition-macros">
                <h5>Macronutrients</h5>
                <div class="macro-grid">
                    ${analysis.macronutrients ? Object.entries(analysis.macronutrients).map(([key, value]) => `
                        <div class="macro-item">
                            <span class="macro-label">${key.charAt(0).toUpperCase() + key.slice(1)}</span>
                            <span class="macro-value">${value}</span>
                        </div>
                    `).join('') : '<p>Macronutrient data unavailable</p>'}
                </div>
            </div>

            ${analysis.deficiencies && analysis.deficiencies.length > 0 ? `
                <div class="nutrition-deficiencies">
                    <h5>Potential Deficiencies</h5>
                    <ul>
                        ${analysis.deficiencies.map(def => `<li>${def}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            ${analysis.recommendations && analysis.recommendations.length > 0 ? `
                <div class="nutrition-recommendations">
                    <h5>Recommendations</h5>
                    <ul>
                        ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;

        resultsDiv.innerHTML = resultsHTML;
        resultsDiv.style.display = 'block';
    }

    async predictCrop(e) {
        e.preventDefault();
        
        if (!this.authToken) {
            this.showNotification('Please login to use this feature', 'warning');
            this.openModal('loginModal');
            return;
        }

        if (this.currentUser.user_type !== 'farmer') {
            this.showNotification('This feature is only available for farmers', 'warning');
            return;
        }

        const cropType = document.getElementById('cropType').value;
        const location = document.getElementById('cropLocation').value;
        const soilType = document.getElementById('soilType').value;
        const soilPH = document.getElementById('soilPH').value;
        const rainfall = document.getElementById('rainfall').value;

        if (!cropType || !location || !soilType) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        try {
            this.setLoading(true);
            
            const soilData = {
                type: soilType,
                ph: parseFloat(soilPH) || 6.5,
                organic_matter: 'medium' // Default value
            };

            const weatherData = {
                expected_rainfall: parseInt(rainfall) || 800,
                temperature_range: '20-30°C' // Default value
            };

            const response = await fetch(`${this.API_BASE}/crops/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify({
                    crop_type: cropType,
                    location: location,
                    soil_data: soilData,
                    weather_data: weatherData
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.displayCropResults(data.prediction);
                this.showNotification('Crop prediction complete!', 'success');
            } else {
                this.showNotification(data.error || 'Prediction failed', 'error');
            }
        } catch (error) {
            console.error('Crop prediction error:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    displayCropResults(prediction) {
        const resultsDiv = document.getElementById('cropResults');
        if (!resultsDiv) return;

        const resultsHTML = `
            <div class="prediction-overview">
                <div class="prediction-confidence">
                    <h4>Confidence: ${prediction.confidence || 0}%</h4>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${prediction.confidence || 0}%"></div>
                    </div>
                </div>
            </div>
            
            <div class="prediction-details">
                <div class="prediction-item">
                    <h5>Expected Yield</h5>
                    <p>${prediction.yield_prediction || 'Data unavailable'}</p>
                </div>
                
                <div class="prediction-item">
                    <h5>Best Planting Time</h5>
                    <p>${prediction.planting_time || 'Consult local agricultural extension'}</p>
                </div>
            </div>

            ${prediction.risk_factors && prediction.risk_factors.length > 0 ? `
                <div class="prediction-risks">
                    <h5>Risk Factors</h5>
                    <ul>
                        ${prediction.risk_factors.map(risk => `<li>${risk}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            ${prediction.recommendations && prediction.recommendations.length > 0 ? `
                <div class="prediction-recommendations">
                    <h5>Optimization Tips</h5>
                    <ul>
                        ${prediction.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;

        resultsDiv.innerHTML = resultsHTML;
        resultsDiv.style.display = 'block';
    }

    // Payment Integration
    async handleDonation(e) {
        e.preventDefault();
        
        if (!this.authToken) {
            this.showNotification('Please login to make a donation', 'warning');
            this.openModal('loginModal');
            return;
        }

        const amount = document.getElementById('donationAmount').value;
        const phone = document.getElementById('donationPhone').value;
        const purpose = document.getElementById('donationPurpose').value;

        if (!amount || !phone || !purpose) {
            this.showNotification('Please fill in all fields', 'error');
            return;
        }

        if (parseFloat(amount) < 1) {
            this.showNotification('Minimum donation amount is 1 KES', 'error');
            return;
        }

        if (!this.validatePhone(phone)) {
            this.showNotification('Please enter a valid phone number', 'error');
            return;
        }

        try {
            this.setLoading(true);
            
            const response = await fetch(`${this.API_BASE}/donate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify({
                    amount: parseFloat(amount),
                    phone_number: phone,
                    purpose: purpose
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showNotification('Donation initiated! Please check your phone for payment prompt.', 'success');
                this.closeModal('donationModal');
                
                if (data.payment_url) {
                    window.open(data.payment_url, '_blank');
                }
            } else {
                this.showNotification(data.error || 'Donation failed', 'error');
            }
        } catch (error) {
            console.error('Donation error:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    // Modal Management
    initModals() {
        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal[style*="block"]');
                if (openModal) {
                    this.closeModal(openModal.id);
                }
            }
        });
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }

    switchModal(fromModalId, toModalId) {
        this.closeModal(fromModalId);
        this.openModal(toModalId);
    }

    // Scroll Effects
    initScrollEffects() {
        // Intersection Observer for animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observe feature cards
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(card);
        });
    }

    // Utility Functions
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    validatePhone(phone) {
        const re = /^[0-9+\-\s()]{10,15}$/;
        return re.test(phone);
    }

    setLoading(isLoading) {
        this.isLoading = isLoading;
        const loadingElements = document.querySelectorAll('.btn-primary, .btn-secondary');
        loadingElements.forEach(btn => {
            if (isLoading) {
                btn.classList.add('loading');
                btn.disabled = true;
            } else {
                btn.classList.remove('loading');
                btn.disabled = false;
            }
        });
    }

    setButtonLoading(buttonId, isLoading) {
        const button = document.getElementById(buttonId);
        if (button) {
            if (isLoading) {
                button.classList.add('loading');
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            } else {
                button.classList.remove('loading');
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-brain"></i> Analyze Nutrition';
            }
        }
    }

    // Notification System
    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Quick Action Functions (called from HTML)
    openNutritionAnalyzer() {
        this.openModal('nutritionModal');
    }

    openCropPredictor() {
        this.openModal('cropModal');
    }

    openDonationPortal() {
        this.openModal('donationModal');
    }

    openCommunityHub() {
        this.showNotification('Community hub coming soon!', 'info');
    }

    initiateDonation(amount, purpose) {
        if (!this.authToken) {
            this.showNotification('Please login to make a donation', 'warning');
            this.openModal('loginModal');
            return;
        }

        document.getElementById('donationAmount').value = amount;
        document.getElementById('donationPurpose').value = purpose;
        this.openModal('donationModal');
    }

    initiateCustomDonation() {
        const amount = document.getElementById('customAmount').value;
        const purpose = document.getElementById('customPurpose').value || 'General donation';

        if (!amount || parseFloat(amount) < 1) {
            this.showNotification('Please enter a valid amount', 'error');
            return;
        }

        this.initiateDonation(amount, purpose);
    }
}

// Global functions for HTML onclick handlers
function openModal(modalId) {
    app.openModal(modalId);
}

function closeModal(modalId) {
    app.closeModal(modalId);
}

function switchModal(fromModalId, toModalId) {
    app.switchModal(fromModalId, toModalId);
}

function scrollToSection(sectionId) {
    app.scrollToSection(sectionId);
}

function openNutritionAnalyzer() {
    app.openNutritionAnalyzer();
}

function openCropPredictor() {
    app.openCropPredictor();
}

function openDonationPortal() {
    app.openDonationPortal();
}

function openCommunityHub() {
    app.openCommunityHub();
}

function initiateDonation(amount, purpose) {
    app.initiateDonation(amount, purpose);
}

function initiateCustomDonation() {
    app.initiateCustomDonation();
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NutriGuardApp();
});

// Service Worker Registration (for PWA capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}