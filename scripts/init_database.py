#!/usr/bin/env python3
"""
Initialize the ReconX Elite database tables for local development.
Run this before starting the backend if not using Docker Compose.
"""
import asyncio
import os
import sys

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
from app.core.config import settings


async def init_db():
    """Create all database tables."""
    # Convert psycopg2 URL to async URL for SQLAlchemy
    db_url = settings.database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    
    print(f"Connecting to database...")
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully!")
    
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(init_db())
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
