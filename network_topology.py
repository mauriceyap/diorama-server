from typing import Dict, Callable, Any, List

import yaml
import json
from tinydb import Query

import database
import constants

RAW_CODE_TYPE = 'rawCode'
UNPACKED_TYPE = 'unpacked'
DATA_KEY = 'data'
TYPE_KEY = 'type'
ERROR_DATA_KEY = 'errorData'
ERROR_MESSAGE_KEY = 'errorMessage'
TOPOLOGY_KEY = 'topology'
IS_VALID_KEY = 'isValid'
ERROR_MESSAGE_PARSING = "NT_ERROR_PARSING"
ERROR_MESSAGE_MUST_BE_MAP = "NT_ERROR_MAP_TYPE"
ERROR_MESSAGE_INVALID_BASE_KEYS = "NT_ERROR_BASE_KEYS"
VALID_BASE_KEYS: List[str] = ['single_nodes', 'node_groups']


class NetworkTopologyValidationException(Exception):
    def __init__(self, message, data=None):
        self.message = message
        self.data = data


def confirm_topology_is_a_dict(topology):
    topology_type = type(topology)
    if topology_type != dict:
        raise NetworkTopologyValidationException(ERROR_MESSAGE_MUST_BE_MAP, topology_type.__name__)


def confirm_all_base_keys_are_valid(topology: Dict[str, List]):
    invalid_keys = [key for key in topology.keys() if key not in VALID_BASE_KEYS]
    if len(invalid_keys) > 0:
        raise NetworkTopologyValidationException(ERROR_MESSAGE_INVALID_BASE_KEYS, invalid_keys)


def validate_topology(topology):
    confirm_topology_is_a_dict(topology)
    confirm_all_base_keys_are_valid(topology)
    # TODO: more validation


parsers: Dict[str, Callable] = {'YAML': yaml.load, 'JSON': json.loads}
parsingErrors: Dict[str, Exception] = {'YAML': yaml.YAMLError, 'JSON': json.JSONDecodeError}


def validate_raw_topology(language: str, raw: str) -> Dict[str, Any]:
    try:
        topology = parsers[language](raw)
        validate_topology(topology)
        return {
            IS_VALID_KEY: True,
            TOPOLOGY_KEY: topology
        }
    except parsingErrors[language] as parsingError:
        return {
            IS_VALID_KEY: False,
            ERROR_MESSAGE_KEY: ERROR_MESSAGE_PARSING,
            ERROR_DATA_KEY: str(parsingError)
        }
    except NetworkTopologyValidationException as validationException:
        return {
            IS_VALID_KEY: False,
            ERROR_MESSAGE_KEY: validationException.message,
            ERROR_DATA_KEY: validationException.data
        }


def unpack_topology(topology: Dict) -> List[Dict]:
    # TODO: node groups
    return topology['single_nodes']


def save_unpacked_network_topology(unpacked_topology: List[Dict]):
    database.network_topology_db.upsert({TYPE_KEY: UNPACKED_TYPE, DATA_KEY: unpacked_topology},
                                        Query().type == UNPACKED_TYPE)


def initialise_unpacked_network_topology():
    save_unpacked_network_topology(constants.DEFAULT_UNPACKED_NETWORK_TOPOLOGY)


def get_unpacked_network_topology() -> List[Dict]:
    if len(database.network_topology_db.search(Query().type == UNPACKED_TYPE)) == 0:
        initialise_unpacked_network_topology()
    return database.network_topology_db.search(Query().type == UNPACKED_TYPE)[0][DATA_KEY]


def save_raw_network_topology_code(raw: str):
    database.network_topology_db.upsert({TYPE_KEY: RAW_CODE_TYPE, DATA_KEY: raw}, Query().type == RAW_CODE_TYPE)


def initialise_raw_network_topology_code():
    save_raw_network_topology_code(constants.DEFAULT_RAW_NETWORK_TOPOLOGY_CODE)


def get_raw_network_topology_code() -> List[Dict]:
    if len(database.network_topology_db.search(Query().type == RAW_CODE_TYPE)) == 0:
        initialise_raw_network_topology_code()
    return database.network_topology_db.search(Query().type == RAW_CODE_TYPE)[0][DATA_KEY]
