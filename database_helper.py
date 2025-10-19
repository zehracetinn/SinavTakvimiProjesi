# database_helper.py
import os, sqlite3

class DatabaseHelper:
    _connection = None
    _db_path = os.path.abspath("sinav_takvimi.db")  # <-- TEK KAYNAK

    @staticmethod
    def get_connection():
        if DatabaseHelper._connection is None:
            DatabaseHelper._connection = sqlite3.connect(
                DatabaseHelper._db_path,
                timeout=10,
                check_same_thread=False,
                isolation_level=None  # autocommit
            )
            # Güvenli foreign key vs.
            DatabaseHelper._connection.execute("PRAGMA foreign_keys = ON;")
        return DatabaseHelper._connection

    @staticmethod
    def get_db_path():
        return DatabaseHelper._db_path

    @staticmethod
    def close_connection():
        if DatabaseHelper._connection:
            DatabaseHelper._connection.close()
            DatabaseHelper._connection = None
