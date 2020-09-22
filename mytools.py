import time
import os
import json
from ffmpy import FFmpeg
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import requests
from PyQt5.QtCore import pyqtSignal,QThread
import threading


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
	def __init__(self,filePath, username, password):
		QThread.__init__(self)
		self.filePath = filePath
		self.fileName = os.path.split(filePath)[1]
		self.username = username
		self.password = password

	def __del__(self):
		return
		self.wait()

	def run(self):
		self.upload()

	def my_callback(self,monitor):
		# Your callback function
		progress = "%d%%" %(monitor.bytes_read/monitor.len * 100)
		if (monitor.bytes_read/8192) % 10 == 0:
        	#time.sleep(1/25)
			self.upload_progress.emit(progress, self.filePath)
		#print("%d%%" %(monitor.bytes_read/monitor.len * 100))

	def upload(self,):
		e = MultipartEncoder(
		fields={'field0': 'value', 'field1': 'value',
				'field2': (self.fileName, open(self.filePath, 'rb'), 'text/plain')}
		)
		m = MultipartEncoderMonitor(e, self.my_callback)

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


def uploadToStreamable(filePath, username, password):
	def my_callback(monitor):
		# Your callback function
		print("%d%%" %(monitor.bytes_read/monitor.len * 100))
		#if (monitor.bytes_read/8192) % 5 == 0:
			#time.sleep(1/25)

	e = MultipartEncoder(
		fields={'field0': 'value', 'field1': 'value',
				'field2': ('filename', open(filePath, 'rb'), 'text/plain')}
		)
	m = MultipartEncoderMonitor(e, my_callback)

	r = requests.post('https://api.streamable.com/upload',auth=(username, password), data=m,
					  headers={'Content-Type': m.content_type})
				  
	print(r.status_code)
	print(r.json())	


def startUploadThread(filePath, username, password):
	uT = threading.Thread(target=startUploadThread, args=(filePath, username, password))
	uT.start()

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
			files.append((fullPath, filename))
	files.sort(key= lambda tup: os.path.getctime(tup[0]), reverse=False)		
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
			files.append((fullPath, filename))
			if fullPath not in thumbs:
				thumbName = randName()
				thumbName = 'thumbs/'+ thumbName+ '.png'
				ff = FFmpeg(inputs={fullPath: None}, outputs={thumbName: ['-ss', '00:00:1', '-vframes', '1','-s', '256x144']})
				ff.run()
				thumbs[fullPath] = thumbName

	with open('thumbs.json', 'w') as outfile:
		json.dump(thumbs, outfile)

	files.sort(key= lambda tup: os.path.getctime(tup[0]), reverse=False)

	return files

