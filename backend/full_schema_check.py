import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost/recruitment')
    
    # Check all columns in resumes table
    rows = await conn.fetch("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'resumes'
        ORDER BY ordinal_position
    """)
    
    with open('full_schema.txt', 'w') as f:
        f.write("Resumes table columns:\n")
        for row in rows:
            f.write(f"  {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})\n")
        f.write(f"\nTotal columns: {len(rows)}\n")
        f.write(f"is_active exists: {'is_active' in [r['column_name'] for r in rows]}\n")
    
    await conn.close()
    print("Schema written to full_schema.txt")

asyncio.run(main())
