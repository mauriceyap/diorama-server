from typing import Dict, Callable, Any, List

import yaml
import json
from tinydb import Query

import database


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


def validate_yaml(raw: str) -> Dict[str, Any]:
    try:
        topology = yaml.load(raw)
        validate_topology(topology)
        return {
            'isValid': True,
            'topology': topology
        }
    except yaml.YAMLError as e:
        return {
            'isValid': False,
            'errorMessage': ERROR_MESSAGE_PARSING,
            'errorData': str(e)
        }
    except NetworkTopologyValidationException as e:
        return {
            'isValid': False,
            'errorMessage': e.message,
            'errorData': e.data
        }


def validate_json(raw: str) -> Dict[str, Any]:
    try:
        topology = json.loads(raw)
        validate_topology(topology)
        return {
            'isValid': True,
            'topology': topology
        }
    except json.JSONDecodeError as e:
        return {
            'isValid': False,
            'errorMessage': ERROR_MESSAGE_PARSING,
            'errorData': str(e)
        }
    except NetworkTopologyValidationException as e:
        return {
            'isValid': False,
            'errorMessage': e.message,
            'errorData': e.data
        }


validators: Dict[str, Callable] = {'YAML': validate_yaml, 'JSON': validate_json}


def validate_raw_topology(language: str, raw: str) -> Dict[str, Any]:
    return validators[language](raw)


def unpack_topology(topology: Dict) -> List[Dict]:
    # TODO: node groups
    return topology['single_nodes']


def save_unpacked_network_topology(unpacked_topology: List[Dict]):
    database.network_topology_db.upsert({'type': 'unpacked', 'data': unpacked_topology}, Query().type == 'unpacked')


def initialise_unpacked_network_topology():
    save_unpacked_network_topology([])


def get_unpacked_network_topology() -> List[Dict]:
    if len(database.network_topology_db.search(Query().type == 'unpacked')) == 0:
        initialise_unpacked_network_topology()
    return database.network_topology_db.search(Query().type == 'unpacked')[0]['data']


def save_raw_network_topology_code(raw: str):
    database.network_topology_db.upsert({'type': 'rawCode', 'data': raw}, Query().type == 'rawCode')


def initialise_raw_network_topology_code():
    save_raw_network_topology_code('')


def get_raw_network_topology_code() -> List[Dict]:
    if len(database.network_topology_db.search(Query().type == 'rawCode')) == 0:
        initialise_raw_network_topology_code()
    return database.network_topology_db.search(Query().type == 'rawCode')[0]['data']
