from typing import Dict, Callable, Any, List, Set
import re

import yaml
import json
from tinydb import Query

import database
import constants
import dict_keys
import network_topology_values
import custom_config
import util

ERROR_MESSAGE_PARSING = "NT_ERROR_PARSING"
ERROR_MESSAGE_MUST_BE_MAP = "NT_ERROR_MAP_TYPE"
ERROR_MESSAGE_INVALID_BASE_KEYS = "NT_ERROR_BASE_KEYS"
ERROR_MESSAGE_BASE_VALUE_NOT_LIST_OF_DICTS_TYPE = "NT_ERROR_BASE_VALUE_NOT_LIST_OF_DICTS"
ERROR_MESSAGE_NO_NID_IN_SINGLE_NODES_ITEM = "NT_ERROR_NO_NID_SINGLE_NODES"
ERROR_MESSAGE_NO_PROGRAM_IN_SINGLE_NODES_ITEM = "NT_ERROR_NO_PROGRAM_SINGLE_NODES"
ERROR_MESSAGE_SINGLE_NODES_NID_STRING_TYPE = "NT_ERROR_NID_SINGLE_NODES_NOT_STRING"
ERROR_MESSAGE_SINGLE_NODES_PROGRAM_STRING_TYPE = "NT_ERROR_PROGRAM_SINGLE_NODES_NOT_STRING"
ERROR_MESSAGE_SINGLE_NODES_CONNECTIONS_LIST_OF_STRING_TYPE = "NT_ERROR_CONNECTIONS_SINGLE_NODES_NOT_LIST_OF_STRINGS"
ERROR_MESSAGE_INVALID_NID = "NT_ERROR_INVALID_NID"
VALID_BASE_KEYS: List[str] = [dict_keys.NETWORK_TOPOLOGY_SINGLE_NODES, dict_keys.NETWORK_TOPOLOGY_NODE_GROUPS]
VALID_NID_REGEX: str = r'^[a-zA-Z0-9][a-zA-Z0-9_\.\-]+$'
SINGLE_TYPE_NODE_GROUPS: List[str] = ['line', 'ring', 'fully_connected']


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


def confirm_single_nodes_have_valid_nids(single_nodes: List[Dict[str, Any]]):
    for node in single_nodes:
        nid = node[dict_keys.NODE_NID]
        if not re.match(VALID_NID_REGEX, nid):
            raise NetworkTopologyValidationException(ERROR_MESSAGE_INVALID_NID, nid)


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
    confirm_single_nodes_have_valid_nids(single_nodes)
    # TODO: more validation

    # TODO: nid validation for group nodes [a-zA-Z0-9][a-zA-Z0-9_.-]+


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


def add_line_group_connections(nodes: List[Dict[str, Any]]):
    for index in range(1, len(nodes)):
        nodes[index][dict_keys.NODE_CONNECTIONS] = [nodes[index - 1][dict_keys.NODE_NID]]


def add_ring_group_connections(nodes: List[Dict[str, Any]]):
    add_line_group_connections(nodes)
    nodes[0][dict_keys.NODE_CONNECTIONS] = [nodes[-1][dict_keys.NODE_NID]]


def add_fully_connected_group_connections(nodes: List[Dict[str, Any]]):
    for index in range(0, len(nodes)):
        nodes[index][dict_keys.NODE_CONNECTIONS] = [node[dict_keys.NODE_NID] for node in nodes[(index + 1):]]


add_connection_functions: Dict[str, Callable[[List[Dict[str, Any]]], None]] = {
    'line': add_line_group_connections,
    'ring': add_ring_group_connections,
    'fully_connected': add_fully_connected_group_connections
}


