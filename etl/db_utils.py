import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_conn():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "ecommerce_db")
    user = os.getenv("DB_USER", "ecommerce_user")
    password = os.getenv("DB_PASSWORD", "teja123")

    # optional debug
    # print("CONNECTING TO:", host, port, dbname, user)

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )


@contextmanager
def db_cursor(commit: bool = False):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
