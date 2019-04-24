from typing import List, Dict, Any, Callable
import shutil
import os
import tempfile
from ipaddress import IPv4Address

from tinydb import Query
import yaml

import network_topology
import docker_interface
import constants
import database
import programs
import custom_config
import dict_keys
import program_values
import ws_events
import simulation_values
import util


def get_from_simulation_db(type_key: str, result_if_none=None):
    if len(database.simulation_db.search(getattr(Query(), dict_keys.SIMULATION_TYPE) == type_key)) == 0:
        return result_if_none
    return database.simulation_db.search(getattr(Query(), dict_keys.SIMULATION_TYPE) == type_key)[0][
        dict_keys.SIMULATION_DATA]


def store_to_simulation_db(type_key: str, data):
    database.simulation_db.upsert({dict_keys.SIMULATION_TYPE: type_key, dict_keys.SIMULATION_DATA: data},
                                  getattr(Query(), dict_keys.SIMULATION_TYPE) == type_key)


def clear_simulation_data():
    database.simulation_db.purge()


def store_simulation_node_list(simulation_nodes: List[Dict[str, Any]]):
    store_to_simulation_db(dict_keys.SIMULATION_NODE_LIST, simulation_nodes)


def get_simulation_node_list() -> List[Dict[str, Any]]:
    return get_from_simulation_db(dict_keys.SIMULATION_NODE_LIST, result_if_none=[])


def store_simulation_program_list(simulation_programs: List[Dict[str, Any]]):
    for simulation_program in simulation_programs:
        if simulation_program[dict_keys.PROGRAM_CODE_SOURCE] == program_values.CODE_SOURCE_RAW:
            simulation_program[
                dict_keys.PROGRAM_MAIN_HANDLER] = f'{constants.NODE_MAIN_FILE_NAME_FOR_RAW}.' \
                                                  f'{simulation_program[dict_keys.PROGRAM_MAIN_HANDLER]}'
    store_to_simulation_db(dict_keys.SIMULATION_PROGRAM_LIST, simulation_programs)


def get_simulation_program_list() -> List[Dict[str, Any]]:
    return get_from_simulation_db(dict_keys.SIMULATION_PROGRAM_LIST, result_if_none=[])


def store_simulation_config(simulation_config: List[Dict[str, Any]]):
    store_to_simulation_db(dict_keys.SIMULATION_CONFIG, simulation_config)


def get_simulation_config() -> Dict[str, Any]:
    return get_from_simulation_db(dict_keys.SIMULATION_CONFIG, result_if_none={})


def store_simulation_node_addresses(node_addresses: List[Dict[str, Any]]):
    store_to_simulation_db(dict_keys.SIMULATION_NODE_ADDRESSES, node_addresses)


def get_simulation_node_addresses() -> Dict[str, Any]:
    return get_from_simulation_db(dict_keys.SIMULATION_NODE_ADDRESSES, result_if_none={})


def store_simulation_state(simulation_state: str):
    store_to_simulation_db(dict_keys.SIMULATION_STATE, simulation_state)


def get_simulation_state() -> str:
    return get_from_simulation_db(dict_keys.SIMULATION_STATE, result_if_none=simulation_values.UNINITIALISED_STATE)


def clean():
    docker_interface.remove_containers(list(map(lambda node: node[dict_keys.NODE_NID], get_simulation_node_list())))
    docker_interface.remove_images(
        list(map(lambda program: program[dict_keys.PROGRAM_NAME], get_simulation_program_list())))
    docker_interface.remove_network(constants.DOCKER_NETWORK_NAME)


def add_self_connections(simulation_node_list):
    for simulation_node in simulation_node_list:
        simulation_node[dict_keys.NODE_CONNECTIONS] = list(
            set(simulation_node[dict_keys.NODE_CONNECTIONS] + [simulation_node[dict_keys.NODE_NID]]))


def load_simulation_data():
    simulation_node_list = network_topology.get_unpacked_network_topology()
    simulation_config = custom_config.get_custom_config()

    if simulation_config[dict_keys.CUSTOM_CONFIG_SELF_CONNECTED_NODES]:
        add_self_connections(simulation_node_list)

    store_simulation_program_list(programs.get_programs())
    store_simulation_node_list(simulation_node_list)
    store_simulation_config(simulation_config)


