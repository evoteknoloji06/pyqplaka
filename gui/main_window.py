import cv2
from PySide6.QtWidgets import (QMainWindow, QWidget, QGridLayout, QVBoxLayout, 
                                 QHBoxLayout, QListWidget, QListWidgetItem, QLabel, 
                                 QTabWidget, QFrame)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap
import numpy as np

from gui.camera_widget import CameraWidget
from gui.management_tab import ManagementTab

class MainWindow(QMainWindow):
    def __init__(self, db, camera_threads):
        super().__init__()
        self.db = db
        self.camera_threads = camera_threads
        self.setWindowTitle("Evo Smart LPR - Dashboard")
        self.resize(1280, 720)
        
        self.init_ui()

    def init_ui(self):
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        # Dashboard Sekmesi
        self.dashboard_tab = QWidget()
        self.dashboard_layout = QHBoxLayout(self.dashboard_tab)
        
        # Kamera Izgarası (2x2)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.camera_widgets = []
        for i in range(4):
            cw = CameraWidget(i)
            self.camera_widgets.append(cw)
            self.grid_layout.addWidget(cw, i // 2, i % 2)
        
        self.dashboard_layout.addWidget(self.grid_container, stretch=3)

        # Sağ Akış Paneli (Recent Activity)
        self.flow_panel = QFrame()
        self.flow_panel.setFrameShape(QFrame.StyledPanel)
        self.flow_panel.setFixedWidth(300)
        self.flow_layout = QVBoxLayout(self.flow_panel)
        
        self.flow_label = QLabel("Son Geçişler")
        self.flow_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        self.flow_layout.addWidget(self.flow_label)
        
        self.log_list = QListWidget()
        self.flow_layout.addWidget(self.log_list)
        
        self.dashboard_layout.addWidget(self.flow_panel, stretch=1)
        
        self.central_widget.addTab(self.dashboard_tab, "Dashboard")

        # Plaka Yönetim Sekmesi
        self.mgmt_tab = ManagementTab(self.db)
        self.central_widget.addTab(self.mgmt_tab, "Plaka Yönetimi")

        # Kamera Thread Bağlantıları
        for i, thread in enumerate(self.camera_threads):
            if i < len(self.camera_widgets):
                thread.change_pixmap_signal.connect(self.camera_widgets[i].update_image)
                thread.plate_detected_signal.connect(self.on_plate_detected)

    @Slot(dict)
    def on_plate_detected(self, data):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)

        # Plaka Görseli (Crop)
        crop_label = QLabel()
        crop_label.setFixedSize(100, 45)
        crop_label.setScaledContents(True)
        if data.get('crop') is not None:
            rgb_crop = cv2.cvtColor(data['crop'], cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_crop.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_crop.data, w, h, bytes_per_line, QImage.Format_RGB888)
            crop_label.setPixmap(QPixmap.fromImage(qt_image))
        layout.addWidget(crop_label)

        # Bilgi Etiketi
        status_text = data.get('status', 'Unknown')
        info_label = QLabel(f"<b>{data['plate']}</b><br><small>{data['timestamp']}</small>")
        
        if status_text == 'Allowed':
            info_label.setStyleSheet("color: green;")
        elif status_text == 'Banned':
            info_label.setStyleSheet("color: red;")
        else:
            info_label.setStyleSheet("color: #555;")
            
        layout.addWidget(info_label)
        layout.addStretch()

        item = QListWidgetItem()
        item.setSizeHint(container.sizeHint())
        self.log_list.insertItem(0, item)
        self.log_list.setItemWidget(item, container)

        if self.log_list.count() > 50:
            self.log_list.takeItem(50)