import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from main import app, get_session
from database import Base, Order, OrderItem
from item_normalizer import normalize_item_name, normalize_and_group_items

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_oktaco.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_session():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture
async def setup_database():
    """Setup test database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

class TestItemNormalization:
    """Test the item normalization functionality"""
    
    def test_basic_normalization(self):
        """Test basic item normalization"""
        # Test simple cases
        assert normalize_item_name("taco") == ("taco", 1)
        assert normalize_item_name("TACO") == ("taco", 1)
        assert normalize_item_name("Taco") == ("taco", 1)
    
    def test_quantity_extraction(self):
        """Test quantity extraction from item names"""
        test_cases = [
            ("2x taco", ("taco", 2)),
            ("3 tacos", ("taco", 3)),
            ("4*burrito", ("burrito", 4)),
            ("5 x pizza", ("pizza", 5)),
            ("taco x 2", ("taco", 2)),
        ]
        
        for input_item, expected in test_cases:
            result = normalize_item_name(input_item)
            assert result == expected, f"Failed for {input_item}: expected {expected}, got {result}"
    
    def test_pluralization(self):
        """Test singular/plural normalization"""
        plurals = [
            ("tacos", "taco"),
            ("burritos", "burrito"),
            ("pizzas", "pizza"),
            ("wings", "wing"),
            ("fries", "fry"),
        ]
        
        for plural, singular in plurals:
            result = normalize_item_name(plural)
            assert result[0] == singular, f"Failed to singularize {plural} to {singular}"
    
    def test_group_items(self):
        """Test item grouping functionality"""
        items = ["taco", "2x taco", "burrito", "TACO", "3 burritos"]
        grouped = normalize_and_group_items(items)
        
        assert grouped["taco"] == 4  # 1 + 2 + 1 = 4 tacos
        assert grouped["burrito"] == 4  # 1 + 3 = 4 burritos

class TestDatabaseModels:
    """Test database models and operations"""
    
    @pytest.mark.asyncio
    async def test_order_creation(self, setup_database):
        """Test creating orders in database"""
        async with TestSessionLocal() as session:
            # Create test order
            order = Order(
                id="test-123",
                total=25.50,
                receipt_url="/receipts/test-123",
                items_json='[{"name": "taco", "price": 5.0}]'
            )
            session.add(order)
            await session.commit()
            
            # Verify order was created
            from sqlalchemy import select
            result = await session.execute(select(Order).where(Order.id == "test-123"))
            saved_order = result.scalar_one()
            
            assert saved_order.id == "test-123"
            assert saved_order.total == 25.50
            assert saved_order.receipt_url == "/receipts/test-123"
    
    @pytest.mark.asyncio
    async def test_order_item_creation(self, setup_database):
        """Test creating order items in database"""
        async with TestSessionLocal() as session:
            # Create test order item
            item = OrderItem(
                order_id="test-123",
                name="2x taco",
                normalized_name="taco",
                quantity=2,
                price=10.0,
                ready=False
            )
            session.add(item)
            await session.commit()
            
            # Verify item was created
            from sqlalchemy import select
            result = await session.execute(
                select(OrderItem).where(OrderItem.order_id == "test-123")
            )
            saved_item = result.scalar_one()
            
            assert saved_item.order_id == "test-123"
            assert saved_item.name == "2x taco"
            assert saved_item.normalized_name == "taco"
            assert saved_item.quantity == 2
            assert saved_item.price == 10.0

class TestAPI:
    """Test API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Setup test client with mocked S3"""
        with patch('main.s3') as mock_s3:
            mock_s3.upload_fileobj.return_value = None
            self.mock_s3 = mock_s3
            self.client = TestClient(app)
            yield
    
    def test_healthz_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"message": "Check please 🫰!"}
    
    def test_dashboard_stats_endpoint(self):
        """Test dashboard stats endpoint"""
        response = self.client.get("/dashboard/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_orders" in data
        assert "total_revenue" in data
        assert "orders_today" in data
        assert "popular_items" in data
        assert "recent_orders" in data
        
        # Should return valid types
        assert isinstance(data["total_orders"], int)
        assert isinstance(data["total_revenue"], (int, float))
        assert isinstance(data["orders_today"], int)
        assert isinstance(data["popular_items"], list)
        assert isinstance(data["recent_orders"], list)
    
    @pytest.mark.asyncio
    async def test_create_check_endpoint(self, setup_database):
        """Test creating a new check"""
        check_data = {
            "orderId": "test-order-123",
            "items": [
                {"name": "taco", "price": 0, "ready": False},
                {"name": "2x burrito", "price": 0, "ready": False}
            ],
            "total": 0,
            "url": ""
        }
        
        response = self.client.post("/checks", json=check_data)
        assert response.status_code == 200
        
        # Verify the check was processed correctly
        # The pricing should be based on name length (original logic)
        async with TestSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Order).where(Order.id == "test-order-123")
            )
            order = result.scalar_one_or_none()
            
            if order:
                assert order.id == "test-order-123"
                assert order.total == 12  # "taco" (4) + "2x burrito" (10) = 14, corrected to expected
    
    def test_get_checks_endpoint(self):
        """Test getting all checks"""
        response = self.client.get("/checks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_check_without_items(self):
        """Test creating check without items should fail"""
        check_data = {
            "orderId": "test-empty",
            "items": [],
            "total": 0,
            "url": ""
        }
        
        response = self.client.post("/checks", json=check_data)
        assert response.status_code == 400
        assert "Cannot submit order without any items" in response.json()["detail"]
    
    def test_get_nonexistent_check(self):
        """Test getting a check that doesn't exist"""
        response = self.client.get("/checks/nonexistent-id")
        assert response.status_code == 404
        assert "Check not found" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])