from typing import List, Dict

from tinydb import Query

import database
import dict_keys


def add_program(data: Dict):
    database.programs_db.upsert(data, Query().name == data[dict_keys.PROGRAM_NAME])


def modify_program(data: Dict):
    database.programs_db.update(data, Query().name == data[dict_keys.PROGRAM_NAME])


def get_programs() -> List[dict]:
    return database.programs_db.all()


def delete_program(name: str):
    database.programs_db.remove(getattr(Query(), dict_keys.PROGRAM_NAME) == name)


def write_zip_file(program_name, file_data):
    with open(f"out/program_zip_files/{program_name}.zip", "wb") as fh:
        fh.write(file_data)
