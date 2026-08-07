import os

# Admin authentication - use same env var as app.py for consistency
ADMIN_PASSWORD = os.getenv('ADMIN_PIN', '1234')

# Database configuration - will be overridden by DATABASE_URL env var if set
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///travelingstar.db')
