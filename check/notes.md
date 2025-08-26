## Check Service with Dashboard 🌯

The Check service is implemented using [FastAPI](https://fastapi.tiangolo.com/), a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints.

### Features

✅ **PostgreSQL Database Storage** - All orders are persisted in PostgreSQL instead of memory  
✅ **Smart Item Normalization** - Handles quantities, case variations, and plural forms  
✅ **Real-time Dashboard** - Beautiful dashboard showing order statistics and analytics  
✅ **RESTful API** - Full CRUD operations with proper error handling  
✅ **Automatic Documentation** - Interactive API docs via Swagger  

### Dashboard Access

🎯 **Dashboard URL**: Access the dashboard directly from the external endpoints in Okteto or visit:  
`https://check-{your-namespace}.{okteto-domain}/dashboard.html`

The dashboard provides:
- **Real-time Statistics**: Total orders, revenue, and average order value
- **Popular Items**: Most ordered items with smart aggregation
- **Order History**: Paginated view of all orders sorted by date
- **Auto-refresh**: Updates every 30 seconds

### API Endpoints

**Core Check Operations**:
- `GET /checks` - List all orders
- `POST /checks` - Create a new order
- `GET /checks/{id}` - Get specific order
- `DELETE /checks/{id}` - Pay/remove order

**Dashboard API**:
- `GET /api/dashboard/stats` - Order statistics
- `GET /api/dashboard/popular-items` - Most popular items
- `GET /api/dashboard/orders` - Paginated order list

**Interactive Documentation**: 
This service uses [Swagger](https://github.com/swagger-api/swagger-ui) for automatic API documentation. Access it at `/docs` endpoint. 🚀

### Database Schema

The service uses PostgreSQL with the following schema:

**Orders Table**:
- `id` (Primary Key)
- `order_id` (Unique identifier)
- `total` (Order total amount)
- `receipt_url` (S3 receipt location)
- `created_at` (Timestamp)

**Order Items Table**:
- `id` (Primary Key)
- `order_id` (Foreign Key to Orders)
- `name` (Original item name)
- `normalized_name` (Cleaned name for analytics)
- `quantity` (Item quantity)
- `price` (Item price)
- `ready` (Preparation status)

### Smart Item Normalization

The system intelligently processes order items:

🔢 **Quantity Extraction**: "2 tacos", "3x pizza" → extracts quantities  
🔤 **Case Handling**: "TACO", "Taco", "taco" → all normalized to "taco"  
📝 **Plural Forms**: "tacos", "burritos" → "taco", "burrito"  
🏷️ **Prefix Removal**: "the taco", "a burrito" → "taco", "burrito"  
✨ **Special Characters**: Removes punctuation and normalizes spacing  

### Development

**Local Development**:
```bash
okteto up check
```

**Deploy Changes**:
```bash
okteto deploy --wait
```

**Run Tests**:
```bash
okteto test check-unit
```