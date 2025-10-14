import pandas as pd
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem
)

class OgrenciYukleWindow(QWidget):
    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("Öğrenci Listesi Yükle")
        self.setGeometry(400, 200, 700, 500)

        self.conn = sqlite3.connect("sinav_takvimi.db")
        self.cur = self.conn.cursor()
        self.setup_ui()

    def setup_ui(self):
        title = QLabel("🎓 Öğrenci Listesi Yükleme ve Görüntüleme")
        title.setStyleSheet("font-size:18px; font-weight:bold; margin-bottom:10px;")

        btn_upload = QPushButton("📁 Excel Dosyası Seç ve Yükle")
        btn_upload.setStyleSheet("background-color:#3498db; color:white; font-weight:bold;")
        btn_upload.clicked.connect(self.upload_excel)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Öğrenci No", "Ad Soyad", "Sınıf", "Ders Kodu"])

        vbox = QVBoxLayout()
        vbox.addWidget(title)
        vbox.addWidget(btn_upload)
        vbox.addWidget(self.table)
        self.setLayout(vbox)

    def upload_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Excel Dosyası Seç", "", "Excel Dosyaları (*.xlsx *.xls)")
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)
            required_columns = {"OgrenciNo", "AdSoyad", "Sinif", "DersKodu"}
            if not required_columns.issubset(df.columns):
                QMessageBox.warning(self, "Uyarı", "Excel dosyası uygun formatta değil!")
                return

            for _, row in df.iterrows():
                self.cur.execute("""
                    INSERT INTO Ogrenci_Ders_Kayitlari (ogrenci_no, ad_soyad, sinif, ders_kodu, bolum_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (row["OgrenciNo"], row["AdSoyad"], row["Sinif"], row["DersKodu"], self.bolum_id))
            self.conn.commit()

            QMessageBox.information(self, "Başarılı", "Öğrenciler başarıyla yüklendi.")
            self.show_table(df)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya okunamadı veya veritabanına eklenemedi:\n{str(e)}")

    def show_table(self, df):
        self.table.setRowCount(0)
        for i, row in df.iterrows():
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(row["OgrenciNo"])))
            self.table.setItem(i, 1, QTableWidgetItem(row["AdSoyad"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(row["Sinif"])))
            self.table.setItem(i, 3, QTableWidgetItem(str(row["DersKodu"])))
