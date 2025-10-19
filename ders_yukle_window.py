import os
import sqlite3
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QFileDialog, QMessageBox,
    QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from database_helper import DatabaseHelper


class DersYukleWindow(QWidget):
    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("📘 Ders Listesi Yükleme")
        self.setGeometry(450, 250, 800, 500)
        self.df = None
        self.setup_ui()

    # ---------------- UI ----------------
    def setup_ui(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(base_dir, 'kou.jpg').replace('\\', '/')
        except NameError:
            image_path = 'kou.jpg'

        self.setStyleSheet(f"""
            DersYukleWindow {{
                background-image: url('{image_path}');
                background-repeat: no-repeat;
                background-position: center;
                background-color: #F5F5F5;
            }}
        """)

        title = QLabel("Ders Listesi Yükleme (Excel Dosyasından)")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.75);
            color: #2c3e50;
            font-size: 20px;
            font-weight: bold;
            padding: 10px;
            margin-bottom: 10px;
            border: 2px solid #4CAF50;
            border-radius: 8px;
        """)

        button_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """

        self.upload_btn = QPushButton("📂 Excel Dosyası Seç")
        self.upload_btn.setStyleSheet(button_style)
        self.upload_btn.clicked.connect(self.load_excel)

        self.save_btn = QPushButton("💾 Veritabanına Kaydet")
        self.save_btn.setStyleSheet(button_style)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_to_db)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Ders Kodu", "Ders Adı", "Öğretim Üyesi", "Sınıf", "Yapı"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)

        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #cccccc;
                background-color: rgba(255, 255, 255, 0.85);
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border: 1px solid #4CAF50;
                font-weight: bold;
            }
            QTableWidget::item:alternate {
                background-color: rgba(230, 230, 230, 0.8);
            }
        """)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.table)
        self.setLayout(layout)

    # ---------------- EXCEL OKUMA ----------------
    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Excel Dosyası Seç", "", "Excel Dosyaları (*.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            df_raw = pd.read_excel(file_path, header=None)
            data = []
            current_class = None

            for i, row in df_raw.iterrows():
                first_cell = str(row[0]).strip().lower() if pd.notna(row[0]) else ""

                # “1. Sınıf”, “2. Sınıf” gibi satırları algıla
                if "sınıf" in first_cell:
                    current_class = first_cell.replace(".", "").replace("sınıf", "").strip()
                    if not current_class.isdigit():
                        current_class = ''.join([c for c in current_class if c.isdigit()])
                    if not current_class:
                        current_class = "1"
                    continue

                # Gerçek başlık satırını atla
                if "ders kodu" in first_cell or "dersin" in str(row[1]).lower():
                    continue

                # Boş satırları geç
                if pd.isna(row[0]) or pd.isna(row[1]) or pd.isna(row[2]):
                    continue

                data.append({
                    "Ders Kodu": str(row[0]).strip(),
                    "Ders Adı": str(row[1]).strip(),
                    "Öğretim Üyesi": str(row[2]).strip(),
                    "Sınıf": current_class if current_class else "1",
                    "Yapı": "Zorunlu"  # varsayılan değer
                })

            if not data:
                QMessageBox.critical(self, "Hata", "Hiç geçerli ders satırı bulunamadı!")
                return

            self.df = pd.DataFrame(data)
            self.table.setRowCount(len(self.df))

            for i, row in self.df.iterrows():
                self.table.setItem(i, 0, QTableWidgetItem(row["Ders Kodu"]))
                self.table.setItem(i, 1, QTableWidgetItem(row["Ders Adı"]))
                self.table.setItem(i, 2, QTableWidgetItem(row["Öğretim Üyesi"]))
                self.table.setItem(i, 3, QTableWidgetItem(str(row["Sınıf"])))
                self.table.setItem(i, 4, QTableWidgetItem(row["Yapı"]))

            self.save_btn.setEnabled(True)
            QMessageBox.information(self, "Başarılı", "Excel dosyası başarıyla yüklendi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel okunamadı:\n{str(e)}")

    # ---------------- VERİTABANINA KAYDETME ----------------
    def save_to_db(self):
        if self.df is None or self.df.empty:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek veri yok!")
            return

        try:
            conn = DatabaseHelper.get_connection()
            cursor = conn.cursor()

            added, skipped = 0, 0
            for _, row in self.df.iterrows():
                ders_kodu = str(row["Ders Kodu"]).strip()
                cursor.execute(
                    "SELECT COUNT(*) FROM Dersler WHERE ders_kodu=? AND bolum_id=?",
                    (ders_kodu, self.bolum_id)
                )
                if cursor.fetchone()[0] > 0:
                    skipped += 1
                    continue

                cursor.execute("""
                    INSERT INTO Dersler (ders_kodu, ders_adi, ogretim_uyesi, sinif, yapi, bolum_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ders_kodu,
                    str(row["Ders Adı"]),
                    str(row["Öğretim Üyesi"]),
                    int(row["Sınıf"]),
                    str(row["Yapı"]),
                    self.bolum_id
                ))
                added += 1

            conn.commit()  # autocommit modda olsa da güvenli
            QMessageBox.information(self, "Başarılı", f"{added} ders eklendi, {skipped} atlandı.")
            self.save_btn.setEnabled(False)

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Hata", str(e))
