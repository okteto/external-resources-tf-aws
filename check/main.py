import boto3
import os
import tempfile
import jinja2
import uvicorn
from datetime import datetime
from math import ceil

from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from pydantic import BaseModel
from typing import List, Optional

from database import (
    get_db, init_db, Order, OrderItem, 
    extract_quantity_and_name, normalize_item_name
)

app = FastAPI()
env = jinja2.Environment(loader=jinja2.PackageLoader("main"), autoescape=jinja2.select_autoescape())
template = env.get_template("receipt.j2")

s3 = boto3.client('s3')
s3Bucket = os.getenv("BUCKET")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

class Item(BaseModel):
    name: str
    price: float | None = 0
    ready: bool | None = False

class Check(BaseModel):
    orderId: str
    items: List[Item]
    total: float | None = 0
    url: str | None = ""

class OrderResponse(BaseModel):
    id: int
    order_id: str
    total: float
    receipt_url: Optional[str]
    created_at: datetime
    items: List[dict]

class OrderStatsResponse(BaseModel):
    total_orders: int
    total_revenue: float
    average_order: float

class PopularItemResponse(BaseModel):
    name: str
    count: int

class PaginatedOrdersResponse(BaseModel):
    orders: List[OrderResponse]
    current_page: int
    total_pages: int
    total_orders: int


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

@app.get("/healthz")
async def healthz():
    return {"message": "Check please 🫰!"}


@app.get("/checks")
async def getChecks(db: Session = Depends(get_db)):
    """Get all checks in format expected by the frontend."""
    orders = db.query(Order).order_by(desc(Order.created_at)).all()
    response = []
    for order in orders:
        # Format items for frontend compatibility
        items = []
        for item in order.items:
            items.append({
                "name": item.name,
                "price": item.price,
                "ready": item.ready
            })
        
        # Return in format expected by main.js
        order_data = {
            "orderId": order.order_id,  # Frontend expects orderId
            "total": order.total,
            "items": items,
            "url": order.receipt_url or ""  # Frontend expects url
        }
        response.append(order_data)
    return response

@app.post("/checks", status_code=200)
async def prepare_check(check: Check, db: Session = Depends(get_db)):
    # Validate that the order has items
    if not check.items or len(check.items) == 0:
        raise HTTPException(status_code=400, detail="Cannot submit order without any items 🚫")
    
    # Create new order in database
    db_order = Order(order_id=check.orderId)
    db.add(db_order)
    db.flush()  # Get the order ID
    
    # Process items with normalization and pricing
    total = 0
    processed_items = []
    
    for item in check.items:
        # Extract quantity and clean name
        quantity, clean_name = extract_quantity_and_name(item.name)
        normalized_name = normalize_item_name(clean_name)
        
        # Calculate price (using original logic)
        price_per_item = len(item.name)
        total_item_price = price_per_item * quantity
        
        # Create order item
        db_item = OrderItem(
            order_id=db_order.id,
            name=item.name,
            normalized_name=normalized_name,
            quantity=quantity,
            price=total_item_price,
            ready=item.ready or False
        )
        db.add(db_item)
        
        processed_items.append({
            'name': item.name,
            'quantity': quantity,
            'price': total_item_price
        })
        total += total_item_price

    # Update order total
    db_order.total = total
    
    # Generate and upload receipt
    receipt = template.render(total=total, items=processed_items, check_id=check.orderId)
    receipt_url = upload_receipt(check.orderId, receipt)
    db_order.receipt_url = receipt_url
    
    # Commit to database
    db.commit()
    
    print(("The total for check {check_id} is: ${total} 🧮").format(check_id=check.orderId, total=total))
    
    # Return response in original format for compatibility
    check.total = total
    check.url = receipt_url
    return check
    
@app.get("/checks/{check_id}")
async def getCheck(check_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == check_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Check not found 👎🏼")
    
    # Return in original Check format for compatibility
    items = []
    for db_item in order.items:
        items.append(Item(
            name=db_item.name,
            price=db_item.price,
            ready=db_item.ready
        ))
    
    return Check(
        orderId=order.order_id,
        items=items,
        total=order.total,
        url=order.receipt_url or ""
    )

@app.get("/checks/{check_id}/receipt")
async def getReceipt(check_id):
    
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
    order = db.query(Order).filter(Order.order_id == check_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Check not found 👎🏼")
    
    # Delete the order and its items (cascade will handle items)
    db.delete(order)
    db.commit()
    return {"message": "Check paid and removed"}

# Dashboard API endpoints
@app.get("/api/dashboard/stats", response_model=OrderStatsResponse)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get order statistics for dashboard."""
    total_orders = db.query(Order).count()
    total_revenue = db.query(func.sum(Order.total)).scalar() or 0.0
    average_order = total_revenue / total_orders if total_orders > 0 else 0.0
    
    return OrderStatsResponse(
        total_orders=total_orders,
        total_revenue=total_revenue,
        average_order=average_order
    )

@app.get("/api/dashboard/popular-items", response_model=List[PopularItemResponse])
async def get_popular_items(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """Get most popular items based on normalized names."""
    # Query items grouped by normalized name, ordered by count
    popular_items = (
        db.query(
            OrderItem.normalized_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        )
        .group_by(OrderItem.normalized_name)
        .order_by(desc('total_quantity'))
        .limit(limit)
        .all()
    )
    
    return [
        PopularItemResponse(name=item.normalized_name, count=int(item.total_quantity))
        for item in popular_items
    ]

@app.get("/api/dashboard/orders", response_model=PaginatedOrdersResponse)
async def get_paginated_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get paginated orders for dashboard."""
    offset = (page - 1) * limit
    
    # Get total count
    total_orders = db.query(Order).count()
    total_pages = ceil(total_orders / limit)
    
    # Get paginated orders
    orders = (
        db.query(Order)
        .order_by(desc(Order.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    order_responses = []
    for order in orders:
        order_data = OrderResponse(
            id=order.id,
            order_id=order.order_id,
            total=order.total,
            receipt_url=order.receipt_url,
            created_at=order.created_at,
            items=[
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "price": item.price,
                    "ready": item.ready
                } for item in order.items
            ]
        )
        order_responses.append(order_data)
    
    return PaginatedOrdersResponse(
        orders=order_responses,
        current_page=page,
        total_pages=total_pages,
        total_orders=total_orders
    )

app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
   reload=bool(os.getenv("RELOAD"))
   uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload)