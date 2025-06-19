import aiosqlite

# Имя базы данных
DB_NAME = "data.db"


# Инициализация базы данных: создание таблиц, если они не существуют
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                phone TEXT
            )
        ''')

        # Таблица кодов, выданных пользователям
        await db.execute('''
            CREATE TABLE IF NOT EXISTS codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                vin TEXT,
                number TEXT,
                code TEXT,
                created_at TEXT
            )
        ''')

        # Таблица заявок на получение кода
        await db.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                vin TEXT,
                number TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        ''')

        # Сохраняем изменения
        await db.commit()