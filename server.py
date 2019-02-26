import tornado.ioloop
import tornado.web
import tornado.websocket
import received_message_handler
import json


class MainHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        self.write("This is the Diorama backend server.")


class WSHandler(tornado.websocket.WebSocketHandler):
    @staticmethod
    def parse_message(message):
        message_dict = json.loads(message)
        return message_dict['event'], (json.loads(message_dict['data']) if 'data' in message_dict else None)

    def data_received(self, chunk):
        pass

    def open(self):
        print('new connection')

    def on_message(self, message):
        event, data = self.parse_message(message)
        received_message_handler.handle(event, data, self.send_message)

    def send_message(self, event, data):
        self.write_message(json.dumps({'event': event, 'data': json.dumps(data)}))

    def on_close(self):
        print('connection closed')

    def check_origin(self, origin):
        return True


def make_server():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r'/ws', WSHandler),
    ])


if __name__ == "__main__":
    server = make_server()
    server.listen(2697)
    tornado.ioloop.IOLoop.current().start()
