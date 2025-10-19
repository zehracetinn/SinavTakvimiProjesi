import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from database_helper import DatabaseHelper


class OgrenciListesiWindow(QWidget):
    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("👩‍🎓 Öğrenci Ders Listesi")
        self.setGeometry(400, 200, 800, 500)
        self.setup_ui()

    def setup_ui(self):
        # Başlık
        title = QLabel("👩‍🎓 Öğrenci Ders Bilgisi")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                background-color: #1abc9c;
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 15px;
            }
        """)

        # Arama alanı
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Öğrenci numarasını girin...")

        btn_search = QPushButton("Ara")
        btn_search.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1abc9c;
            }
        """)
        btn_search.clicked.connect(self.search_student)

        hbox = QHBoxLayout()
        hbox.addWidget(self.search_input)
        hbox.addWidget(btn_search)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Ders Kodu", "Ders Adı"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #fefefe;
                alternate-background-color: #f4f6f4;
                color: black;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #1abc9c;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

        # Layout
        vbox = QVBoxLayout()
        vbox.addWidget(title)
        vbox.addLayout(hbox)
        vbox.addWidget(self.table)
        self.setLayout(vbox)

    def search_student(self):
        ogr_no = self.search_input.text().strip()
        if not ogr_no:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir öğrenci numarası girin.")
            return

        try:
            conn = DatabaseHelper.get_connection()
            cur = conn.cursor()
            cur.execute("""
    SELECT O.ders_kodu, D.ders_adi
    FROM Ogrenci_Ders_Kayitlari O
    JOIN Dersler D ON O.ders_kodu = D.ders_kodu
    WHERE O.ogrenci_no = ? AND O.bolum_id = ?
    ORDER BY O.ders_kodu
        """, (ogr_no, self.bolum_id))

            rows = cur.fetchall()

            self.table.setRowCount(0)
            if not rows:
                QMessageBox.information(self, "Bilgi", "Bu öğrenciye ait ders kaydı bulunamadı.")
                return

            for i, (ders_kodu, ders_adi) in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(ders_kodu)))
                self.table.setItem(i, 1, QTableWidgetItem(str(ders_adi)))

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler alınırken hata oluştu:\n{e}")
