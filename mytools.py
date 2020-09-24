import time
import os
import json
from ffmpy import FFmpeg
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import requests
from PyQt5.QtCore import pyqtSignal,QThread
import threading
from cryptography.fernet import Fernet

def generate_key():
	key = Fernet.generate_key()
	with open("st.key", "wb") as key_file:
		key_file.write(key)

def load_key():
	if not os.path.exists("st.key"):
		generate_key()
	return open("st.key", "rb").read()

def encrypt_text(message):
	key = load_key()
	encoded_message = message.encode()
	f = Fernet(key)
	encrypted_message = f.encrypt(encoded_message)

	return(encrypted_message.decode("utf-8"))
def decrypt_text(encrypted_message):
	key = load_key()
	f = Fernet(key)
	decrypted_message = f.decrypt(encrypted_message.encode("utf-8"))

	return decrypted_message.decode("utf-8")


def verifyStreamableAuth(username,password):
	r = requests.post('https://api.streamable.com/upload',auth=(username, password))

	if r is None:
		return False
	if r.status_code != 400:
		return False
	return True

class FileUploader(QThread):
	upload_progress = pyqtSignal(object,object)
	upload_complete = pyqtSignal(object,object)
	processing_complete = pyqtSignal(object,object)
	def __init__(self,filePath, username, password,uprate):
		QThread.__init__(self)
		self.filePath = filePath
		self.fileName = os.path.split(filePath)[1]
		self.username = username
		self.password = password
		self.timePrev = 0
		self.inc = 10
		self.uprate = uprate
		self.delay = 0

	def __del__(self):
		return
		self.wait()

	def run(self):
		self.upload()

	def my_callback(self,monitor):
		# Your callback function
		progress = "%d%%" %(monitor.bytes_read/monitor.len * 100)
		if (monitor.bytes_read/8192) % self.inc == 0:

			while(time.time()-self.timePrev < self.delay):
				pass
			self.timePrev = time.time()
			#time.sleep(1/25)
			self.upload_progress.emit(progress, self.filePath)
		#print("%d%%" %(monitor.bytes_read/monitor.len * 100))

	def upload(self,):
		e = MultipartEncoder(
		fields={'field0': 'value', 'field1': 'value',
				'field2': (self.fileName, open(self.filePath, 'rb'), 'text/plain')}
		)
		m = MultipartEncoderMonitor(e, self.my_callback)

		self.timePrev = time.time()
		self.setUploadSpeed(self.uprate)
		r = requests.post('https://api.streamable.com/upload',auth=(self.username, self.password), data=m, headers={'Content-Type': m.content_type})

		if r.status_code == 200:
			self.upload_complete.emit(r.json(), self.filePath)
			
			self.checkProcessing(r.json()['shortcode'])

		else:
			self.upload_complete.emit('Upload Failed',self.filePath)

	def checkProcessing(self,sc):
		p_stat = 1
		url = 'https://api.streamable.com/videos/' + sc
		stime =  time.time()
		toTime =  stime + 600
		waitTime = 2
		while p_stat == 1:
			if time.time() > toTime:
				self.processing_complete.emit("timed-out", self.filePath)
				return
			r = requests.get(url)
			p_stat =  r.json()['status']
			waitTime = self.getWaitTime(waitTime)

		vidurl = 'https://streamable.com/' + sc
		self.processing_complete.emit(vidurl, self.filePath)

	def getWaitTime(self,sec):
		time.sleep(sec)
		if sec < 60:
			sec = sec * 1.5
		return sec

	def setUploadSpeed(self, uprate):
		self.uprate = uprate
		kByte = uprate * 128
		self.delay =  (8 * self.inc) / kByte



def getAvailableName(mypath, add):
	noExt, ext = os.path.splitext(mypath)
	newName =  noExt + add + ext
	addNum = 1

	while(os.path.exists(newName)):
		newName =  "%s%s(%d)%s" % (noExt,add,addNum,ext)
		addNum += 1

	return newName



def randName():
	integer = time.time_ns()
	chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
	result = ''
	while integer > 0:
		integer, remainder = divmod(integer, 36)
		result = chars[remainder]+result
	return result

def fast_scandir(dirname):
	subfolders= [f.path for f in os.scandir(dirname) if f.is_dir()]
	for dirname in list(subfolders):
		subfolders.extend(fast_scandir(dirname))
	return subfolders

def getFiles(mypath):
	files = []
	for dirpath, dirnames, filenames in os.walk(mypath):
		for filename in [f for f in filenames if f.endswith(('.mp4','.mkv','.flv','.gif',))]:
			fullPath = os.path.join(dirpath, filename)
			files.append((fullPath, filename, os.path.getctime(fullPath)))
	files.sort(key= lambda x:x[2], reverse=False)		
	return files

def getThumbs():
	thumbs = {}
	if os.path.exists('thumbs.json'):
		with open('thumbs.json') as json_file:
			thumbs = json.load(json_file)
	return thumbs

def getThumb(filepath):
	thumbs = getThumbs()
	thumbName = ''
	if filepath not in thumbs:
		thumbName = randName()
		thumbName = 'thumbs/'+ thumbName+ '.png'
		try:
			ff = FFmpeg(inputs={filepath: None}, outputs={thumbName: ['-ss', '00:00:00.000', '-vframes', '1','-s', '256x144']})
			ff.run()
		except:
			None

	thumbs[filepath] = thumbName
	with open('thumbs.json', 'w') as outfile:
		json.dump(thumbs, outfile)


	
	return thumbName

def checkThumbs(filepaths):
	thumbs = getThumbs()

	for mypath in filepaths:
		if mypath not in thumbs:
			thumbName = randName()
			thumbName = 'thumbs/'+ thumbName+ '.png'
			try:
				ff = FFmpeg(inputs={mypath: None}, outputs={thumbName: ['-ss', '00:00:00.000', '-vframes', '1','-s', '256x144']})
				ff.run()
				thumbs[mypath] = thumbName
			except:
				None

	with open('thumbs.json', 'w') as outfile:
		json.dump(thumbs, outfile)

def getFilesCheckingThumbs(mypath):
	files = []
	thumbs = getThumbs()



	for dirpath, dirnames, filenames in os.walk(mypath):
		for filename in [f for f in filenames if f.endswith(('.mp4','.mkv','.flv','.gif',))]:
			fullPath = os.path.join(dirpath, filename)
			files.append((fullPath, filename, os.path.getctime(fullPath)))
			if fullPath not in thumbs:
				thumbName = randName()
				thumbName = 'thumbs/'+ thumbName+ '.png'
				ff = FFmpeg(inputs={fullPath: None}, outputs={thumbName: ['-ss', '00:00:1', '-vframes', '1','-s', '256x144']})
				ff.run()
				thumbs[fullPath] = thumbName

	with open('thumbs.json', 'w') as outfile:
		json.dump(thumbs, outfile)

	files.sort(key= lambda x:x[2], reverse=False)

	return files

