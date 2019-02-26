import database
from tinydb import Query
import base64


def add_program(data, send_func):
    database.programs_db.upsert(data, Query().name == data['name'])


def modify_program(data, send_func):
    database.programs_db.update(data, Query().name == data['name'])


def get_programs(data, send_func):
    send_func('programs', database.programs_db.all())


def upload_program_zip_file(data, send_func):
    with open(f"out/program_zip_files/{data['programName']}.zip", "wb") as fh:
        fh.write(base64.b64decode(data['fileDataBase64']))
    with open(f"out/program_zip_files/{data['programName']}.txt", "wb") as fh:
        fh.write(bytes(data['fileDataBase64'], 'utf-8'))


def handle(event, data, send_func):
    handlers = {
        'addProgram': add_program,
        'modifyProgram': modify_program,
        'getPrograms': get_programs,
        'uploadProgramZipFile': upload_program_zip_file
    }
    handlers[event](data, send_func)
