import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://USER:PASSWORD@PUBLIC_HOST:PUBLIC_PORT/DBNAME")
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    print("pgvector version:", version)
    await conn.close()

asyncio.run(main())