def generate_single_type_node_group(nids: List[str], program: str, group_type: str) -> List[Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = list(
        map(lambda nid: {dict_keys.NODE_NID: nid, dict_keys.NODE_PROGRAM: program}, nids))
    add_connection_functions[group_type](nodes)
    return nodes


def generate_star_node_group(host_nids: List[str], host_program: str, hub_nid: str,
                             hub_program: str) -> List[Dict[str, Any]]:
    hub_node: Dict[str, Any] = {dict_keys.NODE_NID: hub_nid, dict_keys.NODE_PROGRAM: hub_program}
    host_nodes: List[Dict[str, Any]] = list(
        map(lambda nid: {dict_keys.NODE_NID: nid, dict_keys.NODE_PROGRAM: host_program,
                         dict_keys.NODE_CONNECTIONS: [hub_nid]}, host_nids))
    return [hub_node] + host_nodes


def generate_tree_nids(number_levels: int, number_children: int, nid_prefixes: List[str],
                       nid_starting_numbers: List[int], nid_number_increments: List[int],
                       nid_suffixes: List[str]) -> List[List[str]]:
    tree_nids = []
    for level in range(0, number_levels):
        prefix: str = nid_prefixes[level]
        starting_number: int = nid_starting_numbers[level]
        increment: int = nid_number_increments[level]
        suffix: str = nid_suffixes[level]
        tree_nids.append([f'{prefix}{starting_number + node_index * increment}{suffix}'
                          for node_index in range(0, number_children ** level)])
    return tree_nids


def generate_tree_node_group(nids_for_each_level: List[List[str]], programs: List[str], number_levels: int,
                             number_children: int) -> List[Dict[str, Any]]:
    nodes_for_each_level: List[List[Dict[str, Any]]] = [
        [{dict_keys.NODE_NID: nids_for_each_level[level][index_in_level],
          dict_keys.NODE_PROGRAM: programs[level],
          dict_keys.NODE_CONNECTIONS: ([nids_for_each_level[level - 1][index_in_level // number_children]]
                                       if level > 0 else [])
          } for index_in_level in range(0, len(nids_for_each_level[level]))
         ]
        for level in range(0, number_levels)]
    return util.flatten(nodes_for_each_level)


def unpack_node_groups(node_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nodes = []
    for group in node_groups:
        group_nodes = []
        group_type: str = group[dict_keys.NETWORK_TOPOLOGY_GROUP_TYPE]
        if group_type in SINGLE_TYPE_NODE_GROUPS:
            program: str = group[dict_keys.NODE_PROGRAM]
            number_nodes: int = group[dict_keys.NETWORK_TOPOLOGY_GROUP_NUMBER_NODES]
            nid_prefix: str = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_NID_PREFIX]
                               if dict_keys.NETWORK_TOPOLOGY_GROUP_NID_PREFIX in group
                               else constants.DEFAULT_NID_PREFIX)
            nid_suffix: str = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_NID_SUFFIX]
                               if dict_keys.NETWORK_TOPOLOGY_GROUP_NID_SUFFIX in group
                               else constants.DEFAULT_NID_SUFFIX)
            nid_starting_number: int = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_NID_STARTING_NUMBER]
                                        if dict_keys.NETWORK_TOPOLOGY_GROUP_NID_STARTING_NUMBER in group
                                        else constants.DEFAULT_NID_STARTING_NUMBER)
            nid_number_increment: int = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_NID_NUMBER_INCREMENT]
                                         if dict_keys.NETWORK_TOPOLOGY_GROUP_NID_NUMBER_INCREMENT in group
                                         else constants.DEFAULT_NID_NUMBER_INCREMENT)
            nids: List[str] = [f'{nid_prefix}{nid_starting_number + node_index * nid_number_increment}{nid_suffix}' for
                               node_index in range(0, number_nodes)]
            group_nodes.extend(generate_single_type_node_group(nids, program, group_type))
        elif group_type == 'star':
            hub_nid: str = group[dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HUB_NID]
            hub_program: str = group[dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HUB_PROGRAM]
            number_hosts: int = group[dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_NUMBER_HOSTS]
            host_program: str = group[dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HOST_PROGRAM]
            host_nid_prefix: str = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_PREFIX]
                                    if dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_PREFIX in group
                                    else constants.DEFAULT_NID_PREFIX)
            host_nid_suffix: str = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_SUFFIX]
                                    if dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_SUFFIX in group
                                    else constants.DEFAULT_NID_SUFFIX)
            host_nid_starting_number: int = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_STARTING_NUMBER]
                                             if dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_STARTING_NUMBER in group
                                             else constants.DEFAULT_NID_STARTING_NUMBER)
            host_nid_number_increment: int = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_NUMBER_INCREMENT]
                                              if (dict_keys.NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_NUMBER_INCREMENT
                                                  in group)
                                              else constants.DEFAULT_NID_NUMBER_INCREMENT)
            host_nids: List[str] = [f'{host_nid_prefix}'
                                    f'{host_nid_starting_number + host_node_index * host_nid_number_increment}'
                                    f'{host_nid_suffix}'
                                    for host_node_index in range(0, number_hosts)]
            group_nodes.extend(generate_star_node_group(host_nids, host_program, hub_nid, hub_program))
        elif group_type == 'tree':
            number_levels: int = group[dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_NUMBER_LEVELS]
            number_children: int = group[dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_NUMBER_CHILDREN]
            programs: List[str] = group[dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_PROGRAMS]
            nid_prefixes: List[str] = group[dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_NID_PREFIXES]
            nid_starting_numbers: List[int] = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_NID_STARTING_NUMBERS]
                                               if dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_NID_STARTING_NUMBERS in group
                                               else [constants.DEFAULT_NID_STARTING_NUMBER] * number_levels)
            nid_number_increments: List[int] = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_NID_NUMBER_INCREMENTS]
                                                if dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_NID_NUMBER_INCREMENTS in group
                                                else [constants.DEFAULT_NID_NUMBER_INCREMENT] * number_levels)
            nid_suffixes: List[str] = (group[dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_NID_SUFFIXES]
                                       if dict_keys.NETWORK_TOPOLOGY_GROUP_TREE_NID_SUFFIXES in group
                                       else [constants.DEFAULT_NID_SUFFIX] * number_levels)
            nids_for_each_level: List[List[str]] = generate_tree_nids(number_levels, number_children, nid_prefixes,
                                                                      nid_starting_numbers, nid_number_increments,
                                                                      nid_suffixes)
            group_nodes.extend(generate_tree_node_group(nids_for_each_level, programs, number_levels, number_children))

        for node in group_nodes:
            if dict_keys.NODE_CONNECTIONS not in node:
                node[dict_keys.NODE_CONNECTIONS] = []

        if dict_keys.NETWORK_TOPOLOGY_GROUP_CONNECTIONS in group:
            for connection in group[dict_keys.NETWORK_TOPOLOGY_GROUP_CONNECTIONS]:
                nid_from: str = connection[dict_keys.NETWORK_TOPOLOGY_GROUP_CONNECTIONS_FROM]
                nid_to: str = connection[dict_keys.NETWORK_TOPOLOGY_GROUP_CONNECTIONS_TO]
                for node in group_nodes:
                    if node[dict_keys.NODE_NID] == nid_from:
                        node[dict_keys.NODE_CONNECTIONS].extend([nid_to])
                    elif node[dict_keys.NODE_NID] == nid_to:
                        node[dict_keys.NODE_CONNECTIONS].extend([nid_from])
        nodes.extend(group_nodes)

    return nodes


