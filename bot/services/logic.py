import re
import random
import datetime
import httpx
import aiosqlite

from db.db import DB_NAME


# Добавление или обновление пользователя
async def add_user(user_id: int, first_name: str, last_name: str, phone: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            '''
            INSERT OR REPLACE INTO users (user_id, first_name, last_name, phone)
            VALUES (?, ?, ?, ?)
            ''',
            (user_id, first_name, last_name, phone)
        )
        await db.commit()


# Проверка, зарегистрирован ли пользователь
async def is_registered(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone() is not None


# Регистрация нового пользователя (с full_name)
async def register_user(user_id: int, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            '''
            INSERT OR IGNORE INTO users (user_id, full_name)
            VALUES (?, ?)
            ''',
            (user_id, full_name)
        )
        await db.commit()


# Сохранение нового запроса
async def insert_request(user_id: int, vin: str, number: str, created_at: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            '''
            INSERT INTO requests (user_id, vin, number, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
            ''',
            (user_id, vin, number, created_at)
        )
        await db.commit()


# Обновление статуса запроса
async def update_request_status(user_id: int, vin: str = None, number: str = None, status: str = "approved"):
    async with aiosqlite.connect(DB_NAME) as db:
        if vin and number:
            await db.execute(
                '''
                UPDATE requests
                SET status = ?
                WHERE user_id = ? AND vin = ? AND number = ?
                ''',
                (status, user_id, vin, number)
            )
        else:
            await db.execute(
                '''
                UPDATE requests
                SET status = ?
                WHERE user_id = ?
                ''',
                (status, user_id)
            )
        await db.commit()


# Сохранение кода и отправка на внешний сервер
async def insert_code(user_id: int, vin: str, number: str, code: str, created_at: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            '''
            INSERT INTO codes (user_id, vin, number, code, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (user_id, vin, number, code, created_at)
        )
        await db.commit()

    # Отправка кода на внешний сервер
    url = f"http://localhost:8000/{vin}/{number}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json={"code": code})
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(f"HTTP Error: {e}")


# Удаление запроса
async def delete_request(user_id: int, vin: str = None, number: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if vin and number:
            await db.execute(
                '''
                DELETE FROM requests
                WHERE user_id = ? AND vin = ? AND number = ?
                ''',
                (user_id, vin, number)
            )
        else:
            await db.execute(
                '''
                DELETE FROM requests
                WHERE user_id = ?
                ''',
                (user_id,)
            )
        await db.commit()


# Поиск пользователей по id, имени, фамилии или телефону
async def search_user(query: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            '''
            SELECT user_id, first_name, last_name, phone
            FROM users
            WHERE user_id LIKE ?
               OR first_name LIKE ?
               OR last_name LIKE ?
               OR phone LIKE ?
            ''',
            (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')
        )
        users = await cursor.fetchall()
    return users


# Получение одобренных VIN-ов пользователя
async def get_approved_vins(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            '''
            SELECT vin, created_at
            FROM requests
            WHERE user_id = ? AND status = 'approved'
            ''',
            (user_id,)
        )
        vins = await cursor.fetchall()
    return vins