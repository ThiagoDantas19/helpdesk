from peewee import Proxy, SqliteDatabase

db = Proxy()


def init_db(db_path='customermanagement.db'):
    database = SqliteDatabase(db_path, pragmas={
        'journal_mode': 'wal',
        'foreign_keys': 1,
    })
    db.initialize(database)
    return database
