import sys
from PyQt5.QtWidgets import QFrame,QDialog, QFileDialog, QMenu, QTimeEdit, QAction, QLabel,QScrollArea
from PyQt5.QtWidgets import QSpinBox, QApplication,QPushButton,QLineEdit, QMessageBox,QStyle
from PyQt5.QtWidgets import QWidget,QMainWindow,QGridLayout,QVBoxLayout,QHBoxLayout, QSizePolicy, QSlider 
from PyQt5.QtGui import QPalette, QColor, QIcon, QCursor
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5 import QtCore, QtTest
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import mytools
import qrangeslider #Source: https://stackoverflow.com/a/47342469 ,pip
import time
import json
import subprocess
import os
from ffmpy import FFmpeg
import webbrowser

class VideoWindow(QWidget):
	def __init__(self, vidPath):
		super().__init__()
		self.fullPath = vidPath
		self.startTime = 0
		self.endTime = 0
		self.init_ui()


	def init_ui(self):
		layout = QVBoxLayout()
		self.setLayout(layout)
		self.setWindowTitle(self.fullPath)

		self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

		self.videoWidget = QVideoWidget()

		self.playButton = QPushButton()
		self.playButton.setEnabled(True)
		self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
		self.playButton.setFixedWidth(100)
		self.playButton.setFixedHeight(50)
		self.playButton.clicked.connect(self.play)

		self.trimButton = QPushButton("Trim")
		self.trimButton.setFixedWidth(150)
		self.trimButton.setFixedHeight(50)
		self.trimButton.clicked.connect(self.trimVid)


		self.positionSlider = QSlider(QtCore.Qt.Horizontal)
		self.positionSlider.setRange(0, 0)
		self.positionSlider.sliderMoved.connect(self.setPosition)

		self.rangeSlider = qrangeslider.QRangeSlider()
		self.rangeSlider.setRange(0, 0)
		self.rangeSlider.endValueChanged.connect(self.adjustForEnd)
		self.rangeSlider.startValueChanged.connect(self.adjustForStart)
		self.rangeSlider.setFixedHeight(15)


		self.startTimeInput = QTimeEdit()
		self.endTimeInput = QTimeEdit()
		self.startTimeInput.setDisplayFormat('hh:mm:ss.zzz')
		self.endTimeInput.setDisplayFormat('hh:mm:ss.zzz')

		self.startTimeInput.timeChanged.connect(self.startInputChanged)
		self.endTimeInput.timeChanged.connect(self.endInputChanged)

		self.mediaPlayer.setMedia(QMediaContent(QtCore.QUrl.fromLocalFile(self.fullPath)))


		layout.addWidget(self.videoWidget)
		self.mediaPlayer.setVideoOutput(self.videoWidget)
		self.mediaPlayer.setNotifyInterval(10)
		self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
		self.mediaPlayer.positionChanged.connect(self.positionChanged)
		self.mediaPlayer.durationChanged.connect(self.durationChanged)

		

		controlLayout = QVBoxLayout()
		controlLayout.setContentsMargins(0, 0, 0, 0)
		controlLayout.addWidget(self.rangeSlider)
		controlLayout.addWidget(self.positionSlider)

		timeInputLayout = QHBoxLayout()
		timeInputLayout.addWidget(self.playButton)
		timeInputLayout.addWidget(self.startTimeInput)
		timeInputLayout.addWidget(self.endTimeInput)
		timeInputLayout.addWidget(self.trimButton)

		controlLayout.addLayout(timeInputLayout)


		layout.addLayout(controlLayout)

		self.mediaPlayer.play()

		self.resize(1024,700)

		self.show()


	def closeEvent(self, event):
		self.mediaPlayer.stop()
		self.videoWidget.setParent(None)
		self.mediaPlayer.setParent(None)
		self.mediaPlayer.deleteLater()
		self.videoWidget.deleteLater()


	def trimVid(self):
		self.trimButton.setEnabled(False)
		outName = mytools.getAvailableName(self.fullPath,'Trim')
		print(outName)
		trimStartTime = self.startTimeInput.time().toString('hh:mm:ss.zzz')
		trimEndTime = self.endTimeInput.time().toString('hh:mm:ss.zzz')
		try:
			ff = FFmpeg(inputs={self.fullPath: None}, outputs={outName: ['-ss', trimStartTime, '-to', trimEndTime,'-c:v', 'copy','-c:a','copy',]})
			ff.run()
		except Exception as e:
			msg = QMessageBox()
			msg.setWindowTitle("Trim Failed")
			msg.setText(str(e))
			msg.setIcon(QMessageBox.Critical)

			showMsg = msg.exec_()
		self.trimButton.setEnabled(True)



	def play(self):
		if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
			self.mediaPlayer.pause()
		else:
			self.mediaPlayer.play()

	def mediaStateChanged(self, state):
		if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
			self.playButton.setIcon(
				self.style().standardIcon(QStyle.SP_MediaPause))
		else:
			self.playButton.setIcon(
				self.style().standardIcon(QStyle.SP_MediaPlay))

	def positionChanged(self, position):
		self.positionSlider.setValue(position)
		if position > self.endTime:
			self.mediaPlayer.setPosition(self.startTime)

	def adjustForStart(self, startPos):
		self.startTime =  startPos
		self.mediaPlayer.setPosition(startPos)

		self.startTimeInput.setTime(QtCore.QTime(0,0).addMSecs(startPos))
		self.endTimeInput.setMinimumTime(QtCore.QTime(0,0).addMSecs(startPos))

	def adjustForEnd(self, endPos):
		self.endTime = endPos
		if self.positionSlider.value() > endPos:
			self.mediaPlayer.setPosition(endPos)

		self.endTimeInput.setTime(QtCore.QTime(0,0).addMSecs(endPos))
		self.startTimeInput.setMaximumTime(QtCore.QTime(0,0).addMSecs(endPos))

	def startInputChanged(self, inputTime):
		self.rangeSlider.setStart(QtCore.QTime(0,0,0,0).msecsTo(inputTime))

	def endInputChanged(self, inputTime):
		self.rangeSlider.setEnd(QtCore.QTime(0,0,0,0).msecsTo(inputTime))
		
	def durationChanged(self, duration):
		self.positionSlider.setRange(0, duration)
		self.rangeSlider.setMax(duration)
		self.rangeSlider.setEnd(duration)

		self.startTimeInput.setMinimumTime(QtCore.QTime(0,0))
		self.endTimeInput.setMinimumTime(QtCore.QTime(0,0))
		self.endTimeInput.setTime(QtCore.QTime(0,0).addMSecs(duration))
		self.startTimeInput.setMaximumTime(QtCore.QTime(0,0).addMSecs(duration))
		self.endTimeInput.setMaximumTime(QtCore.QTime(0,0).addMSecs(duration))

	def setPosition(self, position):
		self.mediaPlayer.setPosition(position)

