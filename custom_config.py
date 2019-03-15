from tinydb import Query

import database
import constants
import dict_keys

GET_SINGLETON_QUERY = Query().id == dict_keys.SINGLETON_ID


def initialise_custom_config():
    set_custom_config({
        dict_keys.CUSTOM_CONFIG_BASE_IP_ADDRESS: constants.DEFAULT_BASE_IP_ADDRESS,
        dict_keys.CUSTOM_CONFIG_NETWORK_SUBNET: constants.DEFAULT_NETWORK_SUBNET,
        dict_keys.CUSTOM_CONFIG_SELF_CONNECTED_NODES: constants.DEFAULT_SELF_CONNECTED_NODES,
        dict_keys.CUSTOM_CONFIG_BASE_PORT: constants.DEFAULT_BASE_PORT
    })


def get_custom_config():
    if len(database.custom_config_db.search(GET_SINGLETON_QUERY)) == 0:
        initialise_custom_config()
    return database.custom_config_db.search(GET_SINGLETON_QUERY)[0][dict_keys.CUSTOM_CONFIG]


def set_custom_config(custom_config):
    return database.custom_config_db.upsert(
        {dict_keys.CUSTOM_CONFIG: custom_config, dict_keys.ID: dict_keys.SINGLETON_ID},
        GET_SINGLETON_QUERY)
