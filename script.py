import requests
import time
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from concurrent.futures import ThreadPoolExecutor

postgres_pool = pool.ThreadedConnectionPool(1, 20,  "postgresql://postgres:postgres@localhost:5432/monitoring")

def check_latency(route: str, route_id: int, desired_time: int) -> None:

    value = 10
    retry_seconds = 4

    postgres = postgres_pool.getconn()
    cursor = postgres.cursor(cursor_factory=RealDictCursor)

    try:
        requests.get(route, timeout=(3, desired_time))

    except Exception: 

        time.sleep(retry_seconds)

        retry_seconds *= 2

        try:

            requests.get(route, timeout=(3, desired_time))

          
        except Exception:
            
            retry_seconds *= 2

            try:

                requests.get(route, timeout=(3, desired_time))

     
            except Exception:
                value = 50

    finally:
        cursor.execute("insert into routes_metrics (parent, value) values (%s, %s) returning *;", (route_id, value))

        postgres_response = cursor.fetchone()

        postgres.commit()

        cursor.close()
        postgres_pool.putconn(postgres)

        print(postgres_response)


def main() -> None:
    postgres = postgres_pool.getconn()
    cursor = postgres.cursor(cursor_factory=RealDictCursor)

    sql = """
            select name, route, routes.id as route_id, desired_time from http 
            inner join routes on routes.parent = http.id;
        """
    
    cursor.execute(sql)

    response = cursor.fetchall()

    with ThreadPoolExecutor(15) as executor:
        for item in response:
            executor.submit(check_latency, item['route'], item['route_id'], item['desired_time'])

if __name__ == "__main__":
    while True:
        main()