def generate_connection_parameters_by_node() -> Dict[str, Dict[str, Dict[str, Any]]]:
    connection_parameters_by_node: Dict[str, Dict[str, Dict[str, Any]]] = {}
    all_connection_parameters: Dict[str, Dict[str, Dict[str, Any]]] = network_topology.get_connection_parameters()
    for from_nid in all_connection_parameters:
        for to_nid in all_connection_parameters[from_nid]:
            if from_nid not in connection_parameters_by_node:
                connection_parameters_by_node[from_nid] = {}
            if to_nid not in connection_parameters_by_node:
                connection_parameters_by_node[to_nid] = {}
            this_connection_parameters: Dict[str, Any] = all_connection_parameters[from_nid][to_nid]
            connection_parameters_by_node[from_nid][to_nid] = this_connection_parameters
            connection_parameters_by_node[to_nid][from_nid] = this_connection_parameters
    return connection_parameters_by_node


def create_node_containers():
    programs_by_name = {program[dict_keys.PROGRAM_NAME]: program for program in get_simulation_program_list()}
    simulation_nodes: List[Dict[str, Any]] = get_simulation_node_list()
    node_addresses = get_simulation_node_addresses()
    nodes = util.combine_dict_lists_by_key([simulation_nodes, node_addresses], dict_keys.NODE_NID)
    for node in nodes:
        program = programs_by_name[node[dict_keys.NODE_PROGRAM]]
        peer_nid_list = ','.join(node[dict_keys.NODE_CONNECTIONS])
        run_args = [peer_nid_list, node[dict_keys.NODE_NID], str(node[dict_keys.NODE_ADDRESSES_PORT]),
                    program[dict_keys.PROGRAM_MAIN_HANDLER]]
        docker_interface.create_container_and_connect(node[dict_keys.NODE_PROGRAM], node[dict_keys.NODE_NID],
                                                      program[dict_keys.PROGRAM_RUNTIME],
                                                      run_args, node[dict_keys.NODE_ADDRESSES_IP_ADDRESS],
                                                      [node[dict_keys.NODE_ADDRESSES_PORT]],
                                                      constants.DOCKER_NETWORK_NAME)


def get_ip_address_for_node_index(index: int, base_ip_address: str) -> str:
    return str(IPv4Address(int(IPv4Address(base_ip_address)) + index))


def generate_node_addresses():
    simulation_config = get_simulation_config()
    base_ip_address = simulation_config[dict_keys.CUSTOM_CONFIG_BASE_IP_ADDRESS]
    node_port = simulation_config[dict_keys.CUSTOM_CONFIG_BASE_PORT]
    return [
        {
            dict_keys.NODE_ADDRESSES_NID: simulation_node[dict_keys.NODE_NID],
            dict_keys.NODE_ADDRESSES_IP_ADDRESS: get_ip_address_for_node_index(index, base_ip_address),
            dict_keys.NODE_ADDRESSES_PORT: node_port
        }
        for index, simulation_node
        in enumerate(get_simulation_node_list())
    ]


def get_code_for_program(program, temp_dir):
    code_source = program[dict_keys.PROGRAM_CODE_SOURCE]
    assert code_source in [program_values.CODE_SOURCE_ZIP, program_values.CODE_SOURCE_GIT,
                           program_values.CODE_SOURCE_RAW]

    dir_to_write_to = os.path.join(temp_dir, constants.USER_NODE_FILES_DIRECTORY_NAME)
    os.mkdir(dir_to_write_to)

    if code_source == program_values.CODE_SOURCE_RAW:
        file_name = ''.join(
            [constants.NODE_MAIN_FILE_NAME_FOR_RAW,
             constants.FILE_EXTENSIONS_FOR_RUNTIME[program[dict_keys.PROGRAM_RUNTIME]]])
        with open(os.path.join(dir_to_write_to, file_name), 'w') as file:
            file.write(program[dict_keys.PROGRAM_CODE_DATA])
    elif code_source == program_values.CODE_SOURCE_ZIP:
        pass
        # TODO
    elif code_source == program_values.CODE_SOURCE_GIT:
        # TODO
        pass


def generate_and_store_node_addresses():
    store_simulation_node_addresses(generate_node_addresses())


def create_program_images(temp_dir: tempfile.TemporaryDirectory):
    node_addresses = get_simulation_node_addresses()
    node_addresses_file_path = os.path.join(str(temp_dir), constants.NODE_ADDRESSES_FILE_NAME)
    with open(node_addresses_file_path, 'w') as node_addresses_file:
        yaml.dump(node_addresses, node_addresses_file, default_flow_style=False)
    connection_parameters_by_node = generate_connection_parameters_by_node()
    connection_parameters_by_node_file_path = os.path.join(str(temp_dir), constants.CONNECTION_PARAMETERS_FILE_NAME)
    with open(connection_parameters_by_node_file_path, 'w') as connection_parameters_by_node_file:
        yaml.dump(connection_parameters_by_node, connection_parameters_by_node_file, default_flow_style=False)
    for program in get_simulation_program_list():
        with tempfile.TemporaryDirectory() as _program_temp_dir:
            program_temp_dir = os.path.join(str(_program_temp_dir), 'tmp')  # workaround as copytree requires empty dst
            shutil.copytree(os.path.join(constants.BASE_NODE_FILES_DIRECTORY, program[dict_keys.PROGRAM_RUNTIME]),
                            program_temp_dir)
            shutil.copy2(node_addresses_file_path, program_temp_dir)
            shutil.copy2(connection_parameters_by_node_file_path, program_temp_dir)
            get_code_for_program(program, program_temp_dir)
            docker_interface.create_image(str(program_temp_dir), program[dict_keys.PROGRAM_NAME])


