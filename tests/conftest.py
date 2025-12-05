"""
Pytest configuration and fixtures for all tests.

This file provides common fixtures for Flask app context and database setup.
"""
import pytest
from app import create_app
from models import db as _db


@pytest.fixture(scope='session')
def app():
    """
    Create Flask application for testing.
    
    Scope: session - created once per test session
    """
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    return app


@pytest.fixture(scope='function')
def app_context(app):
    """
    Create Flask application context for each test.
    
    Scope: function - created for each test function
    """
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def db(app_context):
    """
    Create database tables for each test.
    
    Scope: function - fresh database for each test
    """
    _db.create_all()
    yield _db
    _db.session.remove()
    _db.drop_all()


@pytest.fixture(scope='function')
def session(db):
    """
    Create database session for each test.
    
    Scope: function - fresh session for each test
    """
    yield db.session
