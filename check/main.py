import boto3
import os
import tempfile
import jinja2
import uvicorn
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional

from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from pydantic import BaseModel
from database import get_db, create_tables, CheckDB, CheckStatsDB

def normalize_item_name(item_name: str) -> str:
    """
    Normalize item names for consistent grouping by:
    1. Removing leading digits and spaces (e.g., "1 horchata water" -> "horchata water")
    2. Converting to lowercase for case-insensitive comparison
    3. Handling pluralization (e.g., "burritos" -> "burrito", "tacos" -> "taco")
    """
    # Remove leading digits and spaces
    normalized = re.sub(r'^\d+\s+', '', item_name).strip()
    
    # Convert to lowercase
    normalized = normalized.lower()
    
    # Handle pluralization - remove trailing 's' for common plural forms
    # Only remove 's' if word is longer than 3 characters to avoid issues with words like "chips"
    if len(normalized) > 3 and normalized.endswith('s'):
        # Handle common plural patterns
        if normalized.endswith('ies'):
            # e.g., "fries" -> "fry" (but we'll keep it simple and just remove 's')
            normalized = normalized[:-1]
        elif normalized.endswith('es') and len(normalized) > 4:
            # e.g., "tacos" -> "taco" (remove 's' only)
            normalized = normalized[:-1]
        elif not normalized.endswith(('ss', 'us', 'is')):
            # Remove trailing 's' but avoid words that naturally end in 's'
            # like "chips", "beans", "lettuce", etc.
            # Simple heuristic: if it doesn't end in double 's', 'us', or 'is'
            normalized = normalized[:-1]
    
    return normalized

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Oktaco Shop - Check Service", version="2.0.0")
env = jinja2.Environment(loader=jinja2.PackageLoader("main"), autoescape=jinja2.select_autoescape())
template = env.get_template("receipt.j2")

s3 = boto3.client('s3')
s3Bucket = os.getenv("BUCKET")

# Create database tables on startup
DATABASE_AVAILABLE = False
# Fallback in-memory storage when database is not available
memory_checks = {}

try:
    logger.info("Attempting to create database tables...")
    create_tables()
    logger.info("Database tables created successfully")
    DATABASE_AVAILABLE = True
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")
    # Continue without database for now
    logger.warning("Continuing without database functionality")
    DATABASE_AVAILABLE = False

class Item(BaseModel):
    name: str
    price: float | None = 0
    ready: bool | None = False

class Check(BaseModel):
    orderId: str
    items: List[Item]
    total: float | None = 0
    url: str | None = ""

class CheckResponse(BaseModel):
    orderId: str
    items: List[Item]
    total: float
    url: str
    created_at: datetime
    status: str

class DashboardStats(BaseModel):
    total_checks: int
    total_revenue: float
    avg_order_value: float
    checks_today: int
    revenue_today: float
    popular_items: List[dict]

def upload_receipt(orderId: str, receipt: str):
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(bytes(receipt, encoding='utf8'))
        tmp.seek(0)
        key = f'{orderId}.txt'
        try:
            s3.upload_fileobj(tmp, s3Bucket, key, ExtraArgs={'ContentType': 'text/file', 'ContentEncoding':'utf-8'})
            return f'/checks/{orderId}/receipt'
        except ClientError as e:
            print("failed to upload: ", e)
            return ""

def update_stats(db: Session):
    """Update daily statistics"""
    today = datetime.utcnow().date()
    
    # Get today's stats
    total_checks = db.query(CheckDB).filter(
        func.date(CheckDB.created_at) == today
    ).count()
    
    total_revenue = db.query(func.sum(CheckDB.total)).filter(
        func.date(CheckDB.created_at) == today
    ).scalar() or 0.0
    
    avg_order_value = total_revenue / total_checks if total_checks > 0 else 0.0
    
    # Update or create stats record
    stats = db.query(CheckStatsDB).filter(
        func.date(CheckStatsDB.date) == today
    ).first()
    
    if stats:
        stats.total_checks = total_checks
        stats.total_revenue = total_revenue
        stats.avg_order_value = avg_order_value
    else:
        stats = CheckStatsDB(
            date=datetime.utcnow(),
            total_checks=total_checks,
            total_revenue=total_revenue,
            avg_order_value=avg_order_value
        )
        db.add(stats)
    
    db.commit()

@app.get("/healthz")
async def healthz():
    return {"message": "Check please 🫰!"}

