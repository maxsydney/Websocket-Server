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
		self.LCD = True
		self.taskQ = taskQ
		self.resultQ = resultQ
		self.usbPort = '/dev/serial0'
		self.sp = serial.Serial(self.usbPort, 115200, timeout=1)
		self.initLCD()
	
	def drawTemplate(self):
                self.lcd.cursor_pos = (0, 0)
                self.lcd.write_string("Pissbot V2.0")
                self.lcd.cursor_pos = (1, 0)
                self.lcd.write_string("T1: ")
                self.lcd.cursor_pos = (1, 10)
                self.lcd.write_string("T2: ")
                self.lcd.cursor_pos = (2, 0)
                self.lcd.write_string("Setpoint: ")
                self.lcd.cursor_pos = (3, 0)
                self.lcd.write_string("Runtime: ")		

	def initLCD(self):
	    '''
	    Initialize LCD and set permanent text onscreen. Pre-drawing text cuts
	    loop times in half compared to re-drawing every time
	    '''
	    try:
	    	self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, rows=4, cols=20)
	    	self.drawTemplate()

	    except:
	    	print("WARNING: Unable to connect to LCD")
	    	self.LCD = False 

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
				self.sendData(task.encode())
				# Send stuff to ESP here
 
			# look for incoming serial data
			if (self.sp.inWaiting() > 0):
				data = self.sp.readline()
				try: 
					self.updateLCD(data)
				except Exception as e:
					print("The following error occured")
					print(e)
	 				
				self.resultQ.put(data)
	
	def updateLCD(self, data):
		if self.LCD:
			hotTemp, coldTemp, setpoint, time, *_ = data.decode().split(",")
			formatted_time = str(timedelta(seconds=round(float(time))))
			self.lcd.cursor_pos = (1, 3)
			self.lcd.write_string("{:.2f}".format(float(hotTemp)))
			self.lcd.cursor_pos = (1, 13)
			self.lcd.write_string("{:.2f}".format(float(coldTemp)))
			self.lcd.cursor_pos = (2, 9)
			self.lcd.write_string("{:.2f}".format(float(setpoint)))
			self.lcd.cursor_pos = (3, 8)
			self.lcd.write_string(formatted_time)
