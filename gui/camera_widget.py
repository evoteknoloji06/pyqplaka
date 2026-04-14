import cv2
from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap
import numpy as np

class CameraWidget(QFrame):
    def __init__(self, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self.setFrameShape(QFrame.Panel)
        self.setLineWidth(2)
        self.setStyleSheet("background-color: black; border: 1px solid #333;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel("Camera " + str(camera_id + 1))
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("color: white; font-weight: bold;")
        
        # Pencere büyüme sorununu çözen kritik ayarlar:
        self.image_label.setMinimumSize(1, 1)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(False) 
        
        self.layout.addWidget(self.image_label)

    @Slot(np.ndarray)
    def update_image(self, frame):
        if frame is None:
            return

        # BGR -> RGB dönüşümü
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Etiketin mevcut boyutuna göre resmi ölçekle
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)