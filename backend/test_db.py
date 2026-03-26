import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import urllib.parse

# Credentials from .env
USER = "hiring_user"
PASS = urllib.parse.quote_plus("hiring_pass")
HOST = "localhost" # overriding the .env docker hostname 
PORT = 3307
DB = "hiring_db"

async def test_connection():
    db_url = f"mysql+aiomysql://{USER}:{PASS}@{HOST}:{PORT}/{DB}"
    print(f"Testing connection to {HOST}:{PORT}")
    try:
        engine = create_async_engine(db_url)
        # Test connection
        async with engine.connect() as conn:
            print("SUCCESS! Connected to the database.")
            # Execute a simple query
            result = await conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"MySQL Version: {version}")
            
    except Exception as e:
        print(f"FAILED to connect!")
        print(f"Error: {str(e)}")

        print("\nTrying to connect as root as a fallback...")
        try:
            root_url = f"mysql+aiomysql://root:rootpassword@{HOST}:{PORT}/{DB}"
            engine_root = create_async_engine(root_url)
            async with engine_root.connect() as conn:
                print("SUCCESS! Connected as root.")
                result = await conn.execute(text("SELECT VERSION()"))
                print(f"MySQL Version: {result.scalar()}")
        except Exception as e2:
            print(f"FAILED to connect as root too!")
            print(f"Error: {str(e2)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
