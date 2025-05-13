import sys
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QStatusBar, QToolBar, QAction, QFileDialog, QLabel

class MainWindow(QMainWindow):
   def __init__(self):
      super().__init__()

      self.setWindowTitle("Camera Application")
      self.statusBar().showMessage("Ready")
      self.toolbar = QToolBar()
      self.addToolBar(self.toolbar)
      self.label = QLabel()
      self.label.setAlignment(Qt.AlignCenter)
      self.setCentralWidget(self.label)

      self.camera = CameraThread()
      self.camera.image.connect(self.update_image)
      self.camera.start()

      capture_action = QAction("Capture", self.toolbar)
      capture_action.setShortcut("Space")

      capture_action.triggered.connect(self.capture_photo)
      self.toolbar.addAction(capture_action)

   def update_image(self, frame):
      frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
      self.label.setPixmap(QPixmap.fromImage(image))

   def capture_photo(self):
      frame = self.camera.frame
      frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
      filename, _ = QFileDialog.getSaveFileName(self, "Save Photo", "", "JPEG Image (*.jpg)")
      if filename:
         image.save(filename, "jpg")

class CameraThread(QThread):
   image = pyqtSignal(np.ndarray)

   def __init__(self):
      super().__init__()
      self.capture = None

   def start_capture(self):
      self.capture = cv2.VideoCapture(0)

   def stop_capture(self):
      if self.capture:
         self.capture.release()
         self.capture = None

   def run(self):
      self.start_capture()
      while True:
         ret, frame = self.capture.read()
         if ret:
            self.image.emit(frame)

   def stop(self):
      self.stop_capture()
      super().stop()