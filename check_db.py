import asyncio
import sys
import os

# Set up path to import app correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check_db():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT a.id as app_id, j.title, s.overall_score FROM applications a JOIN jobs j ON a.job_id = j.id LEFT JOIN scores s ON a.id = s.application_id"))
        rows = res.fetchall()
        for r in rows:
            print(f"App: {r.app_id}, Job: {r.title}, Score: {r.overall_score}")

if __name__ == "__main__":
    asyncio.run(check_db())
