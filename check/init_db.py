#!/usr/bin/env python3
"""Database initialization script for the check service."""

import sys
import os
from database import init_db, engine, SessionLocal
from sqlalchemy import text

def create_database_if_not_exists():
    """Create the database tables if they don't exist."""
    try:
        print("Initializing database...")
        init_db()
        print("Database tables created successfully!")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def test_database_connection():
    """Test the database connection."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def populate_sample_data():
    """Populate sample data for testing (optional)."""
    from database import Order, OrderItem
    from datetime import datetime, timedelta
    
    try:
        db = SessionLocal()
        
        # Check if we already have data
        if db.query(Order).count() > 0:
            print("Sample data already exists, skipping population.")
            return True
        
        # Create sample orders
        sample_orders = [
            {
                "order_id": "SAMPLE-001",
                "total": 25.50,
                "items": [
                    {"name": "2 tacos", "normalized_name": "taco", "quantity": 2, "price": 12.0},
                    {"name": "BURRITO", "normalized_name": "burrito", "quantity": 1, "price": 13.50}
                ]
            },
            {
                "order_id": "SAMPLE-002", 
                "total": 18.00,
                "items": [
                    {"name": "quesadilla", "normalized_name": "quesadilla", "quantity": 1, "price": 10.0},
                    {"name": "nachos", "normalized_name": "nacho", "quantity": 1, "price": 8.0}
                ]
            },
            {
                "order_id": "SAMPLE-003",
                "total": 31.00,
                "items": [
                    {"name": "3x tacos", "normalized_name": "taco", "quantity": 3, "price": 18.0},
                    {"name": "pizza", "normalized_name": "pizza", "quantity": 1, "price": 13.0}
                ]
            }
        ]
        
        for i, order_data in enumerate(sample_orders):
            # Create order with different timestamps
            db_order = Order(\n                order_id=order_data["order_id"],\n                total=order_data["total"],\n                receipt_url=f"/checks/{order_data['order_id']}/receipt",\n                created_at=datetime.utcnow() - timedelta(hours=i*2)\n            )\n            db.add(db_order)\n            db.flush()\n            \n            # Add items\n            for item_data in order_data["items"]:\n                db_item = OrderItem(\n                    order_id=db_order.id,\n                    name=item_data["name"],\n                    normalized_name=item_data["normalized_name"],\n                    quantity=item_data["quantity"],\n                    price=item_data["price"],\n                    ready=True\n                )\n                db.add(db_item)\n        \n        db.commit()\n        print("Sample data populated successfully!")\n        return True\n        \n    except Exception as e:\n        print(f"Error populating sample data: {e}")\n        db.rollback()\n        return False\n    finally:\n        db.close()\n\ndef main():\n    """Main initialization function."""\n    print("Starting database initialization...")\n    \n    # Test connection first\n    if not test_database_connection():\n        print("Cannot proceed without database connection.")\n        sys.exit(1)\n    \n    # Create tables\n    if not create_database_if_not_exists():\n        print("Failed to initialize database.")\n        sys.exit(1)\n    \n    # Populate sample data if requested\n    if len(sys.argv) > 1 and sys.argv[1] == "--sample-data":\n        if not populate_sample_data():\n            print("Failed to populate sample data, but database is ready.")\n    \n    print("Database initialization completed successfully!")\n\nif __name__ == "__main__":\n    main()