def unpack_topology(topology: Dict[str, Any]) -> List[Dict[str, Any]]:
    single_nodes = (topology[dict_keys.NETWORK_TOPOLOGY_SINGLE_NODES].copy()
                    if dict_keys.NETWORK_TOPOLOGY_SINGLE_NODES in topology
                    else [])
    group_nodes = (unpack_node_groups(topology[dict_keys.NETWORK_TOPOLOGY_NODE_GROUPS])
                   if dict_keys.NETWORK_TOPOLOGY_NODE_GROUPS in topology
                   else [])

    is_nodes_self_connected = custom_config.get_custom_config()[dict_keys.CUSTOM_CONFIG_SELF_CONNECTED_NODES]
    nodes = single_nodes + group_nodes
    for node in nodes:
        if dict_keys.NODE_CONNECTIONS not in node:
            node[dict_keys.NODE_CONNECTIONS] = []
        if is_nodes_self_connected:
            node[dict_keys.NODE_CONNECTIONS] = list(set(node[dict_keys.NODE_CONNECTIONS] + [node[dict_keys.NODE_NID]]))

    for node in nodes:
        peer_nids = node[dict_keys.NODE_CONNECTIONS]
        peer_nodes = filter(lambda n: n[dict_keys.NODE_NID] in peer_nids, nodes)
        for peer_node in peer_nodes:
            peer_node[dict_keys.NODE_CONNECTIONS] = list(
                set(peer_node[dict_keys.NODE_CONNECTIONS] + [node[dict_keys.NODE_NID]]))

    return nodes


