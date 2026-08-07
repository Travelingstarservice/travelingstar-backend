"""
Pytest configuration and fixtures for backend tests.
"""

import pytest
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    from app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['ADMIN_PIN'] = '1234'
    
    with app.app_context():
        from extensions import db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the application."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Create authentication headers for test requests."""
    # Register and login a test user
    client.post('/api/auth/register', json={'password': '5678'})
    response = client.post('/api/auth/login', json={'password': '5678'})
    token = response.json['token']
    
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_headers(client):
    """Create admin authentication headers for test requests."""
    # Login as admin
    response = client.post('/api/auth/login', json={'password': '1234'})
    token = response.json['token']
    
    return {'Authorization': f'Bearer {token}'}