import json
from typing import Dict, Callable

import tornado.websocket

import programs
import network_topology
import custom_config
import simulation
import dict_keys

handlers: Dict[str, Callable] = {
    'addProgram': (lambda data, _: programs.add_program(data)),
    'deleteProgram': (lambda data, _: programs.delete_program(data)),
    'modifyProgram': (lambda data, _: programs.modify_program(data)),
    'getPrograms': (lambda _, send_func: send_func('programs', programs.get_programs())),
    'getRawNetworkTopology': (
        lambda _, send_func: send_func('rawNetworkTopology', network_topology.get_raw_network_topology_code())),
    'setCustomConfig': (lambda data, _: custom_config.set_custom_config(data)),
    'getCustomConfig': (lambda _, send_func: send_func('customConfig', custom_config.get_custom_config())),
    'setUpSimulation': (lambda _, send_func: simulation.set_up_simulation(send_func)),
    'stopAndResetSimulation': (lambda _, send_func: simulation.stop_and_reset_simulation(send_func))
}


def handle(event: str, data, send_func: Callable):
    handlers[event](data, send_func)


class WSHandler(tornado.websocket.WebSocketHandler):
    @staticmethod
    def parse_message(message):
        message_dict = json.loads(message)
        return message_dict[dict_keys.WS_EVENT], (
            json.loads(message_dict[dict_keys.WS_DATA]) if dict_keys.WS_DATA in message_dict else None)

    def data_received(self, chunk):
        pass

    def open(self):
        print('new ws connection')

    def on_message(self, message):
        event, data = self.parse_message(message)
        handle(event, data, self.send_message)

    def send_message(self, event, data):
        self.write_message(json.dumps({dict_keys.WS_EVENT: event, dict_keys.WS_DATA: json.dumps(data)}))

    def on_close(self):
        print('ws connection closed')

    def check_origin(self, origin):
        return True
