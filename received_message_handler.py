import database
from tinydb import Query


def add_program(data, send_func):
    database.programs_db.upsert(data, Query().name == data['name'])


def modify_program(data, send_func):
    database.programs_db.update(data, Query().name == data['name'])


def get_programs(data, send_func):
    send_func('programs', database.programs_db.all())


def handle(event, data, send_func):
    handlers = {
        'addProgram': add_program,
        'modifyProgram': modify_program,
        'getPrograms': get_programs
    }
    handlers[event](data, send_func)