def update_unpacked_topology_with_self_connected_nodes():
    language = get_raw_network_topology_language()
    raw = get_raw_network_topology_code()
    topology = parsers[language](raw)
    save_unpacked_network_topology(unpack_topology(topology))
    update_self_connection_parameters()


def save_unpacked_network_topology(unpacked_topology: List[Dict]):
    database.network_topology_db.upsert(
        {dict_keys.NETWORK_TOPOLOGY_TYPE: network_topology_values.NETWORK_TOPOLOGY_UNPACKED_TYPE,
         dict_keys.NETWORK_TOPOLOGY_DATA: unpacked_topology},
        Query().type == network_topology_values.NETWORK_TOPOLOGY_UNPACKED_TYPE)


def initialise_unpacked_network_topology():
    save_unpacked_network_topology(constants.DEFAULT_UNPACKED_NETWORK_TOPOLOGY)


def get_unpacked_network_topology() -> List[Dict]:
    if len(database.network_topology_db.search(
            Query().type == network_topology_values.NETWORK_TOPOLOGY_UNPACKED_TYPE)) == 0:
        initialise_unpacked_network_topology()
    return \
        database.network_topology_db.search(Query().type == network_topology_values.NETWORK_TOPOLOGY_UNPACKED_TYPE)[0][
            dict_keys.NETWORK_TOPOLOGY_DATA]


def save_raw_network_topology_code(raw: str):
    database.network_topology_db.upsert(
        {dict_keys.NETWORK_TOPOLOGY_TYPE: network_topology_values.NETWORK_TOPOLOGY_RAW_CODE_TYPE,
         dict_keys.NETWORK_TOPOLOGY_DATA: raw},
        Query().type == network_topology_values.NETWORK_TOPOLOGY_RAW_CODE_TYPE)


def initialise_raw_network_topology_code():
    save_raw_network_topology_code(constants.DEFAULT_RAW_NETWORK_TOPOLOGY_CODE)


def get_raw_network_topology_code() -> List[Dict]:
    if len(database.network_topology_db.search(
            Query().type == network_topology_values.NETWORK_TOPOLOGY_RAW_CODE_TYPE)) == 0:
        initialise_raw_network_topology_code()
    return \
        database.network_topology_db.search(Query().type == network_topology_values.NETWORK_TOPOLOGY_RAW_CODE_TYPE)[0][
            dict_keys.NETWORK_TOPOLOGY_DATA]


def save_raw_network_topology_language(language: str):
    database.network_topology_db.upsert(
        {dict_keys.NETWORK_TOPOLOGY_TYPE: network_topology_values.NETWORK_TOPOLOGY_RAW_LANGUAGE_TYPE,
         dict_keys.NETWORK_TOPOLOGY_DATA: language},
        Query().type == network_topology_values.NETWORK_TOPOLOGY_RAW_LANGUAGE_TYPE)


