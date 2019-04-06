from typing import Dict, Callable, Any, List

import yaml
import json
from tinydb import Query

import database
import constants
import dict_keys
import network_topology_values

ERROR_MESSAGE_PARSING = "NT_ERROR_PARSING"
ERROR_MESSAGE_MUST_BE_MAP = "NT_ERROR_MAP_TYPE"
ERROR_MESSAGE_INVALID_BASE_KEYS = "NT_ERROR_BASE_KEYS"
ERROR_MESSAGE_BASE_VALUE_NOT_LIST_OF_DICTS_TYPE = "NT_ERROR_BASE_VALUE_NOT_LIST_OF_DICTS"
ERROR_MESSAGE_NO_NID_IN_SINGLE_NODES_ITEM = "NT_ERROR_NO_NID_SINGLE_NODES"
ERROR_MESSAGE_NO_PROGRAM_IN_SINGLE_NODES_ITEM = "NT_ERROR_NO_PROGRAM_SINGLE_NODES"
ERROR_MESSAGE_SINGLE_NODES_NID_STRING_TYPE = "NT_ERROR_NID_SINGLE_NODES_NOT_STRING"
ERROR_MESSAGE_SINGLE_NODES_PROGRAM_STRING_TYPE = "NT_ERROR_PROGRAM_SINGLE_NODES_NOT_STRING"
ERROR_MESSAGE_SINGLE_NODES_CONNECTIONS_LIST_OF_STRING_TYPE = "NT_ERROR_CONNECTIONS_SINGLE_NODES_NOT_LIST_OF_STRINGS"
VALID_BASE_KEYS: List[str] = [dict_keys.NETWORK_TOPOLOGY_SINGLE_NODES, dict_keys.NETWORK_TOPOLOGY_NODE_GROUPS]
SINGLE_TYPE_NODE_GROUPS: List[str] = ['line', 'bus', 'ring', 'fully_connected']


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


def confirm_all_values_are_lists_of_dicts(topology: Dict[str, List]):
    for key in VALID_BASE_KEYS:
        if key in topology:
            if type(topology[key]) != list:
                raise NetworkTopologyValidationException(ERROR_MESSAGE_BASE_VALUE_NOT_LIST_OF_DICTS_TYPE, key)
            else:
                for item in topology[key]:
                    if type(item) != dict:
                        raise NetworkTopologyValidationException(ERROR_MESSAGE_BASE_VALUE_NOT_LIST_OF_DICTS_TYPE, key)


def confirm_single_nodes_include_nid(single_nodes: List[Dict[str, Any]]):
    for index, node in enumerate(single_nodes):
        if dict_keys.NODE_NID not in node:
            raise NetworkTopologyValidationException(ERROR_MESSAGE_NO_NID_IN_SINGLE_NODES_ITEM, index + 1)


def confirm_single_nodes_include_program(single_nodes: List[Dict[str, Any]]):
    for index, node in enumerate(single_nodes):
        if dict_keys.NODE_PROGRAM not in node:
            raise NetworkTopologyValidationException(ERROR_MESSAGE_NO_PROGRAM_IN_SINGLE_NODES_ITEM, index + 1)


def confirm_single_nodes_nid_string_type(single_nodes: List[Dict[str, Any]]):
    for index, node in enumerate(single_nodes):
        if type(node[dict_keys.NODE_NID]) != str:
            raise NetworkTopologyValidationException(ERROR_MESSAGE_SINGLE_NODES_NID_STRING_TYPE, index + 1)


def confirm_single_nodes_program_string_type(single_nodes: List[Dict[str, Any]]):
    for index, node in enumerate(single_nodes):
        if type(node[dict_keys.NODE_PROGRAM]) != str:
            raise NetworkTopologyValidationException(ERROR_MESSAGE_SINGLE_NODES_PROGRAM_STRING_TYPE, index + 1)


def confirm_single_nodes_connections_list_of_strings_type(single_nodes: List[Dict[str, Any]]):
    for index, node in enumerate(single_nodes):
        if dict_keys.NODE_CONNECTIONS in node:
            connections = node[dict_keys.NODE_CONNECTIONS]
            if type(connections) != list:
                raise NetworkTopologyValidationException(ERROR_MESSAGE_SINGLE_NODES_CONNECTIONS_LIST_OF_STRING_TYPE,
                                                         index + 1)
            for connection in connections:
                if type(connection) != str:
                    raise NetworkTopologyValidationException(ERROR_MESSAGE_SINGLE_NODES_CONNECTIONS_LIST_OF_STRING_TYPE,
                                                             index + 1)


