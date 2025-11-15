import sqlite3
import time
import os

DB_PATH = "db/rides.db"

SLEEP_INTERVAL = 60


def connect_to_db():
    print("Waiting for file...", flush=True)
    while not os.path.exists(DB_PATH):
        time.sleep(2)

    print("Connecting...", flush=True)
    return sqlite3.connect(DB_PATH)


def calculate_statistics():
    conn = None
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS rides (
                    ride_uuid TEXT PRIMARY KEY,
                    user_uuid TEXT,
                    driver_uuid TEXT,
                    distance REAL,
                    price REAL
                )
            ''')
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS drivers (
                    driver_uuid TEXT PRIMARY KEY,
                    name TEXT,
                    surname TEXT,
                    car_uuid TEXT,
                    effective_from TEXT,
                    expiry_date TEXT
                )
            ''')
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_uuid TEXT PRIMARY KEY,
                    name TEXT,
                    surname TEXT,
                    is_driver BOOLEAN
                )
            ''')
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS driver_statistics (
            driver_id TEXT PRIMARY KEY,
            total_distance REAL NOT NULL
        )
        """)

        print("Таблицю driver_statistics перевірено/створено.", flush=True)

        cursor.execute("""
        SELECT 
            driver_id, 
            SUM(distance) as total_distance
        FROM rides
        GROUP BY driver_id
        """)

        statistics = cursor.fetchall()
        print(f"Calculating statistics for {len(statistics)} drivers.", flush=True)

        cursor.executemany("""
        INSERT OR REPLACE INTO driver_statistics (driver_id, total_distance)
        VALUES (?, ?)
        """, statistics)

        conn.commit()
        print("Statistics updated", flush=True)

    except sqlite3.Error as e:
        print(f"Error SQLite: {e}", flush=True)
    except Exception as e:
        print(f"Error {e}", flush=True)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("Сервіс-агрегатор статистики запущено.", flush=True)
    while True:
        calculate_statistics()
        print(f"Наступне оновлення через {SLEEP_INTERVAL} секунд.", flush=True)
        time.sleep(SLEEP_INTERVAL)