def create_network():
    network_subnet = get_simulation_config()[dict_keys.CUSTOM_CONFIG_NETWORK_SUBNET]
    docker_interface.create_network(constants.DOCKER_NETWORK_NAME, network_subnet)


def set_up_simulation(send_func: Callable):
    send_func(ws_events.SIMULATION_STATE, simulation_values.INITIALISING_STATE)
    clean()
    clear_simulation_data()
    load_simulation_data()
    generate_and_store_node_addresses()
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            store_simulation_state(simulation_values.CREATING_VIRTUAL_NETWORK_STATE)
            send_func(ws_events.SIMULATION_STATE, simulation_values.CREATING_VIRTUAL_NETWORK_STATE)

            create_network()

            store_simulation_state(simulation_values.CREATING_PROGRAM_IMAGES_STATE)
            send_func(ws_events.SIMULATION_STATE, simulation_values.CREATING_PROGRAM_IMAGES_STATE)

            create_program_images(temp_dir)

            store_simulation_state(simulation_values.CREATING_NODES_STATE)
            send_func(ws_events.SIMULATION_STATE, simulation_values.CREATING_NODES_STATE)

            create_node_containers()

            store_simulation_state(simulation_values.READY_TO_RUN_STATE)
            send_func(ws_events.SIMULATION_STATE, simulation_values.READY_TO_RUN_STATE)
        except Exception as e:
            print(e)
            stop_and_reset_simulation(send_func)


def stop_and_reset_simulation(send_func: Callable):
    store_simulation_state(simulation_values.RESETTING_STATE)
    send_func(ws_events.SIMULATION_STATE, simulation_values.RESETTING_STATE)

    clean()
    clear_simulation_data()

    store_simulation_state(simulation_values.UNINITIALISED_STATE)
    send_func(ws_events.SIMULATION_STATE, simulation_values.UNINITIALISED_STATE)


def get_simulation_nodes():
    if get_simulation_state() not in [simulation_values.READY_TO_RUN_STATE, simulation_values.RUNNING_STATE]:
        return []
    nodes = get_simulation_node_list()
    program_list = get_simulation_program_list()
    program_runtimes: Dict[str, str] = {p[dict_keys.PROGRAM_NAME]: p[dict_keys.PROGRAM_RUNTIME] for p in
                                        program_list}
    program_descriptions: Dict[str, str] = {p[dict_keys.PROGRAM_NAME]: p[dict_keys.PROGRAM_DESCRIPTION] for p in
                                            program_list}
    statuses: Dict[str, str] = docker_interface.get_container_statuses(
        list(map(lambda n: n[dict_keys.NODE_NID], nodes)))
    simulation_nodes: List[Dict[str, Any]] = []
    for node in nodes:
        nid: str = node[dict_keys.NODE_NID]
        program: str = node[dict_keys.NODE_PROGRAM]
        simulation_nodes.append({
            dict_keys.NODE_NID: nid,
            dict_keys.CONTAINER_STATUS: statuses[nid],
            dict_keys.NODE_PROGRAM: node[dict_keys.NODE_PROGRAM],
            dict_keys.PROGRAM_RUNTIME: program_runtimes[program],
            dict_keys.PROGRAM_DESCRIPTION: program_descriptions[program]
        })
    return simulation_nodes


def perform_node_action(data: Dict[str, str]):
    nid = data[dict_keys.NODE_NID]
    action = data[dict_keys.NODE_ACTION]
    docker_interface.action_container(nid, action)


def stream_node_logs(data: Dict[str, str]):
    if 'all' in data:
        for nid in map(lambda node: node[dict_keys.NODE_NID], get_simulation_node_list()):
            docker_interface.stream_container_logs(nid, None)
    else:
        docker_interface.stream_container_logs(data[dict_keys.NODE_NID],
                                               (data[dict_keys.STREAM_SINCE]
                                                if dict_keys.STREAM_SINCE in data
                                                else None))
