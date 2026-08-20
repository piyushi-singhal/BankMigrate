import os
import pymssql
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "BankMigrate123!")
DB_LEGACY_NAME = os.getenv("DB_LEGACY_NAME", "BankMigrate_Legacy")
DB_TARGET_NAME = os.getenv("DB_TARGET_NAME", "BankMigrate_Target")

def get_legacy_connection():
    """Returns PyMSSQL connection object for BankMigrate_Legacy database."""
    return pymssql.connect(
        server=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_LEGACY_NAME,
        autocommit=True
    )

def get_target_connection():
    """Returns PyMSSQL connection object for BankMigrate_Target database."""
    return pymssql.connect(
        server=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_TARGET_NAME,
        autocommit=True
    )

def get_legacy_engine():
    """Returns SQLAlchemy Engine for BankMigrate_Legacy."""
    connection_url = f"mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_LEGACY_NAME}"
    return create_engine(connection_url)

def get_target_engine():
    """Returns SQLAlchemy Engine for BankMigrate_Target."""
    connection_url = f"mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_TARGET_NAME}"
    return create_engine(connection_url)
