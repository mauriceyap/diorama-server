ID = 'id'
SINGLETON_ID = 'SINGLETON'

WS_EVENT = 'event'
WS_DATA = 'data'


CUSTOM_CONFIG = 'customConfig'
CUSTOM_CONFIG_BASE_IP_ADDRESS = 'baseIpAddress'
CUSTOM_CONFIG_NETWORK_SUBNET = 'networkSubnet'
CUSTOM_CONFIG_SELF_CONNECTED_NODES = 'selfConnectedNodes'
CUSTOM_CONFIG_BASE_PORT = 'basePort'

NETWORK_TOPOLOGY_DATA = 'data'
NETWORK_TOPOLOGY_TYPE = 'type'
NETWORK_TOPOLOGY_ERROR_DATA = 'errorData'
NETWORK_TOPOLOGY_ERROR_MESSAGE = 'errorMessage'
NETWORK_TOPOLOGY_TOPOLOGY = 'topology'
NETWORK_TOPOLOGY_IS_VALID = 'isValid'
NETWORK_TOPOLOGY_SINGLE_NODES = 'single_nodes'
NETWORK_TOPOLOGY_NODE_GROUPS = 'node_groups'
NETWORK_TOPOLOGY_LANGUAGE = 'language'
NETWORK_TOPOLOGY_GROUP_TYPE = 'type'
NETWORK_TOPOLOGY_GROUP_NID_STARTING_NUMBER = 'nid_starting_number'
NETWORK_TOPOLOGY_GROUP_NID_NUMBER_INCREMENT = 'nid_number_increment'
NETWORK_TOPOLOGY_GROUP_NID_PREFIX = 'nid_prefix'
NETWORK_TOPOLOGY_GROUP_NID_SUFFIX = 'nid_suffix'
NETWORK_TOPOLOGY_GROUP_NUMBER_NODES = 'number_nodes'
NETWORK_TOPOLOGY_GROUP_CONNECTIONS = 'connections'
NETWORK_TOPOLOGY_GROUP_CONNECTIONS_FROM = 'from'
NETWORK_TOPOLOGY_GROUP_CONNECTIONS_TO = 'to'
NETWORK_TOPOLOGY_GROUP_STAR_HUB_NID = 'hub_nid'
NETWORK_TOPOLOGY_GROUP_STAR_HUB_PROGRAM = 'hub_program'
NETWORK_TOPOLOGY_GROUP_STAR_NUMBER_HOSTS = 'number_hosts'
NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_STARTING_NUMBER = 'host_nid_starting_number'
NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_NUMBER_INCREMENT = 'host_nid_number_increment'
NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_PREFIX = 'host_nid_prefix'
NETWORK_TOPOLOGY_GROUP_STAR_HOST_NID_SUFFIX = 'host_nid_suffix'
NETWORK_TOPOLOGY_GROUP_STAR_HOST_PROGRAM = 'host_program'
NETWORK_TOPOLOGY_GROUP_TREE_NUMBER_LEVELS = 'number_levels'
NETWORK_TOPOLOGY_GROUP_TREE_NUMBER_CHILDREN = 'number_children'
NETWORK_TOPOLOGY_GROUP_TREE_PROGRAMS = 'programs'
NETWORK_TOPOLOGY_GROUP_TREE_NID_PREFIXES = 'nid_prefixes'
NETWORK_TOPOLOGY_GROUP_TREE_NID_STARTING_NUMBERS = 'nid_starting_numbers'
NETWORK_TOPOLOGY_GROUP_TREE_NID_NUMBER_INCREMENTS = 'nid_number_increments'
NETWORK_TOPOLOGY_GROUP_TREE_NID_SUFFIXES = 'nid_suffixes'

NODE_CONNECTIONS_PARAMETERS_SUCCESS_RATE = 'successRate'
NODE_CONNECTIONS_PARAMETERS_DELAY_DISTRIBUTION = 'delayDistribution'
NODE_CONNECTIONS_PARAMETERS_DELAY_DISTRIBUTION_PARAMETERS = 'delayDistributionParameters'
MODIFY_NODE_CONNECTIONS_FROM_NID = 'fromNid'
MODIFY_NODE_CONNECTIONS_TO_NID = 'toNid'
MODIFY_NODE_CONNECTIONS_PARAMETERS = 'parameters'

NODE_CONNECTIONS = 'connections'
NODE_NID = 'nid'
NODE_PROGRAM = 'program'

PROGRAM_NAME = 'name'
PROGRAM_CODE_SOURCE = 'codeSource'
PROGRAM_CODE_DATA = 'codeData'
PROGRAM_RUNTIME = 'runtime'
PROGRAM_DESCRIPTION = 'description'
PROGRAM_MAIN_HANDLER = 'mainHandler'
PROGRAM_CODE_DATA_RAW_CODE = 'code'
PROGRAM_CODE_DATA_RAW_CODE_DEPENDENCIES = 'dependencies'
PROGRAM_CODE_DATA_GIT_REPO_URL = 'repositoryUrl'
PROGRAM_CODE_DATA_GIT_CHECKOUT_BRANCH_OR_TAG = 'checkoutBranchOrTag'

SIMULATION_NODE_LIST: str = 'simulationNodeList'
SIMULATION_PROGRAM_LIST: str = 'simulationProgramList'
SIMULATION_CURRENT_SIMULATION_HASH: str = 'currentSimulationHash'
SIMULATION_CONFIG: str = 'simulationConfigKey'
SIMULATION_NODE_ADDRESSES: str = 'simulationNodeAddresses'
SIMULATION_DATA: str = 'data'
SIMULATION_TYPE: str = 'type'
SIMULATION_STATE: str = 'state'
SIMULATION_PROGRAMS: str = 'programs'

NODE_ADDRESSES_NID = 'nid'
NODE_ADDRESSES_IP_ADDRESS = 'ip_address'
NODE_ADDRESSES_PORT = 'port'

CONTAINER_STATUS = 'status'

LOG_TIMESTAMP = 'timestamp'
LOG_MESSAGE = 'message'

RUNTIME_DATA_WORKING_DIRECTORY = 'workingDirectory'
RUNTIME_DATA_RUN_COMMAND = 'runCommand'

NODE_ACTION: str = 'action'

STREAM_SINCE: str = 'since'
