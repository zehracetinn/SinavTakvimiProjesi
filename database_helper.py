import sqlite3

class DatabaseHelper:
    _connection = None

    @staticmethod
    def get_connection():
        """Uygulama boyunca tek bağlantı."""
        if DatabaseHelper._connection is None:
            DatabaseHelper._connection = sqlite3.connect(
                "sinav_takvimi.db",
                timeout=10,
                check_same_thread=False,  # çok önemli!
                isolation_level=None  # autocommit açık
            )
        return DatabaseHelper._connection

    @staticmethod
    def close_connection():
        if DatabaseHelper._connection:
            DatabaseHelper._connection.close()
            DatabaseHelper._connection = None
