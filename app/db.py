import asyncpg
import os

pool: asyncpg.Pool = None


async def init_pool():
    global pool
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"), min_size=1, max_size=5)
    # Run schema
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        sql = f.read()
    async with pool.acquire() as conn:
        await conn.execute(sql)


async def close_pool():
    global pool
    if pool:
        await pool.close()


async def fetch(query, *args):
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(r) for r in rows]


async def fetchrow(query, *args):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def execute(query, *args):
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetchval(query, *args):
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)
