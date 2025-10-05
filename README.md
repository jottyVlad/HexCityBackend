# Basic FastAPI REST API

This is a basic skeleton for a REST API application built with FastAPI with an improved project structure.

## Features

- CRUD operations (Create, Read, Update, Delete)
- Pydantic models for request/response validation
- SQLAlchemy database integration
- Built-in Swagger UI documentation
- Health check endpoint

## Installation

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

To run the application, execute:
```bash
python app/main.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the application is running, you can access:
- Interactive API documentation: http://localhost:8000/docs
- Alternative API documentation: http://localhost:8000/redoc

## Endpoints

### General
- `GET /` - Health check

### Items
- `GET /items/` - Get all items
- `GET /items/{id}` - Get item by ID
- `POST /items/` - Create new item
- `PUT /items/{id}` - Update item
- `DELETE /items/{id}` - Delete item

### Hexagon Data
- `GET /hexagons/` - Get all hexagon data
- `GET /hexagons/{id}` - Get hexagon data by ID
- `POST /hexagons/` - Create new hexagon data
- `PUT /hexagons/{id}` - Update hexagon data
- `PATCH /hexagons/{id}` - Partially update hexagon data
- `DELETE /hexagons/{id}` - Delete hexagon data

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # Main application file
│   ├── database.py      # Database configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── item.py      # Item model
│   │   └── hexagon.py   # Hexagon data model
│   ├── schemas/
│   │   ├── __init__.py  # Item Pydantic schemas
│   │   └── hexagon.py   # Hexagon data Pydantic schemas
│   └── routes/
│       ├── items.py     # Item routes
│       └── hexagons.py  # Hexagon data routes
├── requirements.txt     # Project dependencies
└── README.md            # This file
```