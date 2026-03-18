import requests
import time
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from concurrent.futures import ThreadPoolExecutor
import time
from dotenv import load_dotenv
import os

load_dotenv()

postgres_pool = pool.ThreadedConnectionPool(1, 20,  os.getenv("DATABASE_URL"))

def extract_active_authentication() -> dict[str, str]: # ! -> function which always extracts a valid token, to prevent auth failures, which can mislead results.
    body = {
        "username": "admin",
        "password": "admin"
    }

    response = requests.post("http://localhost:3000/api/v1/auth/login", json=body)

    data = response.json()

    headers = {
        "Authorization": f"Bearer {data['token']}"
    }

    return headers
    
def check_latency(route: str, route_id: int, desired_time: int) -> None:

    value = 10
    retry_seconds = 4

    postgres = postgres_pool.getconn()
    cursor = postgres.cursor(cursor_factory=RealDictCursor)

    headers = extract_active_authentication()

    try:
        requests.get(route, timeout=(3, desired_time), headers=headers, verify=False)

        
    except Exception:

        retry_seconds *= 2

        try:

            requests.get(route, timeout=(3, desired_time), headers=headers, verify=False)

          
        except Exception:


            try:

                requests.get(route, timeout=(3, desired_time), headers=headers, verify=False)

     
            except Exception:
                value = 50

    finally:
        cursor.execute("insert into routes_metrics (parent, value) values (%s, %s) returning *;", (route_id, value))

        postgres_response = cursor.fetchone()

        postgres.commit()

        cursor.close()
        postgres_pool.putconn(postgres)

        print(postgres_response)


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
            executor.submit(check_latency, item['route'], item['route_id'], item['desired_time'])

if __name__ == "__main__":
    while True:
        main("goat")
        time.sleep(10)

