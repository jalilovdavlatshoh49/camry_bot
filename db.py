import os
from databases import Database
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Пайвастшавӣ ба базаи PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL дар .env ёфтан нашуд.")

db = Database(DATABASE_URL)


async def connect_db():
    """Пайвастшавӣ ба базаи маълумот"""
    await db.connect()
    print("✅ Базаи маълумот пайваст шуд.")


async def disconnect_db():
    """Ҷудошавӣ аз базаи маълумот"""
    await db.disconnect()
    print("🔌 Базаи маълумот ҷудо шуд.")


async def init_db():
    """Сохтани таблицаҳо агар вуҷуд надошта бошанд"""
    create_users = """
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        phone TEXT
    );
    """

    create_codes = """
    CREATE TABLE IF NOT EXISTS codes (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id),
        vin TEXT,
        number TEXT,
        code TEXT,
        created_at TEXT
    );
    """

    create_requests = """
    CREATE TABLE IF NOT EXISTS requests (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id),
        vin TEXT,
        number TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    );
    """

    # Иҷрои ҳамаи запросҳо
    await db.execute(create_users)
    await db.execute(create_codes)
    await db.execute(create_requests)

    print("📦 Базаи PostgreSQL муваффақона инициализатсия шуд.")