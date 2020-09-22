import sys
from PyQt5.QtWidgets import QDialog, QFileDialog, QMenu, QTimeEdit, QAction, QLabel,QScrollArea
from PyQt5.QtWidgets import QApplication,QPushButton,QLineEdit, QMessageBox,QStyle
from PyQt5.QtWidgets import QWidget,QMainWindow,QGridLayout,QVBoxLayout,QHBoxLayout, QSizePolicy, QSlider 
from PyQt5.QtGui import QPalette, QColor, QIcon, QCursor
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5 import QtCore, QtTest
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import mytools
import qrangeslider #Source: https://stackoverflow.com/a/47342469 ,https://github.com/rsgalloway/qrangeslider
import time
import json
import subprocess
import os
from ffmpy import FFmpeg
import webbrowser



class UploadThread(QtCore.QThread):
	def __init__(self,filePath,username,password):
		QtCore.QThread.__init__(self)
		self.user = username
		self.pw = password
		self.fPath =  filePath

	def __del__(self):
		self.wait()

	def run(self):
		mytools.uploadToStreamable(self.fPath, self.user,self.pw)


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

		videoWidget = QVideoWidget()

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


		layout.addWidget(videoWidget)
		self.mediaPlayer.setVideoOutput(videoWidget)
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
		if self.positionSlider.value() < startPos:
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
		self.username = ''
		self.password = ''
		self.rootpath = ''
		self.init_ui()

	def init_ui(self):
		layout = QVBoxLayout()
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

		uHBox = QHBoxLayout()
		userLabel = QLabel("Username: ")
		self.userInput = QLineEdit()
		uHBox.addWidget(userLabel)
		uHBox.addWidget(self.userInput)

		pHBox = QHBoxLayout()
		pwLabel = QLabel("Password: ")
		self.pwInput = QLineEdit()
		self.pwInput.setEchoMode(QLineEdit.Password)
		pHBox.addWidget(pwLabel)
		pHBox.addWidget(self.pwInput)


		saveButton =  QPushButton("Save")
		saveButton.clicked.connect(self.saveSettings)
		saveButton.setDefault(True)

		layout.addWidget(fpLabel)
		layout.addLayout(fdHBox)
		layout.addLayout(uHBox)
		layout.addLayout(pHBox)
		layout.addWidget(saveButton)


		self.setWindowTitle("Settings")
		self.resize(640,480)
		#self.show()

	def setRootFolder(self):
		file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
		self.fdInput.setText(file)
	def saveSettings(self):
		self.settings['username'] = self.userInput.text()
		self.settings['password'] = self.pwInput.text()
		self.settings['root_path'] = self.fdInput.text()
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
		self.vidButtons = []
		self.vidLabels = []
		self.vidPaths = []
		self.vidBox = {}
		self.numVids = 0
		self.sURLS = {}
		self.init_ui()

	def init_ui(self):

		self.scroll = QScrollArea()
		self.widget = QWidget()
		self.gridLayout = QGridLayout()

		self.widget.setLayout(self.gridLayout)
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

		#print(self.vidBox[self.numVids-1].itemAt(1).widget().setText("ggggg"))


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
		self.password =  settings['password']
		self.mypath =  settings['root_path']

	def addVid(self, newVidPath):
		fl = [newVidPath, os.split(newVidPath)[1]] 
		x = self.gridx
		y = self.gridy
		if x==0:
			x=3
			y-=2

		n = self.numVids
		self.vidButtons.append(QPushButton())

		self.vidButtons[n].setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.vidButtons[n].customContextMenuRequested.connect(lambda state, vPath = fl: self.on_buttonRightClick(vPath))



		self.vidButtons[n].setIcon(QIcon(mytools.getThumb(newVidPath)))
		self.vidButtons[n].setIconSize(QtCore.QSize(256,144))
		self.vidButtons[n].clicked.connect(lambda state, vPath = fl[0]: self.openVideoWindow(self,vPath))
		try:
			self.gridLayout.itemAtPosition(y,x).widget().setParent(None)
		except:
			pass
		self.gridLayout.addWidget(self.vidButtons[n],y,x)

		self.vidLabels.append(QLabel(fl[1]))
		self.vidLabels[n].setMaximumWidth(300)
		self.vidLabels[n].setAlignment(QtCore.Qt.AlignCenter)
		try:
			self.gridLayout.itemAtPosition(y+1,x).widget().setParent(None)
		except:
			pass
		self.gridLayout.addWidget(self.vidLabels[n],y+1,x)

		self.numVids += 1
		x-=1
		self.x = x		


	def openVideoWindow(self,checked,vidPath):
		self.vw = VideoWindow(vidPath)


	def on_buttonRightClick(self, fileData):
		self.popMenu = QMenu(self)

		folderPath = os.path.split(fileData[0])[0]

		openFolderAction = QAction('Open Folder', self)
		openFolderAction.triggered.connect(lambda state, dPath =fileData[0]: self.openFolderExplorer(dPath))


		uploadToStreamable = QAction('Upload', self)
		uploadToStreamable.triggered.connect(lambda state, fPath =fileData[0]: self.uploadStreamable(fPath))

		self.popMenu.addAction(openFolderAction)
		self.popMenu.addSeparator()
		self.popMenu.addAction(uploadToStreamable) 

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
		self.vidBox[filePath].itemAt(1).widget().clicked.connect(lambda: webbrowser.open(vidurl, new=2))
	def onProcessingComplete(self, vidurl, filePath):
		self.vidBox[filePath].itemAt(1).widget().setText("Open URL")

	def uploadStreamable(self, folderPath):
		self.fileUp = mytools.FileUploader(folderPath, self.username,self.password)
		self.fileUp.start()
		self.fileUp.upload_progress.connect(self.showUploadProgress)
		self.fileUp.upload_complete.connect(self.onUploadComplete)
		self.fileUp.processing_complete.connect(self.onProcessingComplete)

	def openFolderExplorer(self, folderPath):
		#print(folderPath)
		folderPath = folderPath.replace('/','\\')
		subprocess.Popen(r'explorer /select,%s'%folderPath)

	'''
	def rereloadGrid(self):
		self.reloadGrid()

	def reloadGGGrid(self):
		self.gridx = (self.numVids%3)
		self.gridy = 999999
		for i in range(self.numVids):
			print(i)
			if self.gridx==0:
				self.gridx=3
				self.gridy-=2
			try:
				self.gridLayout.itemAtPosition(self.gridy,self.gridx).widget().setParent(None)
			finally:
				self.gridLayout.addWidget(self.vidButtons[i], self.gridy,self.gridx)
			try:
				self.gridLayout.itemAtPosition(self.gridy+1,self.gridx).widget().setParent(None)
			finally:
				self.gridLayout.addWidget(self.vidLabels[i], self.gridy+1,self.gridx)
			self.gridx -=1
	'''
	def loadGrid(self):
		self.paths = mytools.getFilesCheckingThumbs(self.mypath)
		x=len(self.paths)%3
		y=999999

		thumbs = mytools.getThumbs()

		for fl in self.paths:
			if x==0:
				x=3
				y-=1

			n = self.numVids

			self.vidBox[fl[0]] = QVBoxLayout()

			#buttonsArea =  QHBoxLayout()
			miniButtons = QHBoxLayout()

			vidButton = QPushButton()
			vidButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
			vidButton.customContextMenuRequested.connect(lambda state, vPath = fl: self.on_buttonRightClick(vPath))

			vidButton.setIcon(QIcon(thumbs[fl[0]]))
			vidButton.setIconSize(QtCore.QSize(256,144))
			vidButton.clicked.connect(lambda state, vPath = fl[0]: self.openVideoWindow(self,vPath))

			openFolderButton = QPushButton()
			uploadStreamableButton = QPushButton()
			openStreamableButton = QPushButton("Not Uploaded")
			copyStreamableButton = QPushButton()

			'''

			openFolderButton.setIcon(QIcon('resources/openFolder.png'))
			uploadStreamableButton.setIcon(QIcon('resources/uploadStreamable.png'))
			openStreamableButton.setIcon(QIcon('resources/openURL.png'))
			copyStreamableButton.setIcon(QIcon('resources/copyURL.png'))

			openFolderButton.setIconSize(QtCore.QSize(30,20))
			uploadStreamableButton.setIconSize(QtCore.QSize(30,20))
			openStreamableButton.setIconSize(QtCore.QSize(30,20))
			copyStreamableButton.setIconSize(QtCore.QSize(30,20))
			'''

			openStreamableButton.setDisabled(True)
			if fl[0] in self.sURLS:
				openStreamableButton.setEnabled(True)
				openStreamableButton.setText('Open URL')
				openStreamableButton.clicked.connect(lambda: webbrowser.open(self.sURLS[fl[0]], new=2))

			vidLabel = QLabel(fl[1])
			vidLabel.setMaximumWidth(300)
			vidLabel.setAlignment(QtCore.Qt.AlignCenter)

			#miniButtons.addWidget(openFolderButton)
			#miniButtons.addWidget(uploadStreamableButton)
			#miniButtons.addWidget(copyStreamableButton)
			#miniButtons.addWidget(openStreamableButton)

			#buttonsArea.addWidget(vidButton)
			#buttonsArea.addLayout(miniButtons)

			self.vidBox[fl[0]].addWidget(vidButton)
			self.vidBox[fl[0]].addWidget(openStreamableButton)
			self.vidBox[fl[0]].addWidget(vidLabel)


			try:
				self.gridLayout.itemAtPosition(y,x).widget().setParent(None)
			except:
				pass
			self.gridLayout.addLayout(self.vidBox[fl[0]],y,x)

			self.numVids += 1
			x-=1			

		self.gridx = x
		self.gridy = y



def directory_changed(path):
	print('Directory Changed: %s' % path)


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