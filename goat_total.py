import requests
import time
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os
import random

load_dotenv()

postgres_pool = pool.ThreadedConnectionPool(1, 20,  os.getenv("DATABASE_URL"))

def extract_active_authentication() -> dict[str, str]: # ! -> function which always extracts a valid token, to prevent auth failures, which can mislead results.
    try:
        body = {
            "username": os.getenv("GOAT_USERNAME"),
            "password": os.getenv("GOAT_PASSWORD")
        } # * only used for testing, will consider caching later.

        response = requests.post("http://localhost:3000/api/v1/auth/login", json=body)

        response.raise_for_status()
        
        data = response.json()

        headers = {
            "Authorization": f"Bearer {data['token']}"
        }

        return headers
    
    except Exception as e:
        print(e)
    
def check_timeout(route: str, route_id: int, desired_time: int) -> None:
    value = 0
    max_retries = 3
    base_delay = 4
    exception_log = None
    exception_type = None
    latency = None


    postgres = postgres_pool.getconn()
    cursor = postgres.cursor(cursor_factory=RealDictCursor)

    headers = extract_active_authentication()

    try:
        for attempt in range(max_retries):
            start = time.perf_counter()
            try:
                response = requests.get(
                    route,
                    timeout=(3, desired_time),
                    headers=headers,
                    verify=False
                )

                latency = time.perf_counter() - start

                response.raise_for_status() # * returns an exception for non 200 status

                break

            except Exception as e:
                if attempt == max_retries - 1:
                    
                    value = 50
                    print(f"Final failure for {route}: {e}")

                    exception_log = str(e)

                    exception_type = type(e).__name__

                    print(exception_log, exception_type, value)

                else:
                    max_delay = base_delay * (2 ** attempt)
                    delay = random.uniform(0, max_delay)
                    print(f"{route} retry {attempt + 1} in {delay}s")
                    time.sleep(delay)

    finally:
        cursor.execute(
            "insert into routes_metrics (parent, value, log, type, latency) values (%s, %s, %s, %s, %s) returning *;",
            (route_id, value, exception_log, exception_type, latency)
        )

        inserted = cursor.fetchone()
        print(inserted)

        postgres.commit()
        cursor.close()
        postgres_pool.putconn(postgres)


def main(entity_name: str) -> None:
    postgres = postgres_pool.getconn()
    cursor = postgres.cursor(cursor_factory=RealDictCursor)

    try:
        sql = """
                select name, route, routes.id as route_id, desired_time from http 
                inner join routes on routes.parent = http.id where name = %s;
            """
        
        cursor.execute(sql, (entity_name,))
        response = cursor.fetchall()

    finally:
        cursor.close()
        postgres_pool.putconn(postgres)

    with ThreadPoolExecutor(10) as executor:
        for item in response:
            executor.submit(check_timeout, item['route'], item['route_id'], item['desired_time'])

if __name__ == "__main__":
    while True:
        main("goat")
        time.sleep(10)

