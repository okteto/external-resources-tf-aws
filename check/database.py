import os
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True)
    name = Column(String)
    normalized_name = Column(String, index=True)  # For smart grouping
    quantity = Column(Integer, default=1)
    price = Column(Float)
    ready = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True, index=True)
    total = Column(Float)
    receipt_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    items_json = Column(Text)  # Store complete item data as JSON backup

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://oktaco:oktaco@postgres:5432/oktaco")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_stats():
    """Get database statistics for dashboard"""
    async with async_session() as session:
        from sqlalchemy import func, text
        
        # Total orders
        total_orders = await session.execute(
            func.count(Order.id)
        )
        total_orders = total_orders.scalar()
        
        # Total revenue
        total_revenue = await session.execute(
            func.sum(Order.total)
        )
        total_revenue = total_revenue.scalar() or 0
        
        # Orders today
        orders_today = await session.execute(
            text("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURRENT_DATE")
        )
        orders_today = orders_today.scalar()
        
        # Most popular items (using normalized names)
        popular_items = await session.execute(
            text("""
                SELECT normalized_name, COUNT(*) as count, SUM(quantity) as total_quantity
                FROM order_items 
                GROUP BY normalized_name 
                ORDER BY total_quantity DESC 
                LIMIT 10
            """)
        )
        popular_items = popular_items.fetchall()
        
        # Recent orders
        recent_orders = await session.execute(
            text("""
                SELECT id, total, created_at 
                FROM orders 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
        )
        recent_orders = recent_orders.fetchall()
        
        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "orders_today": orders_today,
            "popular_items": [
                {"name": item.normalized_name, "count": item.count, "total_quantity": item.total_quantity}
                for item in popular_items
            ],
            "recent_orders": [
                {"id": order.id, "total": order.total, "created_at": order.created_at.isoformat()}
                for order in recent_orders
            ]
        }