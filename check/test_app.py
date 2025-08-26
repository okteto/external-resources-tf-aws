#!/usr/bin/env python3
"""Comprehensive tests for the check service with database and dashboard functionality."""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from main import app
from database import Base, Order, OrderItem, extract_quantity_and_name, normalize_item_name, get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """Create test client with test database."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Test item normalization functions
class TestItemNormalization:
    """Test the smart item normalization logic."""
    
    def test_extract_quantity_basic(self):
        """Test basic quantity extraction."""
        assert extract_quantity_and_name("2 tacos") == (2, "tacos")
        assert extract_quantity_and_name("3x pizza") == (3, "pizza")
        assert extract_quantity_and_name("1 burrito") == (1, "burrito")
        assert extract_quantity_and_name("tacos") == (1, "tacos")
    
    def test_extract_quantity_edge_cases(self):
        """Test quantity extraction edge cases."""
        assert extract_quantity_and_name("10 nachos") == (10, "nachos")
        assert extract_quantity_and_name("2tacos") == (2, "tacos")
        assert extract_quantity_and_name("  3  burritos  ") == (3, "burritos")
        assert extract_quantity_and_name("") == (1, "")
    
    def test_extract_quantity_words(self):
        """Test word-based quantity extraction."""
        assert extract_quantity_and_name("two tacos") == (2, "tacos")
        assert extract_quantity_and_name("five pizzas") == (5, "pizzas")
        assert extract_quantity_and_name("one burrito") == (1, "burrito")
    
    def test_normalize_item_name_case(self):
        """Test case normalization."""
        assert normalize_item_name("TACO") == "taco"
        assert normalize_item_name("Burrito") == "burrito"
        assert normalize_item_name("QUESADILLA") == "quesadilla"
    
    def test_normalize_item_name_plurals(self):
        """Test plural normalization."""
        assert normalize_item_name("tacos") == "taco"
        assert normalize_item_name("burritos") == "burrito"
        assert normalize_item_name("pizzas") == "pizza"
        assert normalize_item_name("nachos") == "nacho"
    
    def test_normalize_item_name_prefixes(self):
        """Test prefix removal."""
        assert normalize_item_name("the taco") == "taco"
        assert normalize_item_name("a burrito") == "burrito"
        assert normalize_item_name("an order") == "order"
    
    def test_normalize_item_name_special_chars(self):
        """Test special character handling."""
        assert normalize_item_name("taco!") == "taco"
        assert normalize_item_name("burrito@") == "burrito"
        assert normalize_item_name("nacho  supreme") == "nacho supreme"

# Test database operations
class TestDatabaseOperations:
    """Test database CRUD operations."""
    
    def test_create_order(self, db_session):
        """Test order creation."""
        order = Order(order_id="TEST-001", total=25.50)
        db_session.add(order)
        db_session.commit()
        
        retrieved_order = db_session.query(Order).filter_by(order_id="TEST-001").first()
        assert retrieved_order is not None
        assert retrieved_order.total == 25.50
    
    def test_create_order_with_items(self, db_session):
        """Test order creation with items."""
        order = Order(order_id="TEST-002", total=30.00)
        db_session.add(order)
        db_session.flush()
        
        item1 = OrderItem(
            order_id=order.id,
            name="2 tacos",
            normalized_name="taco",
            quantity=2,
            price=12.00
        )
        item2 = OrderItem(
            order_id=order.id,
            name="burrito",
            normalized_name="burrito",
            quantity=1,
            price=18.00
        )
        
        db_session.add(item1)
        db_session.add(item2)
        db_session.commit()
        
        retrieved_order = db_session.query(Order).filter_by(order_id="TEST-002").first()
        assert len(retrieved_order.items) == 2
        assert retrieved_order.items[0].normalized_name in ["taco", "burrito"]

# Test API endpoints
class TestAPIEndpoints:
    """Test the FastAPI endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert "Check please" in response.json()["message"]
    
    @patch('main.upload_receipt')
    def test_create_check(self, mock_upload, client):
        """Test check creation endpoint."""
        mock_upload.return_value = "/checks/TEST-001/receipt"
        
        check_data = {
            "orderId": "TEST-001",
            "items": [
                {"name": "2 tacos", "price": 0, "ready": False},
                {"name": "burrito", "price": 0, "ready": False}
            ],
            "total": 0,
            "url": ""
        }
        
        response = client.post("/checks", json=check_data)
        assert response.status_code == 200
        
        # Verify the order was created in database
        checks_response = client.get("/checks")
        assert checks_response.status_code == 200
        orders = checks_response.json()
        assert len(orders) == 1
        assert orders[0]["order_id"] == "TEST-001"
    
    def test_create_check_no_items(self, client):
        """Test check creation with no items fails."""
        check_data = {
            "orderId": "TEST-002",
            "items": [],
            "total": 0,
            "url": ""
        }
        
        response = client.post("/checks", json=check_data)
        assert response.status_code == 400
        assert "Cannot submit order without any items" in response.json()["detail"]

# Test Dashboard API endpoints
class TestDashboardAPI:
    """Test dashboard-specific API endpoints."""
    
    def test_dashboard_stats_empty(self, client):
        """Test dashboard stats with no orders."""
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_orders"] == 0
        assert stats["total_revenue"] == 0.0
        assert stats["average_order"] == 0.0
    
    @patch('main.upload_receipt')
    def test_popular_items_empty(self, mock_upload, client):
        """Test popular items with no orders."""
        response = client.get("/api/dashboard/popular-items")
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])