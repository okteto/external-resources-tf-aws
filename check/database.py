import os
import re
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:oktaco123@localhost:5432/oktacodb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    total = Column(Float)
    receipt_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to items
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    name = Column(String)
    normalized_name = Column(String)  # For analytics
    quantity = Column(Integer, default=1)
    price = Column(Float)
    ready = Column(Boolean, default=False)
    
    # Relationship to order
    order = relationship("Order", back_populates="items")

# Item normalization functions
def extract_quantity_and_name(item_name: str) -> tuple[int, str]:
    """Extract quantity and clean name from item string."""
    # Remove extra spaces and convert to lowercase for processing
    clean_name = item_name.strip().lower()
    
    # Pattern to match numbers at the start (e.g., "2 tacos", "3x pizza")
    quantity_patterns = [
        r'^(\d+)x?\s+(.+)$',  # "2 tacos" or "2x tacos"
        r'^(\d+)\s*(.+)$',    # "2tacos"
    ]
    
    for pattern in quantity_patterns:
        match = re.match(pattern, clean_name)
        if match:
            quantity = int(match.group(1))
            name = match.group(2).strip()
            return quantity, name
    
    # If no quantity found, check for quantity words
    quantity_words = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    
    words = clean_name.split()
    if len(words) > 1 and words[0] in quantity_words:
        return quantity_words[words[0]], ' '.join(words[1:])
    
    return 1, clean_name

def normalize_item_name(name: str) -> str:
    """Normalize item names for consistent analytics."""
    # Convert to lowercase and remove extra spaces
    normalized = name.lower().strip()
    
    # Remove common prefixes
    prefixes_to_remove = ['the ', 'a ', 'an ']
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
    
    # Handle plurals - simple approach for common food items
    plural_mappings = {
        'tacos': 'taco',
        'burritos': 'burrito',
        'quesadillas': 'quesadilla',
        'nachos': 'nacho',
        'pizzas': 'pizza',
        'burgers': 'burger',
        'fries': 'fry',
        'wings': 'wing',
        'drinks': 'drink',
        'sodas': 'soda',
        'beers': 'beer'
    }
    
    # Check for exact plural matches
    if normalized in plural_mappings:
        normalized = plural_mappings[normalized]
    else:
        # Generic plural handling (remove 's' if ends with 's' and length > 3)
        if normalized.endswith('s') and len(normalized) > 3:
            # Don't remove 's' from words that naturally end with 's'
            non_plural_s_endings = ['glass', 'pass', 'grass', 'class']
            if not any(normalized.endswith(ending) for ending in non_plural_s_endings):
                normalized = normalized[:-1]
    
    # Remove special characters and normalize spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)