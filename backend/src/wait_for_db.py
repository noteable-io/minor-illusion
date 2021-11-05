# Loop until we see cockroach is happy ...

import time
import psycopg2

while True:

    try:
        psycopg2.connect('dbname=defaultdb user=root host=cockroach port=26257').close()
        print('wait_for_db: DB is observed online.')
        # Happy!
        break
    except psycopg2.OperationalError as e:
        time.sleep(2)
