import boto3
import os
import tempfile
import jinja2
import uvicorn
import json
import asyncio
from datetime import datetime

from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from pydantic import BaseModel
from typing import List, Optional

# Import our custom modules
from database import get_session, init_db, Order, OrderItem, get_db_stats
from item_normalizer import normalize_item_name

app = FastAPI()
env = jinja2.Environment(loader=jinja2.PackageLoader("main"), autoescape=jinja2.select_autoescape())
template = env.get_template("receipt.j2")

# Keep S3 functionality for receipt storage
s3 = boto3.client('s3')
s3Bucket = os.getenv("BUCKET")
checks = {}  # Keep in-memory store for backwards compatibility

class Item(BaseModel):
    name: str
    price: float | None = 0
    ready: bool | None = False

class Check(BaseModel):
    orderId: str
    items: List[Item]
    total: float | None = 0
    url: str | None = ""

class DashboardStats(BaseModel):
    total_orders: int
    total_revenue: float
    orders_today: int
    popular_items: List[dict]
    recent_orders: List[dict]


async def save_order_to_database(check: Check, session: AsyncSession):
    """Save order and items to PostgreSQL database with normalization"""
    try:
        # Create order record
        order = Order(
            id=check.orderId,
            total=check.total,
            receipt_url=check.url,
            items_json=json.dumps([item.dict() for item in check.items])
        )
        session.add(order)
        
        # Process and save items with normalization
        for item in check.items:
            normalized_name, quantity = normalize_item_name(item.name)
            
            order_item = OrderItem(
                order_id=check.orderId,
                name=item.name,
                normalized_name=normalized_name,
                quantity=quantity,
                price=item.price,
                ready=item.ready
            )
            session.add(order_item)
        
        await session.commit()
        print(f"Saved order {check.orderId} to database with {len(check.items)} items")
    except Exception as e:
        await session.rollback()
        print(f"Database error saving order {check.orderId}: {e}")
        raise

def upload_receipt(orderId: str, receipt: str):
    """Upload receipt to S3 (preserved functionality)"""
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

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await init_db()
    print("Database initialized successfully")

@app.get("/healthz")
async def healthz():
    return {"message": "Check please 🫰!"}

# New dashboard endpoint
@app.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        stats = await get_db_stats()
        return DashboardStats(**stats)
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        # Return empty stats if database is not available
        return DashboardStats(
            total_orders=0,
            total_revenue=0.0,
            orders_today=0,
            popular_items=[],
            recent_orders=[]
        )

@app.get("/checks", response_model=list[Check])
async def getChecks(session: AsyncSession = Depends(get_session)):
    """Get current checks (enhanced with database support)"""
    try:
        # Try to get from database first
        result = await session.execute(
            select(Order).where(Order.paid_at.is_(None)).order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()
        
        response = []
        for order in orders:
            # Parse items from JSON backup
            items_data = json.loads(order.items_json) if order.items_json else []
            items = [Item(**item_data) for item_data in items_data]
            
            check = Check(
                orderId=order.id,
                items=items,
                total=order.total,
                url=order.receipt_url
            )
            response.append(check)
        
        return response
    except Exception as e:
        print(f"Database error in getChecks: {e}")
        # Fallback to in-memory store
        response = []
        for checkID in checks:
            response.append(checks[checkID])
        return response

@app.post("/checks", status_code=200)
async def prepare_check(check: Check, session: AsyncSession = Depends(get_session)):
    """Create a new check (enhanced with database storage and normalization)"""
    # Validate that the order has items
    if not check.items or len(check.items) == 0:
        raise HTTPException(status_code=400, detail="Cannot submit order without any items 🚫")
    
    # Calculate price
    total = 0
    for i in range(len(check.items)):
        item = check.items[i]
        price = len(item.name)  # Keep original pricing logic
        check.items[i].price = price
        total += price

    check.total = total
    receipt = template.render(total=check.total, items=check.items, check_id=check.orderId)
    check.url = upload_receipt(check.orderId, receipt)
    
    # Save to database
    try:
        await save_order_to_database(check, session)
    except Exception as e:
        print(f"Failed to save to database: {e}")
    
    # Keep in-memory store for backwards compatibility
    checks[check.orderId] = check
    print(("The total for check {check_id} is: ${total} 🧮").format(check_id=check.orderId, total=check.total))
    
@app.get("/checks/{check_id}")
async def getCheck(check_id: str, session: AsyncSession = Depends(get_session)):
    """Get a specific check (enhanced with database support)"""
    try:
        # Try database first
        result = await session.execute(select(Order).where(Order.id == check_id))
        order = result.scalar_one_or_none()
        
        if order:
            items_data = json.loads(order.items_json) if order.items_json else []
            items = [Item(**item_data) for item_data in items_data]
            
            return Check(
                orderId=order.id,
                items=items,
                total=order.total,
                url=order.receipt_url
            )
    except Exception as e:
        print(f"Database error in getCheck: {e}")
    
    # Fallback to in-memory store
    if check_id in checks.keys():
        return checks[check_id]
    
    raise HTTPException(status_code=404, detail="Check not found 👎🏼")

@app.get("/checks/{check_id}/receipt")
async def getReceipt(check_id: str):
    """Get receipt from S3 (preserved functionality)"""
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
async def payCheck(check_id: str, session: AsyncSession = Depends(get_session)):
    """Mark check as paid (enhanced with database support)"""
    try:
        # Update in database
        result = await session.execute(select(Order).where(Order.id == check_id))
        order = result.scalar_one_or_none()
        
        if order:
            order.paid_at = datetime.utcnow()
            await session.commit()
        else:
            raise HTTPException(status_code=404, detail="Check not found 👎🏼")
            
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        print(f"Database error in payCheck: {e}")
    
    # Remove from in-memory store for backwards compatibility
    if check_id in checks.keys():
        del checks[check_id]
    
    return {"message": "Check paid successfully"}

app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
   reload=bool(os.getenv("RELOAD"))
   uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload)