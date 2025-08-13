# Oktaco Shop Check Service

The Check service is implemented using [FastAPI](https://fastapi.tiangolo.com/), a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints. 

## 📊 Enhanced Dashboard

The service now includes a comprehensive dashboard at the root endpoint (`/`) that provides:

### Real-time Statistics
- **Total Orders**: Complete order count across all time
- **Total Revenue**: Sum of all order totals
- **Today's Orders**: Orders placed today

### Data Visualization
- **Popular Items Chart**: Interactive doughnut chart showing the most ordered items
- **Recent Orders**: List of the 10 most recent orders with timestamps

### Smart Item Normalization
The system intelligently processes order items to provide accurate statistics:
- **Quantity Extraction**: Recognizes patterns like "2x taco", "3 burritos" 
- **Plural Normalization**: Converts "tacos" → "taco", "pizzas" → "pizza"
- **Case Normalization**: Handles "TACO", "Taco", "taco" as the same item
- **Grouping**: Combines similar items for accurate popularity tracking

## 🗄️ PostgreSQL Integration

Orders are now persisted in a PostgreSQL database with:
- **Dual Storage**: Maintains backward compatibility with in-memory storage
- **Data Persistence**: Orders survive service restarts
- **Analytics**: Enhanced reporting and statistics capabilities
- **Normalization**: Smart item processing for better data analysis

## 🔧 API Documentation

This service uses [Swagger](https://github.com/swagger-api/swagger-ui) to provide automatic interactive API documentation. You can use the `/docs` endpoint to try the API using your browser to speed up your development.

### New Endpoints
- `GET /dashboard/stats` - Comprehensive dashboard statistics
- `GET /` - Interactive dashboard interface

### Enhanced Endpoints
All existing endpoints now support PostgreSQL storage while maintaining full backward compatibility.

## 🧪 Testing

The service includes comprehensive unit tests covering:
- Item normalization algorithms
- Database models and operations  
- API endpoints functionality
- Dashboard statistics generation

Run tests using: `okteto test check-unit`

This works both in "deploy" and "okteto up" mode. 🚀