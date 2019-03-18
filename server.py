import tornado.ioloop
import tornado.web
import tornado.websocket

from WSHandler import WSHandler
from http_handlers import BaseHandler, ZipFileUploadHandler, SaveNetworkTopologyHandler, LoggingMessageHandler
import constants


def make_server() -> tornado.web.Application:
    return tornado.web.Application([
        (r"/", BaseHandler),
        (r"/uploadZipFile/(.*)", ZipFileUploadHandler),
        (r"/saveNetworkTopology", SaveNetworkTopologyHandler),
        (r'/ws', WSHandler),
        (r'/loggingMessage', LoggingMessageHandler)
    ])


if __name__ == "__main__":
    server = make_server()
    server.listen(constants.DEFAULT_MAIN_SERVER_PORT)
    tornado.ioloop.IOLoop.current().start()
