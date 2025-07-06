import httpx
from db import db  # объект Database из db.py


async def add_user(user_id: int, first_name: str, last_name: str, phone: str):
    """
    Добавляет нового пользователя или обновляет данные существующего по user_id.
    """
    query = """
        INSERT INTO users (user_id, first_name, last_name, phone)
        VALUES (:user_id, :first_name, :last_name, :phone)
        ON CONFLICT (user_id) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            phone = EXCLUDED.phone;
    """
    await db.execute(query, {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone
    })


async def is_registered(user_id: int) -> bool:
    """
    Проверяет, зарегистрирован ли пользователь с заданным user_id.
    Возвращает True если есть, иначе False.
    """
    query = "SELECT 1 FROM users WHERE user_id = :user_id"
    row = await db.fetch_one(query, {"user_id": user_id})
    return row is not None


async def register_user(user_id: int, full_name: str):
    """
    Регистрирует пользователя с полным именем (используется, если нет first/last name).
    """
    query = """
        INSERT INTO users (user_id, first_name)
        VALUES (:user_id, :full_name)
        ON CONFLICT DO NOTHING
    """
    await db.execute(query, {"user_id": user_id, "full_name": full_name})


async def insert_request(user_id: int, vin: str, number: str, created_at: str):
    """
    Сохраняет новую заявку со статусом 'pending'.
    """
    query = """
        INSERT INTO requests (user_id, vin, number, status, created_at)
        VALUES (:user_id, :vin, :number, 'pending', :created_at)
    """
    await db.execute(query, {
        "user_id": user_id,
        "vin": vin,
        "number": number,
        "created_at": created_at
    })


async def update_request_status(user_id: int, vin: str = None, number: str = None, status: str = "approved"):
    """
    Обновляет статус заявки. Если указаны vin и number — обновляет конкретную заявку,
    иначе обновляет все заявки пользователя.
    """
    if vin and number:
        query = """
            UPDATE requests
            SET status = :status
            WHERE user_id = :user_id AND vin = :vin AND number = :number
        """
        values = {"status": status, "user_id": user_id, "vin": vin, "number": number}
    else:
        query = """
            UPDATE requests
            SET status = :status
            WHERE user_id = :user_id
        """
        values = {"status": status, "user_id": user_id}

    await db.execute(query, values)


async def insert_code(user_id: int, vin: str, number: str, code: str, created_at: str):
    """
    Сохтани рекорд дар ҷадвали codes.
    """
    query = """
        INSERT INTO codes (user_id, vin, number, code, created_at)
        VALUES (:user_id, :vin, :number, :code, :created_at)
    """
    await db.execute(query, {
        "user_id": user_id,
        "vin": vin,
        "number": number,
        "code": code,
        "created_at": created_at
    })


async def delete_request(user_id: int, vin: str = None, number: str = None):
    """
    Удаляет заявку: либо конкретную (если vin и number заданы), либо все заявки пользователя.
    """
    if vin and number:
        query = """
            DELETE FROM requests
            WHERE user_id = :user_id AND vin = :vin AND number = :number
        """
        values = {"user_id": user_id, "vin": vin, "number": number}
    else:
        query = """
            DELETE FROM requests
            WHERE user_id = :user_id
        """
        values = {"user_id": user_id}

    await db.execute(query, values)


async def search_user(query: str):
    """
    Поиск пользователей по user_id, имени, фамилии или телефону с использованием ILIKE (регистронезависимо).
    """
    like_query = f"%{query}%"
    query_sql = """
        SELECT user_id, first_name, last_name, phone
        FROM users
        WHERE CAST(user_id AS TEXT) ILIKE :q
           OR first_name ILIKE :q
           OR last_name ILIKE :q
           OR phone ILIKE :q
    """
    return await db.fetch_all(query=query_sql, values={"q": like_query})


async def get_approved_vins(user_id: int):
    """
    Получение всех одобренных VIN-ов для пользователя.
    """
    query = """
        SELECT vin, created_at
        FROM requests
        WHERE user_id = :user_id AND status = 'approved'
    """
    return await db.fetch_all(query, {"user_id": user_id})