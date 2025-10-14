import sqlite3
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QFileDialog, QMessageBox, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt

class DersYukleWindow(QWidget):
    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("📘 Ders Listesi Yükleme")
        self.setGeometry(450, 250, 800, 500)
        self.setup_ui()

    def setup_ui(self):
        title = QLabel("Ders Listesi Yükleme (Excel Dosyasından)")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:bold; margin-bottom:15px;")

        self.upload_btn = QPushButton("📂 Excel Dosyası Seç")
        self.upload_btn.setStyleSheet("background-color:#005BBB; color:white; font-weight:bold; padding:8px; border-radius:5px;")
        self.upload_btn.clicked.connect(self.load_excel)

        self.save_btn = QPushButton("💾 Veritabanına Kaydet")
        self.save_btn.setStyleSheet("background-color:#27ae60; color:white; font-weight:bold; padding:8px; border-radius:5px;")
        self.save_btn.clicked.connect(self.save_to_db)
        self.save_btn.setEnabled(False)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Ders Kodu", "Ders Adı", "Öğretim Üyesi", "Sınıf", "Yapı"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.df = None  # Excel verilerini geçici olarak tutacağız

    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Excel Dosyası Seç", "", "Excel Dosyaları (*.xlsx *.xls)")
        if not file_path:
            return

        try:
            self.df = pd.read_excel(file_path)
            expected_cols = ["Ders Kodu", "Ders Adı", "Öğretim Üyesi", "Sınıf", "Yapı"]

            if not all(col in self.df.columns for col in expected_cols):
                QMessageBox.critical(self, "Hata", f"Excel formatı hatalı! Beklenen sütunlar:\n{expected_cols}")
                return

            self.table.setRowCount(len(self.df))
            for i, row in self.df.iterrows():
                self.table.setItem(i, 0, QTableWidgetItem(str(row["Ders Kodu"])))
                self.table.setItem(i, 1, QTableWidgetItem(str(row["Ders Adı"])))
                self.table.setItem(i, 2, QTableWidgetItem(str(row["Öğretim Üyesi"])))
                self.table.setItem(i, 3, QTableWidgetItem(str(row["Sınıf"])))
                self.table.setItem(i, 4, QTableWidgetItem(str(row["Yapı"])))

            self.save_btn.setEnabled(True)
            QMessageBox.information(self, "Başarılı", "Excel dosyası başarıyla yüklendi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel okunamadı: {str(e)}")

    def save_to_db(self):
        if self.df is None or self.df.empty:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek veri yok!")
            return

        try:
            conn = sqlite3.connect("sinav_takvimi.db")
            cursor = conn.cursor()

            for _, row in self.df.iterrows():
                cursor.execute("""
                    INSERT INTO Dersler (ders_kodu, ders_adi, ogretim_uyesi, sinif, yapi, bolum_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(row["Ders Kodu"]),
                    str(row["Ders Adı"]),
                    str(row["Öğretim Üyesi"]),
                    int(row["Sınıf"]),
                    str(row["Yapı"]),
                    self.bolum_id
                ))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Kaydedildi", f"{len(self.df)} ders başarıyla veritabanına kaydedildi!")
            self.save_btn.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, "Veritabanı Hatası", str(e))
