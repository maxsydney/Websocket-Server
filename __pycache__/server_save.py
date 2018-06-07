import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import json
from tornado import ioloop

import multiprocessing
import serialprocess
 
from tornado.options import define, options
define("port", default=8080, help="run on the given port", type=int)

count = 6
 
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')
 
class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True
    
    def open(self):
        print('New connection', flush=True)
        self.write_message(json.dumps([1, 2, 3, 4, 5]))
        self.callback = ioloop.PeriodicCallback(self.sendInt, 2)
        self.callback.start()

    def sendInt(self):
        global count
        self.write_message('{}'.format(count))
        count += 1
 
    def on_message(self, message):
        print('message received {}'.format(message), flush=True)
        self.write_message('message received {}'.format(message))
 
    def on_close(self):
        print('connection closed', flush=True)
 
if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/ws", WebSocketHandler)
        ]
    )
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    print("Listening on port:", options.port, flush=True)
    tornado.ioloop.IOLoop.instance().start()
    
