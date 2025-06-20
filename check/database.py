import os
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "checksdb")
DB_USER = os.getenv("DB_USER", "checksuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "checkspass123!")

# Remove port from host if present (RDS endpoints include port)
if ":" in DB_HOST:
    DB_HOST = DB_HOST.split(":")[0]

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_timeout=10,
    pool_recycle=3600,
    connect_args={"connect_timeout": 10}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class CheckDB(Base):
    __tablename__ = "checks"
    
    order_id = Column(String, primary_key=True, index=True)
    items = Column(JSON)  # Store items as JSON
    total = Column(Float)
    receipt_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="active")  # active, paid, cancelled

class CheckStatsDB(Base):
    __tablename__ = "check_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow)
    total_checks = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    avg_order_value = Column(Float, default=0.0)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()