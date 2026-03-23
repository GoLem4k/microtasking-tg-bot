import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    # Подключение к базе
    engine = create_async_engine("mysql+aiomysql://root:cabbeg-cohhim-juNza8@localhost:3306/mydb")
    print("Connecting to:", engine.url)

    async with engine.connect() as conn:
        # Используем sqlalchemy.text() для "сырых" SQL запросов
        result = await conn.execute(text("SHOW TABLES;"))

        tables = result.fetchall()
        print("Tables in mydb:")
        for table in tables:
            print(table[0])

    await engine.dispose()

asyncio.run(check())