class SettingsWindow(QDialog):
	def __init__(self):
		super().__init__()
		self.settings = {}
		self.init_ui()

	def init_ui(self):
		layout = QVBoxLayout()
		layout.setStretch(0,0)
		self.setLayout(layout)

		if os.path.exists('settings.json'):
			with open('settings.json') as json_file:
				self.settings = json.load(json_file)


		fpLabel =  QLabel("Videos Folder: ")

		fdHBox = QHBoxLayout()
		self.fdInput = QLineEdit()
		self.fdInput.setReadOnly(True)
		fdButton = QPushButton("Browse")
		fdButton.clicked.connect(self.setRootFolder)
		fdHBox.addWidget(self.fdInput)
		fdHBox.addWidget(fdButton)

		uploadOptions = QHBoxLayout()
		streamableOptions = QVBoxLayout()

		uHBox = QHBoxLayout()
		userLabel = QLabel("Username: ")
		self.userInput = QLineEdit()
		self.userInput.setMaximumWidth(150)
		uHBox.addWidget(userLabel)
		uHBox.addWidget(self.userInput)

		pHBox = QHBoxLayout()
		pwLabel = QLabel("Password: ")
		self.pwInput = QLineEdit()
		self.pwInput.setMaximumWidth(150)
		self.pwInput.setEchoMode(QLineEdit.Password)
		pHBox.addWidget(pwLabel)
		pHBox.addWidget(self.pwInput)

		streamableOptions.addLayout(uHBox)
		streamableOptions.addLayout(pHBox)

		uprateOptions = QVBoxLayout()
		uprateLabel = QLabel("Upload Speed (megabits per second):")
		self.uprateInput = QSpinBox()
		self.uprateInput.setRange(1,1000)
		self.uprateInput.setMaximumWidth(80)
		self.upDetails = QLabel()
		self.uprateInput.valueChanged.connect(self.uploadChanged)
		self.uprateInput.setValue(24)

		uprateOptions.addWidget(uprateLabel)
		uprateOptions.addWidget(self.uprateInput)
		uprateOptions.addWidget(self.upDetails)

		uploadOptions.addLayout(streamableOptions)
		uploadOptions.addLayout(uprateOptions)

		saveButton =  QPushButton("Save")
		saveButton.clicked.connect(self.saveSettings)
		saveButton.setDefault(True)

		if 'root_path' in self.settings:
			self.fdInput.setText(self.settings['root_path'])
		if 'username' in self.settings:
			self.userInput.setText(self.settings['username'])
		if 'password' in self.settings:
			self.pwInput.setText(mytools.decrypt_text(self.settings['password']))
		if 'upload_speed' in self.settings:
			self.uprateInput.setValue(int(self.settings['upload_speed']))

		layout.addWidget(fpLabel)
		layout.addLayout(fdHBox)
		layout.addWidget(QLabel("Streamable Settings:"))
		layout.addLayout(uploadOptions)
		layout.addWidget(saveButton)


		self.setWindowTitle("Settings")
		self.resize(400,200)
		#self.show()

	def uploadChanged(self, uprate):
		mBit = uprate
		mByte = uprate / 8
		self.upDetails.setText("%04.2f Mb/s = %04.2f MB/s"%(mBit,mByte))

	def setRootFolder(self):
		file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
		self.fdInput.setText(file)
	def saveSettings(self):
		self.settings['username'] = self.userInput.text()
		self.settings['password'] = mytools.encrypt_text(self.pwInput.text())
		self.settings['root_path'] = self.fdInput.text()
		self.settings['upload_speed'] = self.uprateInput.value()
		with open('settings.json', 'w') as outfile:
			json.dump(self.settings, outfile)

		self.close()
	def getSettings(self):
		return(self.settings)

