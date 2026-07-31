import importlib
from peewee import Model

MODEL_MODULES = [
    'database.models.usuarios',
    'database.models.equipamentos',
    'database.models.chamados',
    'database.models.log',
    'database.models.tarefa',
    'database.models.credencial',
    'database.models.emprestimo',
]


def get_all_models():
    tabelas = []
    vistos = set()
    for mod_name in MODEL_MODULES:
        mod = importlib.import_module(mod_name)
        for name in dir(mod):
            obj = getattr(mod, name)
            if (isinstance(obj, type) and issubclass(obj, Model)
                    and obj is not Model and obj.__name__ not in vistos):
                vistos.add(obj.__name__)
                tabelas.append(obj)
    return tabelas
