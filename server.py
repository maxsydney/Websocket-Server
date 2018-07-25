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
        dataT = list(zip(*data))
        self.write_message(json.dumps({"T1": dataT[0],
				       "T2": dataT[1],
				       "setpoint": dataT[2],
				       "time": dataT[3]}))
 
    def on_message(self, message):
        queue = self.application.settings.get('queue')
        queue.put(message)
 
    def on_close(self):
        try:
            clients.discard(self)
            print('connection closed', flush=True)
        except:
            print("Connection dropped before it could be closed successfully")

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
            T1, T2, setpoint, time = [float(d) for d in inData[:4]]
            data.append([T1, T2, setpoint, time])
            for client in clients:
                client.write_message(json.dumps(inData))

    mainLoop = tornado.ioloop.IOLoop.instance()
    scheduler = tornado.ioloop.PeriodicCallback(get_data, 10)
    scheduler.start()
    mainLoop.start()
    
if __name__ == "__main__":
    main()
