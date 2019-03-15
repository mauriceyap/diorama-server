import json
from typing import Dict, Callable

import tornado.websocket

import programs
import network_topology
import custom_config
import simulation
import dict_keys
import ws_events

handlers: Dict[str, Callable] = {
    ws_events.ADD_PROGRAM: (lambda data, _: programs.add_program(data)),
    ws_events.DELETE_PROGRAM: (lambda data, _: programs.delete_program(data)),
    ws_events.MODIFY_PROGRAM: (lambda data, _: programs.modify_program(data)),
    ws_events.GET_PROGRAMS: (lambda _, send_func: send_func(ws_events.PROGRAMS, programs.get_programs())),
    ws_events.GET_RAW_NETWORK_TOPOLOGY: (
        lambda _, send_func: send_func(ws_events.RAW_NETWORK_TOPOLOGY,
                                       network_topology.get_raw_network_topology_code())),
    ws_events.SET_CUSTOM_CONFIG: (lambda data, _: custom_config.set_custom_config(data)),
    ws_events.GET_CUSTOM_CONFIG: (
        lambda _, send_func: send_func(ws_events.CUSTOM_CONFIG, custom_config.get_custom_config())),
    ws_events.SET_UP_SIMULATION: (lambda _, send_func: simulation.set_up_simulation(send_func)),
    ws_events.STOP_AND_RESET_SIMULATION: (lambda _, send_func: simulation.stop_and_reset_simulation(send_func))
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
