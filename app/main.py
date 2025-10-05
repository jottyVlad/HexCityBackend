from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(hexagons.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)