def validate_topology(topology):
    confirm_topology_is_a_dict(topology)
    confirm_all_base_keys_are_valid(topology)
    confirm_all_values_are_lists_of_dicts(topology)

    # Single nodes
    single_nodes = topology[dict_keys.NETWORK_TOPOLOGY_SINGLE_NODES]
    confirm_single_nodes_include_nid(single_nodes)
    confirm_single_nodes_include_program(single_nodes)
    confirm_single_nodes_nid_string_type(single_nodes)
    confirm_single_nodes_program_string_type(single_nodes)
    confirm_single_nodes_connections_list_of_strings_type(single_nodes)
    # TODO: more validation


parsers: Dict[str, Callable] = {'YAML': lambda raw: yaml.load(raw, Loader=yaml.FullLoader), 'JSON': json.loads}
parsingErrors: Dict[str, Exception] = {'YAML': yaml.YAMLError, 'JSON': json.JSONDecodeError}


def validate_raw_topology(language: str, raw: str) -> Dict[str, Any]:
    try:
        topology = parsers[language](raw)
        validate_topology(topology)
        return {
            dict_keys.NETWORK_TOPOLOGY_IS_VALID: True,
            dict_keys.NETWORK_TOPOLOGY_TOPOLOGY: topology
        }
    except parsingErrors[language] as parsingError:
        return {
            dict_keys.NETWORK_TOPOLOGY_IS_VALID: False,
            dict_keys.NETWORK_TOPOLOGY_ERROR_MESSAGE: ERROR_MESSAGE_PARSING,
            dict_keys.NETWORK_TOPOLOGY_ERROR_DATA: str(parsingError)
        }
    except NetworkTopologyValidationException as validationException:
        return {
            dict_keys.NETWORK_TOPOLOGY_IS_VALID: False,
            dict_keys.NETWORK_TOPOLOGY_ERROR_MESSAGE: validationException.message,
            dict_keys.NETWORK_TOPOLOGY_ERROR_DATA: validationException.data
        }


def unpack_topology(topology: Dict) -> List[Dict]:
    nodes = topology[dict_keys.NETWORK_TOPOLOGY_SINGLE_NODES]
    # TODO: node groups

    for node in nodes:
        if dict_keys.NODE_CONNECTIONS not in node:
            node[dict_keys.NODE_CONNECTIONS] = []

    for node in nodes:
        peer_nids = node[dict_keys.NODE_CONNECTIONS]
        peer_nodes = filter(lambda n: n[dict_keys.NODE_NID] in peer_nids, nodes)
        for peer_node in peer_nodes:
            peer_node[dict_keys.NODE_CONNECTIONS] = list(
                set(peer_node[dict_keys.NODE_CONNECTIONS] + [node[dict_keys.NODE_NID]]))

    return nodes


def save_unpacked_network_topology(unpacked_topology: List[Dict]):
    database.network_topology_db.upsert(
        {dict_keys.NETWORK_TOPOLOGY_TYPE: network_topology_values.NETWORK_TOPOLOGY_UNPACKED_TYPE,
         dict_keys.NETWORK_TOPOLOGY_DATA: unpacked_topology},
        Query().type == network_topology_values.NETWORK_TOPOLOGY_UNPACKED_TYPE)


def initialise_unpacked_network_topology():
    save_unpacked_network_topology(constants.DEFAULT_UNPACKED_NETWORK_TOPOLOGY)


def get_unpacked_network_topology() -> List[Dict]:
    if len(database.network_topology_db.search(Query().type == network_topology_values.NETWORK_TOPOLOGY_UNPACKED_TYPE)) == 0:
        initialise_unpacked_network_topology()
    return database.network_topology_db.search(Query().type == network_topology_values.NETWORK_TOPOLOGY_UNPACKED_TYPE)[0][
        dict_keys.NETWORK_TOPOLOGY_DATA]


def save_raw_network_topology_code(raw: str):
    database.network_topology_db.upsert(
        {dict_keys.NETWORK_TOPOLOGY_TYPE: network_topology_values.NETWORK_TOPOLOGY_RAW_CODE_TYPE,
         dict_keys.NETWORK_TOPOLOGY_DATA: raw},
        Query().type == network_topology_values.NETWORK_TOPOLOGY_RAW_CODE_TYPE)


def initialise_raw_network_topology_code():
    save_raw_network_topology_code(constants.DEFAULT_RAW_NETWORK_TOPOLOGY_CODE)


def get_raw_network_topology_code() -> List[Dict]:
    if len(database.network_topology_db.search(Query().type == network_topology_values.NETWORK_TOPOLOGY_RAW_CODE_TYPE)) == 0:
        initialise_raw_network_topology_code()
    return database.network_topology_db.search(Query().type == network_topology_values.NETWORK_TOPOLOGY_RAW_CODE_TYPE)[0][
        dict_keys.NETWORK_TOPOLOGY_DATA]
