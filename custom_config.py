from tinydb import Query

import database
import constants

SINGLETON = 'SINGLETON'
GET_SINGLETON_QUERY = Query().id == SINGLETON


def initialise_custom_config():
    set_custom_config({
        'baseIpAddress': constants.DEFAULT_BASE_IP_ADDRESS,
        'networkSubnet': constants.DEFAULT_NETWORK_SUBNET,
        'selfConnectedNodes': constants.DEFAULT_SELF_CONNECTED_NODES,
        'basePort': constants.DEFAULT_BASE_PORT
    })


def get_custom_config():
    if len(database.custom_config_db.search(GET_SINGLETON_QUERY)) == 0:
        initialise_custom_config()
    return database.custom_config_db.search(GET_SINGLETON_QUERY)[0]['customConfig']


def set_custom_config(custom_config):
    return database.custom_config_db.upsert({'customConfig': custom_config, 'id': SINGLETON}, GET_SINGLETON_QUERY)
