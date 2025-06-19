import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError

# Import the app and related functions
from main import app, upload_receipt, Check, Item

client = TestClient(app)

@pytest.fixture
def sample_check():
    return Check(
        orderId="test-order-123",
        items=[
            Item(name="Taco", price=4.0, ready=True),
            Item(name="Burrito", price=7.0, ready=True)
        ],
        total=11.0,
        url="/checks/test-order-123/receipt"
    )

@pytest.fixture
def sample_check_data():
    return {
        "orderId": "test-order-456",
        "items": [
            {"name": "Quesadilla", "ready": True},
            {"name": "Nachos", "ready": True}
        ]
    }

class TestHealthEndpoint:
    def test_healthz_endpoint(self):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"message": "Check please 🫰!"}

class TestCheckModel:
    def test_item_model_defaults(self):
        item = Item(name="Taco")
        assert item.name == "Taco"
        assert item.price == 0
        assert item.ready == False

    def test_item_model_with_values(self):
        item = Item(name="Burrito", price=5.5, ready=True)
        assert item.name == "Burrito"
        assert item.price == 5.5
        assert item.ready == True

    def test_check_model_defaults(self):
        check = Check(orderId="test-123", items=[])
        assert check.orderId == "test-123"
        assert check.items == []
        assert check.total == 0
        assert check.url == ""

class TestUploadReceipt:
    @patch('main.s3')
    def test_upload_receipt_success(self, mock_s3):
        # Mock successful upload
        mock_s3.upload_fileobj.return_value = None
        
        # Set environment variable
        os.environ['BUCKET'] = 'test-bucket'
        
        result = upload_receipt("test-order-123", "Test receipt content")
        
        assert result == "/checks/test-order-123/receipt"
        mock_s3.upload_fileobj.assert_called_once()
        
        # Clean up
        del os.environ['BUCKET']

    @patch('main.s3')
    def test_upload_receipt_failure(self, mock_s3):
        # Mock S3 client error
        mock_s3.upload_fileobj.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            operation_name='upload_fileobj'
        )
        
        os.environ['BUCKET'] = 'test-bucket'
        
        result = upload_receipt("test-order-123", "Test receipt content")
        
        assert result == ""
        
        # Clean up
        del os.environ['BUCKET']