class FileObserver(QtCore.QObject):
	file_found = QtCore.pyqtSignal(object)
	def __init__(self, rootPath):
		super().__init__()
		self.rootPath = rootPath
		self.patterns = ["*.mkv", "*.mp4", "*.flv", "*.gif"]
		self.ignore_patterns = []
		self.ignore_directories = True
		self.case_sensitive = False
		self.run()
	
	def on_created(self, event):
		print(f"{event.src_path} has been created")
		QtTest.QTest.qWait(3000)
		self.file_found.emit(event.src_path)

	def on_deleted(self, event):
		print(f"{event.src_path} has been deleted")

	def on_modified(self, event):
		print(f"{event.src_path} has been modified")

	def on_moved(self, event):
		print(f"{event.src_path} has moved to {event.dest_path}")

	def run(self):
		my_event_handler = PatternMatchingEventHandler(self.patterns, self.ignore_patterns, self.ignore_directories, self.case_sensitive)
	
		my_event_handler.on_created = self.on_created
		my_observer = Observer()
		my_observer.schedule(my_event_handler, self.rootPath, recursive=True)
		my_observer.start()


class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.gridx = 3
		self.gridy = 999999
		self.mypath = ""
		self.vw = None
		self.username = ''
		self.password = ''
		self.vidPaths = []
		self.vidBox = {}
		self.vidframe = {}
		self.numVids = 0
		self.sURLS = {}
		self.uprate = 18
		self.init_ui()

	def init_ui(self):

		self.scroll = QScrollArea()
		self.widget = QWidget()
		self.gridLayout = QGridLayout()

		topBar = QHBoxLayout()

		settingsButton  = QPushButton("Settings")
		settingsButton.setMaximumWidth(100)
		settingsButton.clicked.connect(self.openSettings)
		topBar.addWidget(settingsButton, alignment= QtCore.Qt.AlignLeft)

		saButton  = QPushButton("Open Streamable")
		saButton.setMaximumWidth(140)
		saButton.setStyleSheet("background-color: #17a2b8")
		saButton.clicked.connect(lambda: webbrowser.open('https://streamable.com', new=2))
		topBar.addWidget(saButton)

		settingsButton  = QPushButton("Refresh")
		settingsButton.setMaximumWidth(100)
		settingsButton.clicked.connect(self.loadGrid)
		topBar.addWidget(settingsButton)

		self.vlayout = QVBoxLayout()
		self.vlayout.addLayout(topBar)
		self.vlayout.addLayout(self.gridLayout)

		self.widget.setLayout(self.vlayout)
		self.popMenu = QMenu(self)
		self.cursor = QCursor()



		if not os.path.exists('thumbs'):
			os.makedirs('thumbs')

		if os.path.exists('streamableURLS.json'):
			with open('streamableURLS.json') as json_file:
				self.sURLS = json.load(json_file)
		else:
			with open('streamableURLS.json', 'w') as outfile:
				json.dump(self.sURLS, outfile)
		

		self.loadSettings()
		self.loadGrid()

		self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.scroll.setWidgetResizable(True)
		self.scroll.setWidget(self.widget)

		fObs = FileObserver(self.mypath)
		fObs.file_found.connect(self.addVid)


		self.setCentralWidget(self.scroll)
		self.setWindowTitle("Clips")
		self.setGeometry(520,260,1030,590)
		self.show()



	def openSettings(self):
		self.sw = SettingsWindow()
		self.sw.exec_()
		settings = self.sw.getSettings()

		if 'root_path' not in settings:
			sys.exit()
		if not os.path.exists(settings['root_path']):
			sys.exit()

		self.username =  settings['username']
		self.password =  mytools.decrypt_text(settings['password'])
		self.mypath =  settings['root_path']
		self.uprate = settings['upload_speed']

	def loadSettings(self):
		settings = {}

		if os.path.exists('settings.json'):
			with open('settings.json') as json_file:
				settings = json.load(json_file)

		if 'root_path' not in settings:
			self.sw = SettingsWindow()
			self.sw.exec_()
			settings = self.sw.getSettings()
		elif not os.path.exists(settings['root_path']):
			self.sw = SettingsWindow()
			self.sw.exec_()
			settings = self.sw.getSettings()

		if 'root_path' not in settings:
			sys.exit()
		if not os.path.exists(settings['root_path']):
				sys.exit()

		self.username =  settings['username']
		self.password =  mytools.decrypt_text(settings['password'])
		self.mypath =  settings['root_path']
		self.uprate = settings['upload_speed']


	def removeFile(self, path):
		if os.path.exists(path):
			os.remove(path)
		try:
			self.vidframe[path].setParent(None)
			for i in reversed(range(self.vidBox[path].count())): 
				self.vidBox[path].itemAt(i).widget().setParent(None)
		except:
			pass

	def addVid(self, newVidPath):
		fl = [newVidPath, os.path.split(newVidPath)[1]] 
		x = self.gridx
		y = self.gridy
		if x==0:
			x=3
			y-=1

		n = self.numVids

		self.vidBox[fl[0]] = QVBoxLayout()


		vidButton = QPushButton()
		vidButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		vidButton.customContextMenuRequested.connect(lambda state, vPath = fl: self.on_buttonRightClick(vPath))

		vidButton.setIcon(QIcon(mytools.getThumb(newVidPath)))
		vidButton.setIconSize(QtCore.QSize(256,144))
		vidButton.clicked.connect(lambda state, vPath = fl[0]: self.openVideoWindow(self,vPath))

		openStreamableButton = QPushButton("Not Uploaded")

		openStreamableButton.setDisabled(True)
		if fl[0] in self.sURLS:
			openStreamableButton.setEnabled(True)
			openStreamableButton.setStyleSheet("background-color: #17a2b8")
			openStreamableButton.setText('Open URL')
			openStreamableButton.clicked.connect(lambda state, url = self.sURLS[fl[0]]: webbrowser.open(url, new=2))

		vidLabel = QLabel(fl[1])
		vidLabel.setMaximumWidth(300)
		vidLabel.setAlignment(QtCore.Qt.AlignCenter)


		self.vidBox[fl[0]].addWidget(vidButton)
		self.vidBox[fl[0]].addWidget(openStreamableButton)
		self.vidBox[fl[0]].addWidget(vidLabel)


		try:
			self.gridLayout.itemAtPosition(y,x).widget().setParent(None)
		except:
			pass

		self.vidframe[fl[0]] =  QFrame()
		self.vidframe[fl[0]].setLayout(self.vidBox[fl[0]])
		self.vidframe[fl[0]].setObjectName('vidFrame')
		self.vidframe[fl[0]].setStyleSheet("QWidget#vidFrame {border:3px solid rgb(0, 0, 0)} ")
		self.gridLayout.addWidget(self.vidframe[fl[0]],y,x)

		self.numVids += 1
		x-=1			

		self.gridx = x
		self.gridy = y


	def openVideoWindow(self,checked,vidPath):
		self.vw = VideoWindow(vidPath)


	def on_buttonRightClick(self, fileData):
		self.popMenu = QMenu(self)

		folderPath = os.path.split(fileData[0])[0]

		openFolderAction = QAction('Open Folder', self)
		openFolderAction.triggered.connect(lambda state, dPath =fileData[0]: self.openFolderExplorer(dPath))

		uploadToStreamable = QAction('Upload', self)
		uploadToStreamable.triggered.connect(lambda state, fPath =fileData[0]: self.uploadStreamable(fPath))

		delVideo = QAction('Delete',self)
		delVideo.triggered.connect(lambda state, fpath =fileData[0]: self.removeFile(fpath))

		blankAction = QAction('',self)

		self.popMenu.addAction(openFolderAction)
		self.popMenu.addSeparator()
		self.popMenu.addAction(uploadToStreamable) 
		self.popMenu.addAction(blankAction)
		self.popMenu.addAction(delVideo)

		self.popMenu.popup(self.cursor.pos())


	def showUploadProgress(self, progress, filePath):
		self.vidBox[filePath].itemAt(1).widget().setText("Uploading... %s"%(progress))
	def onUploadComplete(self, response, filePath):
		vidurl = 'https://streamable.com/%s' %  response['shortcode']

		self.sURLS[filePath] =  vidurl
		with open('streamableURLS.json', 'w') as outfile:
			json.dump(self.sURLS, outfile)

		self.vidBox[filePath].itemAt(1).widget().setText("Open URL (Processing...)")
		self.vidBox[filePath].itemAt(1).widget().setEnabled(True)
		self.vidBox[filePath].itemAt(1).widget().setStyleSheet("background-color: #17a2b8")
		self.vidBox[filePath].itemAt(1).widget().clicked.connect(lambda: webbrowser.open(vidurl, new=2))
	def onProcessingComplete(self, vidurl, filePath):
		self.vidBox[filePath].itemAt(1).widget().setText("Open URL")

	def uploadStreamable(self, folderPath):
		self.fileUp = mytools.FileUploader(folderPath, self.username,self.password,self.uprate)
		self.fileUp.start()
		self.fileUp.upload_progress.connect(self.showUploadProgress)
		self.fileUp.upload_complete.connect(self.onUploadComplete)
		self.fileUp.processing_complete.connect(self.onProcessingComplete)

	def openFolderExplorer(self, folderPath):
		#print(folderPath)
		folderPath = folderPath.replace('/','\\')
		subprocess.Popen(r'explorer /select,%s'%folderPath)

	def loadGrid(self):
		self.paths = mytools.getFilesCheckingThumbs(self.mypath)
		x=len(self.paths)%3
		y=999999

		self.numVids = 0
		#self.gridLayout = QGridLayout()

		thumbs = mytools.getThumbs()

		for fl in self.paths:
			if x==0:
				x=3
				y-=1

			n = self.numVids

			self.vidBox[fl[0]] = QVBoxLayout()


			vidButton = QPushButton()
			vidButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
			vidButton.customContextMenuRequested.connect(lambda state, vPath = fl: self.on_buttonRightClick(vPath))

			vidButton.setIcon(QIcon(thumbs[fl[0]]))
			vidButton.setIconSize(QtCore.QSize(256,144))
			vidButton.clicked.connect(lambda state, vPath = fl[0]: self.openVideoWindow(self,vPath))

			openStreamableButton = QPushButton("Not Uploaded")

			openStreamableButton.setDisabled(True)
			if fl[0] in self.sURLS:
				openStreamableButton.setEnabled(True)
				openStreamableButton.setStyleSheet("background-color: #17a2b8")
				openStreamableButton.setText('Open URL')
				openStreamableButton.clicked.connect(lambda state, url = self.sURLS[fl[0]]: webbrowser.open(url, new=2))

			vidLabel = QLabel(fl[1])
			vidLabel.setMaximumWidth(300)
			vidLabel.setAlignment(QtCore.Qt.AlignCenter)


			self.vidBox[fl[0]].addWidget(vidButton)
			self.vidBox[fl[0]].addWidget(openStreamableButton)
			self.vidBox[fl[0]].addWidget(vidLabel)


			try:
				self.gridLayout.itemAtPosition(y,x).widget().setParent(None)
			except:
				pass

			self.vidframe[fl[0]] =  QFrame()
			self.vidframe[fl[0]].setLayout(self.vidBox[fl[0]])
			self.vidframe[fl[0]].setObjectName('vidFrame')
			self.vidframe[fl[0]].setStyleSheet("QWidget#vidFrame {border:3px solid rgb(0, 0, 0)} ")
			self.gridLayout.addWidget(self.vidframe[fl[0]],y,x)

			self.numVids += 1
			x-=1


		self.gridx = x
		self.gridy = y

		for d in range(30):
			if x==0:
				x=3
				y-=1
			try:
				self.gridLayout.itemAtPosition(y,x).widget().setParent(None)
			except:
				pass			

		self.vlayout.itemAt(1).setParent(None)
		self.vlayout.addLayout(self.gridLayout)



if __name__=="__main__":

	app=QApplication(sys.argv)
	app.setStyle("Fusion")
	palette = QPalette()
	palette.setColor(QPalette.Window, QColor(53, 53, 53))
	palette.setColor(QPalette.WindowText, QtCore.Qt.white)
	palette.setColor(QPalette.Base, QColor(25, 25, 25))
	palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
	palette.setColor(QPalette.ToolTipBase, QtCore.Qt.black)
	palette.setColor(QPalette.ToolTipText, QtCore.Qt.white)
	palette.setColor(QPalette.Text, QtCore.Qt.white)
	palette.setColor(QPalette.Button, QColor(53, 53, 53))
	palette.setColor(QPalette.ButtonText, QtCore.Qt.white)
	palette.setColor(QPalette.BrightText, QtCore.Qt.red)
	palette.setColor(QPalette.Link, QColor(42, 130, 218))
	palette.setColor(QPalette.Highlight, QColor(0,0,0,0))
	palette.setColor(QPalette.HighlightedText, QtCore.Qt.white)
	app.setPalette(palette)

	mainWindow = MainWindow()


	sys.exit(app.exec_())