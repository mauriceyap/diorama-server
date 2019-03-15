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


def get_from_simulation_db(type_key: str):
    if len(database.simulation_db.search(getattr(Query(), dict_keys.SIMULATION_TYPE) == type_key)) == 0:
        return []
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
    return get_from_simulation_db(dict_keys.SIMULATION_NODE_LIST)


def store_simulation_program_list(simulation_programs: List[Dict[str, Any]]):
    for simulation_program in simulation_programs:
        if simulation_program[dict_keys.PROGRAM_CODE_SOURCE] == program_values.CODE_SOURCE_RAW:
            simulation_program[
                dict_keys.PROGRAM_MAIN_HANDLER] = f'{constants.NODE_MAIN_FILE_NAME_FOR_RAW}.' \
                                                  f'{simulation_program[dict_keys.PROGRAM_MAIN_HANDLER]}'
    store_to_simulation_db(dict_keys.SIMULATION_PROGRAM_LIST, simulation_programs)


def get_simulation_program_list() -> List[Dict[str, Any]]:
    return get_from_simulation_db(dict_keys.SIMULATION_PROGRAM_LIST)


def store_simulation_config(simulation_config: List[Dict[str, Any]]):
    store_to_simulation_db(dict_keys.SIMULATION_CONFIG, simulation_config)


def get_simulation_config() -> Dict[str, Any]:
    return get_from_simulation_db(dict_keys.SIMULATION_CONFIG)


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


def create_node_containers():
    pass


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
    elif code_source == program_values.CODE_SOURCE_ZIP:
        # TODO
        pass


def create_program_images(temp_dir: tempfile.TemporaryDirectory):
    node_addresses = generate_node_addresses()
    node_addresses_file_path = os.path.join(str(temp_dir), constants.NODE_ADDRESSES_FILE_NAME)
    with open(node_addresses_file_path, 'w') as node_addresses_file:
        yaml.dump(node_addresses, node_addresses_file, default_flow_style=False)
    for program in get_simulation_program_list():
        with tempfile.TemporaryDirectory() as _program_temp_dir:
            program_temp_dir = os.path.join(str(_program_temp_dir), 'tmp')  # workaround as copytree requires empty dst
            shutil.copytree(os.path.join(constants.BASE_NODE_FILES_DIRECTORY, program[dict_keys.PROGRAM_RUNTIME]),
                            program_temp_dir)
            shutil.copy2(node_addresses_file_path, program_temp_dir)
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
    with tempfile.TemporaryDirectory() as temp_dir:
        send_func(ws_events.SIMULATION_STATE, simulation_values.CREATING_VIRTUAL_NETWORK_STATE)
        create_network()
        send_func(ws_events.SIMULATION_STATE, simulation_values.CREATING_PROGRAM_IMAGES_STATE)
        create_program_images(temp_dir)
        # send_func('simulationState', simulation_values.CREATING_NODES_STATE)
        # create_node_containers()
        # send_func('simulationState', simulation_values.READY_TO_RUN_STATE)


def stop_and_reset_simulation(send_func: Callable):
    clean()
    clear_simulation_data()
    send_func(ws_events.SIMULATION_STATE, simulation_values.UNINITIALISED_STATE)
