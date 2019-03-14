import json
from typing import List

import tornado.web

import network_topology
import programs


class GeneralHTTPHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST,OPTIONS')
        self.set_header("Access-Control-Allow-Headers",
                        "access-control-allow-origin,authorization,content-type,x-requested-with")

    def data_received(self, chunk):
        pass

    def options(self, *args):
        self.set_status(204)
        self.finish()


class BaseHandler(GeneralHTTPHandler):
    def get(self):
        self.write("This is the Diorama backend server.")


class ZipFileUploadHandler(GeneralHTTPHandler):
    def post(self, program_name: str):
        programs.write_zip_file(program_name, self.request.body)
        self.write('Upload successful')


class SaveNetworkTopologyHandler(GeneralHTTPHandler):
    # Returns a json object of either:
    # - { isValidAndSaved: true, unpackedTopology: list of objects }
    # - { isValidAndSaved: false, errorMessage: str }
    def post(self):
        body = json.loads(self.request.body)
        language: str = body['language']
        raw_network_topology: str = body['rawNetworkTopology']
        validation_result = network_topology.validate_raw_topology(language, raw_network_topology)
        if validation_result['isValid']:
            topology = validation_result['topology']
            unpacked_topology: List[dict] = network_topology.unpack_topology(topology)
            network_topology.save_raw_network_topology_code(raw_network_topology)
            network_topology.save_unpacked_network_topology(unpacked_topology)
            self.write({'isValidAndSaved': True, 'unpackedTopology': unpacked_topology})
        else:
            self.write({'isValidAndSaved': False, 'errorMessage': validation_result['errorMessage'],
                        'errorData': validation_result['errorData']})