class TestGetChecks:
    def test_get_checks_empty(self):
        # Clear the checks dictionary
        from main import checks
        checks.clear()
        
        response = client.get("/checks")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_checks_with_data(self, sample_check):
        from main import checks
        checks.clear()
        checks["test-order-123"] = sample_check
        
        response = client.get("/checks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["orderId"] == "test-order-123"

class TestPrepareCheck:
    @patch('main.upload_receipt')
    @patch('main.template')
    def test_prepare_check_success(self, mock_template, mock_upload):
        from main import checks
        checks.clear()
        
        # Mock template rendering and upload
        mock_template.render.return_value = "Rendered receipt"
        mock_upload.return_value = "/checks/test-order-456/receipt"
        
        check_data = {
            "orderId": "test-order-456",
            "items": [
                {"name": "Taco", "ready": True},
                {"name": "Burrito", "ready": True}
            ]
        }
        
        response = client.post("/checks", json=check_data)
        assert response.status_code == 200
        
        # Verify check was stored
        assert "test-order-456" in checks
        stored_check = checks["test-order-456"]
        assert stored_check.orderId == "test-order-456"
        assert len(stored_check.items) == 2
        assert stored_check.items[0].price == 4  # len("Taco")
        assert stored_check.items[1].price == 7  # len("Burrito")
        assert stored_check.total == 11
        assert stored_check.url == "/checks/test-order-456/receipt"

    def test_prepare_check_price_calculation(self):
        from main import checks
        checks.clear()
        
        with patch('main.upload_receipt') as mock_upload, \
             patch('main.template') as mock_template:
            
            mock_template.render.return_value = "Receipt"
            mock_upload.return_value = "/checks/test/receipt"
            
            check_data = {
                "orderId": "test-price-calc",
                "items": [
                    {"name": "A", "ready": True},      # price = 1
                    {"name": "BB", "ready": True},     # price = 2
                    {"name": "CCC", "ready": True}     # price = 3
                ]
            }
            
            response = client.post("/checks", json=check_data)
            assert response.status_code == 200
            
            stored_check = checks["test-price-calc"]
            assert stored_check.total == 6  # 1 + 2 + 3

class TestGetCheck:
    def test_get_check_exists(self, sample_check):
        from main import checks
        checks.clear()
        checks["test-order-123"] = sample_check
        
        response = client.get("/checks/test-order-123")
        assert response.status_code == 200
        data = response.json()
        assert data["orderId"] == "test-order-123"

    def test_get_check_not_found(self):
        from main import checks
        checks.clear()
        
        response = client.get("/checks/nonexistent-order")
        assert response.status_code == 404
        assert "Check not found" in response.json()["detail"]

class TestGetReceipt:
    @patch('main.s3')
    @patch('main.s3Bucket', 'test-bucket')
    def test_get_receipt_success(self, mock_s3):
        # Mock S3 response
        mock_body = MagicMock()
        mock_body.iter_chunks.return_value = iter([b"Receipt content"])
        mock_s3.get_object.return_value = {"Body": mock_body}
        
        response = client.get("/checks/test-order-123/receipt")
        assert response.status_code == 200
        
        mock_s3.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test-order-123.txt'
        )

    @patch('main.s3')
    def test_get_receipt_not_found(self, mock_s3):
        # Mock S3 404 error
        mock_s3.get_object.side_effect = ClientError(
            error_response={'Error': {'Code': '404', 'Message': 'Not Found'}},
            operation_name='get_object'
        )
        
        os.environ['BUCKET'] = 'test-bucket'
        
        response = client.get("/checks/nonexistent-order/receipt")
        assert response.status_code == 404
        assert "Receipt not found" in response.json()["detail"]
        
        # Clean up
        del os.environ['BUCKET']

    @patch('main.s3')
    def test_get_receipt_other_error(self, mock_s3):
        # Mock other S3 error
        mock_s3.get_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            operation_name='get_object'
        )
        
        os.environ['BUCKET'] = 'test-bucket'
        
        with pytest.raises(ClientError):
            client.get("/checks/test-order/receipt")
        
        # Clean up
        del os.environ['BUCKET']

class TestPayCheck:
    def test_pay_check_success(self, sample_check):
        from main import checks
        checks.clear()
        checks["test-order-123"] = sample_check
        
        response = client.delete("/checks/test-order-123")
        assert response.status_code == 200
        
        # Verify check was removed
        assert "test-order-123" not in checks

    def test_pay_check_not_found(self):
        from main import checks
        checks.clear()
        
        response = client.delete("/checks/nonexistent-order")
        assert response.status_code == 404
        assert "Check not found" in response.json()["detail"]

class TestIntegration:
    def test_full_check_workflow(self):
        """Test the complete workflow: create check, get check, get receipt, pay check"""
        from main import checks
        checks.clear()
        
        with patch('main.upload_receipt') as mock_upload, \
             patch('main.template') as mock_template, \
             patch('main.s3') as mock_s3, \
             patch('main.s3Bucket', 'test-bucket'):
            
            # Setup mocks
            mock_template.render.return_value = "Test receipt content"
            mock_upload.return_value = "/checks/workflow-test/receipt"
            
            mock_body = MagicMock()
            mock_body.iter_chunks.return_value = iter([b"Test receipt content"])
            mock_s3.get_object.return_value = {"Body": mock_body}
            
            # 1. Create check
            check_data = {
                "orderId": "workflow-test",
                "items": [{"name": "Test Item", "ready": True}]
            }
            
            response = client.post("/checks", json=check_data)
            assert response.status_code == 200
            
            # 2. Get check
            response = client.get("/checks/workflow-test")
            assert response.status_code == 200
            data = response.json()
            assert data["orderId"] == "workflow-test"
            assert data["total"] == 9  # len("Test Item")
            
            # 3. Get receipt
            response = client.get("/checks/workflow-test/receipt")
            assert response.status_code == 200
            
            # 4. Pay check (delete)
            response = client.delete("/checks/workflow-test")
            assert response.status_code == 200
            
            # 5. Verify check is gone
            response = client.get("/checks/workflow-test")
            assert response.status_code == 404