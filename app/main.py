from fastapi import FastAPI
from routes import hexagons
from database.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create the FastAPI app instance
app = FastAPI(
    title="Basic REST API",
    description="A basic skeleton for a REST API using FastAPI with improved structure",
    version="0.2.0"
)

# Include routers
app.include_router(hexagons.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)