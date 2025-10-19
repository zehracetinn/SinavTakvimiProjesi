import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QFileDialog, QMessageBox,
    QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from database_helper import DatabaseHelper
from unidecode import unidecode



class OgrenciYukleWindow(QWidget):
    data_loaded = pyqtSignal()  # ✅ Excel başarıyla yüklendiğinde ana pencereye sinyal gönderir

    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("🎓 Öğrenci Listesi Yükleme")
        self.setGeometry(400, 200, 900, 600)
        self.df = None
        self.setup_ui()

    # ------------------ ARAYÜZ ------------------
    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QLabel {
                color: #004d26;
                font-size: 16px;
                font-weight: 500;
            }

            QPushButton {
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                color: white;
                border: none;
            }

            QPushButton#upload { background-color: #007bff; }
            QPushButton#upload:hover { background-color: #1a8cff; }

            QPushButton#save { background-color: #00b050; }
            QPushButton#save:hover { background-color: #00cc5c; }

            QPushButton#search { background-color: #f57c00; }
            QPushButton#search:hover { background-color: #ffa31a; }

            QLineEdit {
                border: 2px solid #007b5e;
                border-radius: 5px;
                padding: 6px;
                background-color: white;
                font-size: 13px;
                color: black;
            }

            QTableWidget, QTableView, QAbstractItemView {
                border: 1px solid #c8c8c8;
                background-color: white;
                alternate-background-color: #f2f2f2;
                color: black;
                font-size: 13px;
                selection-background-color: #16a085;
                selection-color: white;
            }

            QHeaderView::section {
                background-color: #007b5e;
                color: white;
                padding: 6px;
                font-weight: bold;
                border: none;
            }
        """)

        # Başlık
        title = QLabel("🎓 Öğrenci Listesi Yükleme ve Görüntüleme")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                background-color: #007b5e;
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
        """)

        # Excel yükleme butonu
        btn_upload = QPushButton("📂 Excel Dosyası Seç")
        btn_upload.setObjectName("upload")
        btn_upload.clicked.connect(self.load_excel)

        # Kaydet butonu
        self.save_btn = QPushButton("💾 Veritabanına Kaydet")
        self.save_btn.setObjectName("save")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_to_db)

        # Arama alanı
        search_label = QLabel("🔍 Öğrenci No:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Öğrenci numarasını girin...")
        btn_search = QPushButton("Ara")
        btn_search.setObjectName("search")
        btn_search.clicked.connect(self.search_student)

        search_layout = QHBoxLayout()
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(btn_search)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Öğrenci No", "Ad Soyad", "Sınıf", "Ders Kodu"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)

        # 🎨 Renklerin beyaz kalmaması için palet uygulandı
        palette = self.table.palette()
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(242, 242, 242))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(22, 160, 133))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.table.setPalette(palette)

        # Ana düzen
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(btn_upload)
        layout.addWidget(self.save_btn)
        layout.addLayout(search_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    # ------------------ EXCEL YÜKLE ------------------


    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Excel Dosyası Seç", "", "Excel Dosyaları (*.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)

            # 🔹 Türkçe karakterleri temizle (unidecode ile)
            df.columns = [
                unidecode(str(c)).strip().replace(" ", "").replace("ı", "i").replace("İ", "I")
                for c in df.columns
            ]

            # 🔹 Sütunları yeniden adlandır
            df.rename(columns={
                "OgrenciNo": "OgrenciNo",
                "OgrenciNumara": "OgrenciNo",
                "OgrenciNumarasi": "OgrenciNo",
                "Ogrenci": "OgrenciNo",
                "AdSoyad": "AdSoyad",
                "Sinif": "Sinif",
                "Ders": "DersKodu"
            }, inplace=True)

            expected_cols = ["OgrenciNo", "AdSoyad", "Sinif", "DersKodu"]
            if not all(col in df.columns for col in expected_cols):
                QMessageBox.critical(
                    self, "Hata",
                    f"Excel formatı hatalı!\nBeklenen sütunlar:\n{expected_cols}\n\nBulunan sütunlar:\n{df.columns.tolist()}"
                )
                return

            # 🔹 Tabloya yükle
            self.df = df.fillna("")
            self.table.setRowCount(len(self.df))
            for i, row in self.df.iterrows():
                for j, col in enumerate(expected_cols):
                    item = QTableWidgetItem(str(row[col]))
                    item.setForeground(QColor(0, 0, 0))
                    self.table.setItem(i, j, item)

            self.save_btn.setEnabled(True)
            QMessageBox.information(self, "Başarılı", "Excel dosyası başarıyla yüklendi.")
            self.data_loaded.emit()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel okunamadı:\n{e}")



    # ------------------ VERİTABANINA KAYDET ------------------
    def save_to_db(self):
        if self.df is None or self.df.empty:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek veri yok!")
            return

        try:
            conn = DatabaseHelper.get_connection()
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE")

            added, skipped = 0, 0
            for _, row in self.df.iterrows():
                ogr_no = str(row["OgrenciNo"]).strip()
                ders_kodu = str(row["DersKodu"]).strip()

                cur.execute("""
                    SELECT COUNT(*) FROM Ogrenci_Ders_Kayitlari 
                    WHERE ogrenci_no=? AND ders_kodu=? AND bolum_id=?
                """, (ogr_no, ders_kodu, self.bolum_id))
                if cur.fetchone()[0] > 0:
                    skipped += 1
                    continue

                cur.execute("""
                    INSERT INTO Ogrenci_Ders_Kayitlari 
                    (ogrenci_no, ad_soyad, sinif, ders_kodu, bolum_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    ogr_no,
                    str(row["AdSoyad"]),
                    str(row["Sinif"]),
                    ders_kodu,
                    self.bolum_id
                ))
                added += 1

            conn.commit()
            QMessageBox.information(self, "Başarılı",
                f"{added} öğrenci kaydı eklendi.\n{skipped} kayıt zaten mevcuttu.")
            self.save_btn.setEnabled(False)
            self.data_loaded.emit()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt sırasında hata oluştu:\n{e}")

    # ------------------ ÖĞRENCİ ARAMA ------------------
    def search_student(self):
        ogr_no = self.search_input.text().strip()
        if not ogr_no:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir öğrenci numarası girin.")
            return

        try:
            conn = DatabaseHelper.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT ogrenci_no, ad_soyad, sinif, ders_kodu
                FROM Ogrenci_Ders_Kayitlari
                WHERE ogrenci_no=? AND bolum_id=?
            """, (ogr_no, self.bolum_id))
            rows = cur.fetchall()

            self.table.setRowCount(0)
            if not rows:
                QMessageBox.information(self, "Bilgi", "Bu öğrenciye ait kayıt bulunamadı.")
                return

            for i, row in enumerate(rows):
                self.table.insertRow(i)
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    item.setForeground(QColor(0, 0, 0))  # 🖤 Hücre metinleri siyah
                    self.table.setItem(i, j, item)

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
