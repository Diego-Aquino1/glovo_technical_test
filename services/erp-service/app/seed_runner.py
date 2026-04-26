import asyncio
import os
from pathlib import Path

import asyncpg


async def run_seed() -> None:
    raw_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://erp_user:erp_pass@postgres:5432/erp_db",
    )
    db_url = raw_url.replace("postgresql+asyncpg://", "postgresql://")

    seed_file = Path(__file__).parent.parent / "db" / "seed.sql"

    conn = await asyncpg.connect(db_url)
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM articles")
        if count and count > 0:
            print(f"[seed] BD ya tiene datos ({count} artículos), saltando seed.")
            return

        sql = seed_file.read_text(encoding="utf-8")
        await conn.execute(sql)
        print("[seed] Seed ejecutado correctamente.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_seed())
