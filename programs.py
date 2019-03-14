from typing import List, Dict

from tinydb import Query

import database

NAME_UNIQUE_KEY = 'name'


def add_program(data: Dict):
    database.programs_db.upsert(data, Query().name == data[NAME_UNIQUE_KEY])


def modify_program(data: Dict):
    database.programs_db.update(data, Query().name == data[NAME_UNIQUE_KEY])


def get_programs() -> List[dict]:
    return database.programs_db.all()


def write_zip_file(program_name, file_data):
    with open(f"out/program_zip_files/{program_name}.zip", "wb") as fh:
        fh.write(file_data)
