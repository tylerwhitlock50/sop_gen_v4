from api.services.database import init_db
import asyncio
import pytest
from  api.services.logger import logger

@pytest.mark.asyncio
def test_db_setup():
    logger.info("Testing database setup")
    asyncio.run(init_db())
    logger.info("Database setup completed")
    
if __name__ == "__main__":
    test_db_setup()