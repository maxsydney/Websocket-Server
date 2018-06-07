import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import logging
import json
from tornado import ioloop

import multiprocessing
import serialProcess

logger = multiprocessing.log_to_stderr(logging.INFO)
 
from tornado.options import define, options
define("port", default=8080, help="run on the given port", type=int)

count = 6
data = []          # n x 3 matrix of data
clients = set()
 
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')
 
class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True
    
    def open(self):
        print('New connection', flush=True)
        clients.add(self)
        self.write_message(json.dumps(str(zip(*data))))		# Transpose to a 3 x n
 
    def on_message(self, message):
        print('message received {}'.format(message), flush=True)
        self.write_message('message received {}'.format(message))
 
    def on_close(self):
        clients.discard(self)
        print('connection closed', flush=True)

def main():
    taskQ = multiprocessing.Queue()
    outQ = multiprocessing.Queue()
    sp = serialProcess.SerialProcess(taskQ, outQ)
    sp.daemon = True
    sp.start()    

    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/ws", WebSocketHandler)
        ], queue=taskQ
    )
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    print("Listening on port:", options.port, flush=True)
 	
    def get_data():
        if not outQ.empty():
            inData = outQ.get().decode().split(',')
            temp, setpoint, time = [float(d) for d in inData[:3]]
            data.append([temp, setpoint, time])
            for client in clients:
                client.write_message(json.dumps([temp, setpoint, time]))
                #client.write_message("{}".format(temp))
                #print("Got {} from serial".format(temp), flush=True)

    mainLoop = tornado.ioloop.IOLoop.instance()
    scheduler = tornado.ioloop.PeriodicCallback(get_data, 10)
    scheduler.start()
    mainLoop.start()
    
if __name__ == "__main__":
    main()
