from flask_caching import Cache

TTL_PADRAO = 60

cache = Cache()


def init_cache(app):
    cache.init_app(app, config={
        'CACHE_TYPE': app.config.get('CACHE_TYPE', 'SimpleCache'),
        'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', TTL_PADRAO),
        'CACHE_REDIS_URL': app.config.get('CACHE_REDIS_URL'),
    })


def get(chave):
    return cache.get(chave)


def set(chave, valor, ttl=None):
    cache.set(chave, valor, timeout=ttl or TTL_PADRAO)


def invalidate(chave=None):
    if chave:
        cache.delete(chave)
    else:
        cache.clear()
