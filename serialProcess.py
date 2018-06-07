import serial
import time
import multiprocessing
from RPLCD.i2c import CharLCD
from datetime import timedelta
 
class SerialProcess(multiprocessing.Process):
	'''
	This subprocess handles the serial communications with the ESP32 and 
	runs the drivers for the LCD display. Communication with Tornado server
	is done via two queues. One for relaying data to webserver, and one to 
	receive messages to pass to ESP
	'''
 
	def __init__(self, taskQ, resultQ):
		multiprocessing.Process.__init__(self)
		self.taskQ = taskQ
		self.resultQ = resultQ
		self.usbPort = '/dev/serial0'
		self.sp = serial.Serial(self.usbPort, 115200, timeout=1)
		self.initLCD()
	
	def initLCD(self):
	    '''
	    Initialize LCD and set permanent text onscreen. Pre-drawing text cuts
	    loop times in half compared to re-drawing every time
	    '''
	    self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, rows=4, cols=20)
	    self.lcd.write_string("Pissbot V1.0")
	    self.lcd.cursor_pos = (1, 0)
	    self.lcd.write_string("Temp: ")
	    self.lcd.cursor_pos = (2, 0)
	    self.lcd.write_string("Setpoint: ")
	    self.lcd.cursor_pos = (3, 0)
	    self.lcd.write_string("Runtime: ")
 
	def close(self):
		self.sp.close()
 
	def sendData(self, data):
		self.sp.write(data)
		time.sleep(3)
 
	def run(self):
 
		self.sp.flushInput()
 
		while True:
			if not self.taskQ.empty():
				task = self.taskQ.get()
				# Send stuff to ESP here
 
			# look for incoming serial data
			if (self.sp.inWaiting() > 0):
				data = self.sp.readline()
				self.updateLCD(data)
				self.resultQ.put(data)
	
	def updateLCD(self, data):
		temp, setpoint, time, *_ = data.decode().split(",")
		formatted_time = str(timedelta(seconds=round(float(time))))
		self.lcd.cursor_pos = (1, 5)
		self.lcd.write_string("{:.2f}".format(float(temp)))
		self.lcd.cursor_pos = (2, 9)
		self.lcd.write_string("{:.2f}".format(float(setpoint)))
		self.lcd.cursor_pos = (3, 8)
		self.lcd.write_string(formatted_time)