@app.get("/api/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    if not DATABASE_AVAILABLE:
        # Calculate stats from memory storage when database is not available
        if not memory_checks:
            return DashboardStats(
                total_checks=0,
                total_revenue=0.0,
                avg_order_value=0.0,
                checks_today=0,
                revenue_today=0.0,
                popular_items=[]
            )
        
        today = datetime.utcnow().date()
        checks_list = list(memory_checks.values())
        
        # Overall stats
        total_checks = len(checks_list)
        total_revenue = sum(check["total"] for check in checks_list)
        avg_order_value = total_revenue / total_checks if total_checks > 0 else 0.0
        
        # Today's stats
        checks_today = len([
            check for check in checks_list 
            if check["created_at"].date() == today
        ])
        
        revenue_today = sum(
            check["total"] for check in checks_list 
            if check["created_at"].date() == today
        )
        
        # Popular items (from last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_checks = [
            check for check in checks_list 
            if check["created_at"] >= thirty_days_ago
        ]
        
        item_counts = {}
        for check in recent_checks:
            for item in check["items"]:
                # Normalize item name for consistent grouping
                item_name = item['name']
                normalized_name = normalize_item_name(item_name)
                item_counts[normalized_name] = item_counts.get(normalized_name, 0) + 1
        
        # Sort by count (descending) then by name (ascending) for consistent ordering
        # Show top 6 items to include all current items
        popular_items = [
            {"name": name, "count": count} 
            for name, count in sorted(item_counts.items(), key=lambda x: (-x[1], x[0]))[:6]
        ]
        
        return DashboardStats(
            total_checks=total_checks,
            total_revenue=total_revenue,
            avg_order_value=avg_order_value,
            checks_today=checks_today,
            revenue_today=revenue_today,
            popular_items=popular_items
        )
    
    try:
        today = datetime.utcnow().date()
        
        # Overall stats
        total_checks = db.query(CheckDB).count()
        total_revenue = db.query(func.sum(CheckDB.total)).scalar() or 0.0
        avg_order_value = total_revenue / total_checks if total_checks > 0 else 0.0
        
        # Today's stats
        checks_today = db.query(CheckDB).filter(
            func.date(CheckDB.created_at) == today
        ).count()
        
        revenue_today = db.query(func.sum(CheckDB.total)).filter(
            func.date(CheckDB.created_at) == today
        ).scalar() or 0.0
        
        # Popular items (from last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_checks = db.query(CheckDB).filter(
            CheckDB.created_at >= thirty_days_ago
        ).all()
        
        item_counts = {}
        for check in recent_checks:
            for item in check.items:
                # Normalize item name for consistent grouping
                item_name = item['name']
                normalized_name = normalize_item_name(item_name)
                item_counts[normalized_name] = item_counts.get(normalized_name, 0) + 1
        
        # Sort by count (descending) then by name (ascending) for consistent ordering
        # Show top 6 items to include all current items
        popular_items = [
            {"name": name, "count": count} 
            for name, count in sorted(item_counts.items(), key=lambda x: (-x[1], x[0]))[:6]
        ]
        
        return DashboardStats(
            total_checks=total_checks,
            total_revenue=total_revenue,
            avg_order_value=avg_order_value,
            checks_today=checks_today,
            revenue_today=revenue_today,
            popular_items=popular_items
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        # Return empty stats on error
        return DashboardStats(
            total_checks=0,
            total_revenue=0.0,
            avg_order_value=0.0,
            checks_today=0,
            revenue_today=0.0,
            popular_items=[]
        )

@app.get("/checks", response_model=List[CheckResponse])
async def getChecks(
    status: Optional[str] = Query(None, description="Filter by status: active, paid, cancelled"),
    limit: int = Query(50, description="Number of checks to return"),
    offset: int = Query(0, description="Number of checks to skip"),
    db: Session = Depends(get_db)
):
    checks_list = []
    
    if DATABASE_AVAILABLE:
        try:
            query = db.query(CheckDB)
            
            if status:
                query = query.filter(CheckDB.status == status)
            
            checks = query.order_by(desc(CheckDB.created_at)).offset(offset).limit(limit).all()
            
            checks_list = [
                CheckResponse(
                    orderId=check.order_id,
                    items=check.items,
                    total=check.total,
                    url=check.receipt_url,
                    created_at=check.created_at,
                    status=check.status
                )
                for check in checks
            ]
        except Exception as e:
            logger.error(f"Error getting checks from database: {e}")
    
    # If database failed or not available, use memory storage
    if not checks_list and memory_checks:
        memory_list = list(memory_checks.values())
        
        # Filter by status if specified
        if status:
            memory_list = [check for check in memory_list if check["status"] == status]
        
        # Sort by created_at descending
        memory_list.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        memory_list = memory_list[offset:offset + limit]
        
        checks_list = [
            CheckResponse(
                orderId=check["orderId"],
                items=check["items"],
                total=check["total"],
                url=check["url"],
                created_at=check["created_at"],
                status=check["status"]
            )
            for check in memory_list
        ]
    
    return checks_list

@app.post("/checks", status_code=200)
async def prepare_check(check: Check, db: Session = Depends(get_db)):
    # Calculate price
    total = 0
    for i in range(len(check.items)):
        item = check.items[i]
        price = len(item.name)
        check.items[i].price = price
        total += price

    check.total = total
    receipt = template.render(total=check.total, items=check.items, check_id=check.orderId)
    check.url = upload_receipt(check.orderId, receipt)
    
    if DATABASE_AVAILABLE:
        try:
            # Check if order already exists
            existing_check = db.query(CheckDB).filter(CheckDB.order_id == check.orderId).first()
            if existing_check:
                raise HTTPException(status_code=400, detail="Check already exists")
            
            # Save to database
            db_check = CheckDB(
                order_id=check.orderId,
                items=[item.dict() for item in check.items],
                total=check.total,
                receipt_url=check.url,
                status="active"
            )
            
            db.add(db_check)
            db.commit()
            db.refresh(db_check)
            
            # Update statistics
            update_stats(db)
        except Exception as e:
            logger.error(f"Error saving check to database: {e}")
            # Fall back to memory storage
            memory_checks[check.orderId] = {
                "orderId": check.orderId,
                "items": [item.dict() for item in check.items],
                "total": check.total,
                "url": check.url,
                "created_at": datetime.utcnow(),
                "status": "active"
            }
    else:
        # Use memory storage when database is not available
        if check.orderId in memory_checks:
            raise HTTPException(status_code=400, detail="Check already exists")
        
        memory_checks[check.orderId] = {
            "orderId": check.orderId,
            "items": [item.dict() for item in check.items],
            "total": check.total,
            "url": check.url,
            "created_at": datetime.utcnow(),
            "status": "active"
        }
    
    print(f"The total for check {check.orderId} is: ${check.total} 🧮")
    return {"message": "Check created successfully", "orderId": check.orderId}

@app.get("/checks/{check_id}")
async def getCheck(check_id: str, db: Session = Depends(get_db)):
    if DATABASE_AVAILABLE:
        try:
            check = db.query(CheckDB).filter(CheckDB.order_id == check_id).first()
            if check:
                return CheckResponse(
                    orderId=check.order_id,
                    items=check.items,
                    total=check.total,
                    url=check.receipt_url,
                    created_at=check.created_at,
                    status=check.status
                )
        except Exception as e:
            logger.error(f"Error getting check from database: {e}")
    
    # Check memory storage
    if check_id in memory_checks:
        check = memory_checks[check_id]
        return CheckResponse(
            orderId=check["orderId"],
            items=check["items"],
            total=check["total"],
            url=check["url"],
            created_at=check["created_at"],
            status=check["status"]
        )
    
    raise HTTPException(status_code=404, detail="Check not found 👎🏼")

@app.get("/checks/{check_id}/receipt")
async def getReceipt(check_id: str, db: Session = Depends(get_db)):
    # Verify check exists
    check_exists = False
    
    if DATABASE_AVAILABLE:
        try:
            check = db.query(CheckDB).filter(CheckDB.order_id == check_id).first()
            if check:
                check_exists = True
        except Exception as e:
            logger.error(f"Error checking database: {e}")
    
    if not check_exists and check_id in memory_checks:
        check_exists = True
    
    if not check_exists:
        raise HTTPException(status_code=404, detail="Check not found 👎🏼")
    
    key = f'{check_id}.txt'
    try:
        result = s3.get_object(Bucket=s3Bucket, Key=key)
        return StreamingResponse(content=result["Body"].iter_chunks())
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            raise HTTPException(status_code=404, detail="Receipt not found 👎🏼")
        else:
            raise

@app.delete("/checks/{check_id}")
async def payCheck(check_id: str, db: Session = Depends(get_db)):
    if DATABASE_AVAILABLE:
        try:
            check = db.query(CheckDB).filter(CheckDB.order_id == check_id).first()
            if check:
                # Mark as paid instead of deleting
                check.status = "paid"
                check.updated_at = datetime.utcnow()
                db.commit()
                
                # Update statistics
                update_stats(db)
                return {"message": "Check paid successfully"}
        except Exception as e:
            logger.error(f"Error updating check in database: {e}")
    
    # Check memory storage
    if check_id in memory_checks:
        memory_checks[check_id]["status"] = "paid"
        return {"message": "Check paid successfully"}
    
    raise HTTPException(status_code=404, detail="Check not found 👎🏼")

@app.get("/api/checks/history")
async def get_checks_history(
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """Get historical check data for charts"""
    if not DATABASE_AVAILABLE:
        # Return empty history when database is not available
        return []
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily revenue and check counts
        daily_stats = db.query(
            func.date(CheckDB.created_at).label('date'),
            func.count(CheckDB.order_id).label('check_count'),
            func.sum(CheckDB.total).label('revenue')
        ).filter(
            CheckDB.created_at >= start_date
        ).group_by(
            func.date(CheckDB.created_at)
        ).order_by(
            func.date(CheckDB.created_at)
        ).all()
        
        return [
            {
                "date": stat.date.isoformat(),
                "check_count": stat.check_count,
                "revenue": float(stat.revenue or 0)
            }
            for stat in daily_stats
        ]
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return []

app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
   reload=bool(os.getenv("RELOAD"))
   uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload)