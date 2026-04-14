from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                                 QTableWidgetItem, QPushButton, QLineEdit, QComboBox, QLabel, QMessageBox)
from PySide6.QtCore import Qt

class ManagementTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        input_layout = QHBoxLayout()
        self.plate_input = QLineEdit()
        self.plate_input.setPlaceholderText("Plaka Giriniz (Örn: 06ABC123)")
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Allowed", "Banned", "Guest"])
        
        add_btn = QPushButton("Kaydet / Güncelle")
        add_btn.clicked.connect(self.add_plate)
        
        input_layout.addWidget(QLabel("Plaka:"))
        input_layout.addWidget(self.plate_input)
        input_layout.addWidget(QLabel("Durum:"))
        input_layout.addWidget(self.status_combo)
        input_layout.addWidget(add_btn)
        
        layout.addLayout(input_layout)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Plaka", "Durum"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        controls_layout = QHBoxLayout()
        refresh_btn = QPushButton("Listeyi Yenile")
        refresh_btn.clicked.connect(self.refresh_list)
        delete_btn = QPushButton("Seçileni Sil")
        delete_btn.clicked.connect(self.delete_plate)
        
        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(delete_btn)
        layout.addLayout(controls_layout)

        self.refresh_list()

    def refresh_list(self):
        plates = self.db.get_all_plates()
        self.table.setRowCount(0)
        if plates:
            for plate, status in plates:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(plate))
                self.table.setItem(row, 1, QTableWidgetItem(status))

    def add_plate(self):
        plate = self.plate_input.text().strip().upper()
        status = self.status_combo.currentText()
        if plate:
            if self.db.add_plate(plate, status):
                self.refresh_list()
                self.plate_input.clear()
            else:
                QMessageBox.warning(self, "Hata", "Plaka eklenemedi.")
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir plaka girin.")

    def delete_plate(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            plate = self.table.item(current_row, 0).text()
            if self.db.delete_plate(plate):
                self.refresh_list()
            else:
                QMessageBox.warning(self, "Hata", "Plaka silinemedi.")