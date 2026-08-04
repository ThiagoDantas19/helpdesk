from peewee import Proxy, SqliteDatabase
import unicodedata

db = Proxy()


def unaccent(texto):
    if not texto:
        return texto
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def init_db(db_path='customermanagement.db'):
    database = SqliteDatabase(db_path, pragmas={
        'journal_mode': 'wal',
        'foreign_keys': 1,
    })
    database.register_function(unaccent, 'unaccent', 1)
    db.initialize(database)
    return database
