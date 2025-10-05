# Moscow Hexagon FastAPI REST API

This is a backend for a Moscow hexagon map

## Features

- CRUD operations (Create, Read, Update, Delete)
- Pydantic models for request/response validation
- SQLAlchemy database integration

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

## Endpoints

### Hexagon Data
- `GET /hexagons/` - Get all hexagon data
- `GET /hexagons/{id}` - Get hexagon data by ID
- `POST /hexagons/` - Create new hexagon data
- `PUT /hexagons/{id}` - Update hexagon data
- `PATCH /hexagons/{id}` - Partially update hexagon data
- `DELETE /hexagons/{id}` - Delete hexagon data
- `GET /hexagons/{id}/metrics` - Get hexagon metric
