from .db import get_db, engine
from .models import Base
import asyncio
from api.services.logger import logger


async def init_db():
    """Initialize the database"""
    logger.info("Initializing database")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    
if __name__ == "__main__":
    asyncio.run(init_db())






