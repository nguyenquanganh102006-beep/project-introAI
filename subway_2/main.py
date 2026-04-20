from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router as api_router
from app.core.graph_manager import GraphManager
from app.core.database import SessionLocal, engine, Base
import app.core.models  # Import this to ensure models are known to SQLAlchemy Base

app = FastAPI(title="Subway Routing Engine", version="1.0.0")

# Setup CORS to allow Frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific URLs (like ["http://localhost:3000"]) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Only suitable for dev: automatically create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Initialize the Singleton GraphManager safely on startup
    manager = GraphManager()
    
    # Load data from the PostgreSQL database
    db = SessionLocal()
    try:
        manager.load_data(db)
        print("Graph data successfully loaded from Database.")
    except Exception as e:
        print(f"Warning: Could not load data from database on startup. Ensure DB is running. Error: {e}")
    finally:
        db.close()

app.include_router(api_router)