def initialise_raw_network_topology_language():
    save_raw_network_topology_code(constants.DEFAULT_RAW_NETWORK_TOPOLOGY_LANGUAGE)


def get_raw_network_topology_language() -> str:
    if len(database.network_topology_db.search(
            Query().type == network_topology_values.NETWORK_TOPOLOGY_RAW_LANGUAGE_TYPE)) == 0:
        initialise_raw_network_topology_code()
    return \
        database.network_topology_db.search(Query().type == network_topology_values.NETWORK_TOPOLOGY_RAW_LANGUAGE_TYPE)[
            0][
            dict_keys.NETWORK_TOPOLOGY_DATA]


def save_connection_parameters(connection_parameters: Dict[str, Dict[str, Dict[str, Any]]]):
    database.network_topology_db.upsert(
        {dict_keys.NETWORK_TOPOLOGY_TYPE: network_topology_values.NETWORK_TOPOLOGY_CONNECTION_PARAMETERS_TYPE,
         dict_keys.NETWORK_TOPOLOGY_DATA: connection_parameters},
        Query().type == network_topology_values.NETWORK_TOPOLOGY_CONNECTION_PARAMETERS_TYPE
    )


def initialise_connection_parameters():
    save_connection_parameters({})


def get_connection_parameters() -> Dict[str, Dict[str, Dict[str, Any]]]:
    if len(database.network_topology_db.search(
            Query().type == network_topology_values.NETWORK_TOPOLOGY_CONNECTION_PARAMETERS_TYPE)) == 0:
        initialise_connection_parameters()
    return \
        database.network_topology_db.search(
            Query().type == network_topology_values.NETWORK_TOPOLOGY_CONNECTION_PARAMETERS_TYPE)[
            0][
            dict_keys.NETWORK_TOPOLOGY_DATA]


def save_initial_connection_parameters():
    unpacked_topology: List[dict] = get_unpacked_network_topology()
    connection_parameters: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for node in unpacked_topology:
        nid = node[dict_keys.NODE_NID]
        connections = node[dict_keys.NODE_CONNECTIONS]
        for connection_nid in connections:
            if connection_nid >= nid:
                if nid not in connection_parameters:
                    connection_parameters[nid] = {}
                connection_parameters[nid][connection_nid] = constants.DEFAULT_CONNECTION_PARAMETERS
    save_connection_parameters(connection_parameters)


def update_self_connection_parameters():
    connection_parameters: Dict[str, Dict[str, Dict[str, Any]]] = get_connection_parameters()
    unpacked_topology: List[dict] = get_unpacked_network_topology()
    for node in unpacked_topology:
        nid: str = node[dict_keys.NODE_NID]
        is_node_self_connected: bool = nid in node[dict_keys.NODE_CONNECTIONS]
        if is_node_self_connected:
            if nid in connection_parameters:
                if nid not in connection_parameters[nid]:
                    connection_parameters[nid][nid] = constants.DEFAULT_CONNECTION_PARAMETERS
            else:
                connection_parameters[nid] = {nid: constants.DEFAULT_CONNECTION_PARAMETERS}
        else:
            connection_parameters_keys_to_remove: Set[str] = set()  # remove empty dictionaries
            if nid in connection_parameters[nid]:
                del connection_parameters[nid][nid]
            if len(connection_parameters[nid]) == 0:
                connection_parameters_keys_to_remove.add(nid)
            for nid_to_remove in connection_parameters_keys_to_remove:
                del connection_parameters[nid_to_remove]
    save_connection_parameters(connection_parameters)


def modify_connection_parameters(from_nid: str, to_nid: str, parameters: Dict[str, Any]):
    connection_parameters: Dict[str, Dict[str, Dict[str, Any]]] = get_connection_parameters()
    connection_parameters[from_nid][to_nid] = parameters
    save_connection_parameters(connection_parameters)
