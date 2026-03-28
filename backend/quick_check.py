#!/usr/bin/env python
"""Quick check of resumes table structure"""
import asyncpg
import asyncio

async def check():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost/recruitment')
    result = await conn.fetch("""
        SELECT column_name, data_type FROM information_schema.columns 
        WHERE table_name = 'resumes' ORDER BY ordinal_position LIMIT 20
    """)
    for r in result:
        print(f"{r['column_name']}: {r['data_type']}")
    await conn.close()

asyncio.run(check())
