# server/main.py
import threading
import uvicorn

from fastapi import FastAPI, HTTPException
import aiosqlite

app = FastAPI()
DB_NAME = "data.db"


@app.get("/vin/{vin}/puk/{puk}")
async def get_code_by_vin_and_puk(vin: str, puk: str):
    """
    Получение кода по VIN и PUK (номер).
    Пример запроса: /vin/ABC123/puk/4567
    """
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT code FROM codes WHERE vin = ? AND number = ?",
            (vin, puk)
        )
        row = await cursor.fetchone()
        await cursor.close()

    if row:
        return {
            "status": "success",
            "code": row[0]
        }
    else:
        raise HTTPException(status_code=404, detail="Code not found")
    

    # Запуск FastAPI-сервера в отдельном потоке
def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    threading.Thread(target=start_api).start()
