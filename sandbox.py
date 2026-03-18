import requests
import time

url = "http://localhost:3001/api/v1/me"

headers = {
    "x-auth-token": "3GDAz0Ctmng12P48TS9GsB3wK6PEcBQhEPrm92enZnL",
    "x-user-id": "zfcAEKzBha48PZLXF",
    "cookie": "grafana_session=c05697cb147b4ea3737839243101a617; rc_uid=zfcAEKzBha48PZLXF; rc_token=3GDAz0Ctmng12P48TS9GsB3wK6PEcBQhEPrm92enZnL"
}

value = 0

try:

    start_time = time.perf_counter()

    response = requests.get(url, headers=headers, timeout=(3, 10))

    print(response.status_code)
    print(response.text)

    end_time = time.perf_counter()

    value = end_time - start_time

except Exception as e:
    value = 10

finally:
    print(value)