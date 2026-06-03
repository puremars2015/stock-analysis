from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config import config
import pyodbc
import urllib.parse

engine = None
Session = None


def get_engine():
    global engine
    if engine is None:
        drivers = [
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 18 for SQL Server",
            "SQL Server",
        ]
        for driver in drivers:
            try:
                # Build ODBC connection string and pass it via odbc_connect
                # to avoid URL-encoding issues with special characters in password
                odbc_conn_str = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={config.DB_SERVER};"
                    f"DATABASE={config.DB_NAME};"
                    f"UID={config.DB_USER};"
                    f"PWD={config.DB_PASSWORD}"
                )
                conn_str = (
                    f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc_conn_str)}"
                )
                engine = create_engine(conn_str, pool_pre_ping=True, pool_size=5)
                engine.connect().close()
                print(f"[DB] Connected with driver: {driver}")
                return engine
            except Exception as e:
                print(f"[DB] Failed with {driver}: {str(e)[:80]}")
                continue
        raise RuntimeError("Could not connect to SQL Server with any driver")
    return engine


def get_session():
    global Session
    if Session is None:
        Session = scoped_session(sessionmaker(bind=get_engine()))
    return Session()


def init_db():
    from models import Base
    eng = get_engine()
    Base.metadata.create_all(eng)
    print("[DB] Tables created successfully")


def close_session():
    global Session
    if Session:
        Session.remove()
