from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
import sqlite3


class BolumWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bölüm Yönetimi (Admin Modülü)")
        self.setGeometry(400, 200, 600, 450)

        # 🔹 Arka plan görseli yolu
        self.bg_path = "/Users/USER/Desktop/SinavTakvimiProjesi/kou.jpg"

        self.conn = sqlite3.connect("sinav_takvimi.db")
        self.cur = self.conn.cursor()

        self.setup_ui()
        self.load_departments()

    # 🔹 Arka plan resmi çizimi
    def paintEvent(self, event):
        painter = QPainter(self)
        pixmap = QPixmap(self.bg_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.setOpacity(0.35)  # 🔸 %35 saydamlık
            painter.drawPixmap(0, 0, scaled)
        painter.setOpacity(1.0)
        super().paintEvent(event)

    def setup_ui(self):
        # --- Genel Stil ---
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                color: black;
            }
            QLabel {
                color: black;
                font-size: 15px;
                font-weight: 600;
                background-color: rgba(255, 255, 255, 180);
                border-radius: 4px;
                padding: 2px 4px;
            }
            QLineEdit {
                border: 2px solid #007b5e;
                border-radius: 6px;
                padding: 6px;
                background-color: rgba(255, 255, 255, 220);
                font-size: 14px;
                color: black;
            }
            QLineEdit:focus {
                border: 2px solid #005b44;
                background-color: rgba(255, 255, 255, 240);
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QTableWidget {
                background-color: rgba(255, 255, 255, 230);
                color: black;
                border: 2px solid #007b5e;
                border-radius: 6px;
                gridline-color: #00823b;
                selection-background-color: #c8f7c5;
                selection-color: black;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #00823b;
                color: white;
                padding: 6px;
                font-weight: bold;
                border: none;
            }
        """)

        # --- Başlık ---
        title = QLabel("🏫 Bölüm Yönetimi")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            background-color: rgba(0, 130, 59, 220);
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        """)

        # --- Giriş alanı ve butonlar ---
        lbl_name = QLabel("Bölüm Adı:")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Örn: Bilgisayar Mühendisliği")

        btn_add = QPushButton("Bölüm Ekle")
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #00823b;
                color: white;
            }
            QPushButton:hover {
                background-color: #006b30;
            }
        """)
        btn_add.clicked.connect(self.add_department)

        btn_delete = QPushButton("Seçili Bölümü Sil")
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_delete.clicked.connect(self.delete_department)

        # --- Tablo ---
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(2)
        self.tbl.setHorizontalHeaderLabels(["ID", "Bölüm Adı"])
        self.tbl.setColumnWidth(1, 320)

        # --- Düzen ---
        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(lbl_name)
        hbox.addWidget(self.txt_name)
        hbox.addWidget(btn_add)

        vbox = QVBoxLayout()
        vbox.setSpacing(10)
        vbox.addWidget(title)
        vbox.addLayout(hbox)
        vbox.addWidget(self.tbl)
        vbox.addWidget(btn_delete)

        self.setLayout(vbox)

    # --- Veritabanı işlemleri ---
    def load_departments(self):
        self.tbl.setRowCount(0)
        self.cur.execute("SELECT id, bolum_adi FROM Bolumler")
        for row_idx, row_data in enumerate(self.cur.fetchall()):
            self.tbl.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                item.setForeground(Qt.GlobalColor.black)
                self.tbl.setItem(row_idx, col_idx, item)

    def add_department(self):
        bolum_adi = self.txt_name.text().strip()
        if not bolum_adi:
            QMessageBox.warning(self, "Uyarı", "Bölüm adı giriniz.")
            return

        self.cur.execute("INSERT INTO Bolumler (bolum_adi) VALUES (?)", (bolum_adi,))
        self.conn.commit()
        QMessageBox.information(self, "Başarılı", "Bölüm eklendi.")
        self.load_departments()

    def delete_department(self):
        selected = self.tbl.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek bölümü seçin.")
            return

        bolum_id = self.tbl.item(selected, 0).text()
        self.cur.execute("DELETE FROM Bolumler WHERE id=?", (bolum_id,))
        self.conn.commit()
        QMessageBox.information(self, "Silindi", "Bölüm silindi.")
        self.load_departments()
