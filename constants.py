import os

import dict_keys

DEFAULT_SERVER_PORT = 2697

DEFAULT_BASE_IP_ADDRESS = '172.190.0.4'
DEFAULT_NETWORK_SUBNET = '172.190.0.0/16'
DEFAULT_BASE_PORT = 2000
DEFAULT_SELF_CONNECTED_NODES = True

DEFAULT_RAW_NETWORK_TOPOLOGY_CODE = ''
DEFAULT_UNPACKED_NETWORK_TOPOLOGY = []

DOCKER_NETWORK_NAME = 'DIORAMA_NETWORK'

BASE_NODE_FILES_DIRECTORY = os.path.join('.', 'base_node_files')
NODE_ADDRESSES_FILE_NAME: str = 'node_addresses.yml'

NODE_MAIN_FILE_NAME_FOR_RAW = 'node'
USER_NODE_FILES_DIRECTORY_NAME = 'user_node_files'

FILE_EXTENSIONS_FOR_RUNTIME = {
    'python3': '.py',
    'python2': '.py',
    'elixir': '.ex',
    'scala': '.scala'
}

RUNTIME_DATA = {
    'python3': {
        dict_keys.RUNTIME_DATA_WORKING_DIRECTORY: '/usr/src/app',
        dict_keys.RUNTIME_DATA_RUN_COMMAND: ['python', '-u', 'main.py']
    }
}
