# Inventory & Order Management System – Backend API

Production-ready FastAPI backend for inventory and order management with PostgreSQL, SQLAlchemy ORM, Alembic migrations, and Docker support. Designed for deployment on platforms like Render.

## Tech Stack

- **Python 3.12**
- **FastAPI** – REST API framework
- **PostgreSQL** – Primary database
- **SQLAlchemy 2.0** – ORM
- **Pydantic v2** – Request/response validation
- **Alembic** – Database migrations
- **Docker & Docker Compose** – Containerized deployment
- **pytest** – Testing

## Project Structure

```
inventory-backend/
├── app/
│   ├── api/              # Route handlers
│   ├── core/             # Config & database
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── utils/            # Exceptions & helpers
│   └── main.py           # Application entry point
├── alembic/              # Migration scripts
├── tests/                # pytest test suite
├── logs/                 # Application logs
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Quick Start with Docker

### Prerequisites

- Docker
- Docker Compose

### Run the Application

```bash
cd inventory-backend
docker-compose up --build
```

The API will be available at:

- **API Base:** http://localhost:8000/api
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

Migrations run automatically on container startup.

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes

```bash
docker-compose down -v
```

## Local Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16+

### Installation

```bash
cd inventory-backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Environment Variables

Copy the example environment file and update values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/inventory_db` |
| `APP_NAME` | Application display name | `Inventory Management System` |
| `DEBUG` | Enable debug logging | `false` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000,http://localhost:8000` |
| `LOW_STOCK_THRESHOLD` | Stock level for low-stock alerts | `10` |

### Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description of changes"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Tests

```bash
pytest -v
```

Tests use an in-memory SQLite database and do not require PostgreSQL.

## API Documentation

Base URL: `/api`

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/products` | Create product |
| `GET` | `/api/products` | List products (pagination, search) |
| `GET` | `/api/products/{id}` | Get product by ID |
| `PUT` | `/api/products/{id}` | Update product |
| `DELETE` | `/api/products/{id}` | Delete product |

**Query Parameters (List):**
- `page` – Page number (default: 1)
- `limit` – Items per page (default: 10, max: 100)
- `search` – Search by product name or SKU

**Create Product Example:**

```json
{
  "name": "iPhone 15",
  "sku": "IPH15",
  "price": 79999,
  "stock_quantity": 50
}
```

### Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/customers` | Create customer |
| `GET` | `/api/customers` | List customers (pagination) |
| `GET` | `/api/customers/{id}` | Get customer by ID |
| `DELETE` | `/api/customers/{id}` | Delete customer |

**Create Customer Example:**

```json
{
  "full_name": "Azad Khan",
  "email": "azad@gmail.com",
  "phone": "9999999999"
}
```

### Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/orders` | Create order |
| `GET` | `/api/orders` | List orders with details |
| `GET` | `/api/orders/{id}` | Get order details |
| `DELETE` | `/api/orders/{id}` | Cancel order & restore inventory |

**Create Order Example:**

```json
{
  "customer_id": "uuid-here",
  "items": [
    { "product_id": "uuid-here", "quantity": 2 },
    { "product_id": "uuid-here", "quantity": 1 }
  ]
}
```

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/dashboard` | Summary statistics |

**Response Example:**

```json
{
  "total_products": 100,
  "total_customers": 50,
  "total_orders": 250,
  "low_stock_products": 5
}
```

## Error Response Format

All errors follow a consistent structure:

```json
{
  "success": false,
  "message": "Product not found"
}
```

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request |
| `404` | Not Found |
| `409` | Conflict (duplicate SKU/email) |
| `422` | Validation Error |
| `500` | Internal Server Error |

## Business Rules

1. SKU must be unique across products
2. Customer email must be unique
3. Product price and stock quantity cannot be negative
4. Order item quantity must be greater than zero
5. Orders cannot be created with insufficient inventory
6. Inventory decreases automatically on order creation
7. Inventory restores automatically on order cancellation
8. Total order amount is calculated server-side only
9. All order operations use database transactions with rollback on failure

## Deploying to Render

1. Create a **PostgreSQL** database on Render
2. Create a **Web Service** connected to this repository
3. Set environment variables:
   - `DATABASE_URL` – Internal database URL from Render
   - `APP_NAME` – Your app name
   - `DEBUG` – `false`
   - `ALLOWED_ORIGINS` – Your frontend URL(s)
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Logging

Application logs are written to:

- Console (stdout)
- `logs/app.log` (rotating, 10 MB max per file)

Logged events include API requests, application errors, and database errors.

## License

MIT
