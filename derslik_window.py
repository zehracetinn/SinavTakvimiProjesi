import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt

class DerslikWindow(QWidget):
    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("🏫 Derslik Yönetimi")
        self.setGeometry(450, 200, 800, 500)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        title = QLabel("Derslik Yönetimi")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:bold;")

        # Derslik Bilgi Girişi
        self.kod_input = QLineEdit()
        self.kod_input.setPlaceholderText("Derslik Kodu (örnek: B101)")

        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("Derslik Adı (örnek: Yazılım Lab 1)")

        self.kapasite_input = QSpinBox()
        self.kapasite_input.setRange(1, 300)
        self.kapasite_input.setPrefix("Kapasite: ")

        self.sira_input = QSpinBox()
        self.sira_input.setRange(1, 30)
        self.sira_input.setPrefix("Boyuna sıra: ")

        self.sutun_input = QSpinBox()
        self.sutun_input.setRange(1, 30)
        self.sutun_input.setPrefix("Enine sıra: ")

        self.duzen_box = QComboBox()
        self.duzen_box.addItems(["2'li", "3'lü"])

        # Butonlar
        self.add_btn = QPushButton("➕ Ekle / Güncelle")
        self.add_btn.setStyleSheet("background-color:#27ae60; color:white; font-weight:bold;")
        self.add_btn.clicked.connect(self.add_or_update_derslik)

        self.del_btn = QPushButton("🗑️ Sil")
        self.del_btn.setStyleSheet("background-color:#c0392b; color:white; font-weight:bold;")
        self.del_btn.clicked.connect(self.delete_derslik)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Kodu", "Adı", "Kapasite", "Sıra", "Sütun"])
        self.table.cellClicked.connect(self.select_row)

        # Layout
        form_layout = QVBoxLayout()
        form_layout.addWidget(title)
        form_layout.addWidget(self.kod_input)
        form_layout.addWidget(self.ad_input)
        form_layout.addWidget(self.kapasite_input)
        form_layout.addWidget(self.sira_input)
        form_layout.addWidget(self.sutun_input)
        form_layout.addWidget(self.duzen_box)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)

        form_layout.addLayout(btn_layout)
        form_layout.addWidget(self.table)
        self.setLayout(form_layout)

    def load_data(self):
        conn = sqlite3.connect("sinav_takvimi.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT derslik_id, derslik_kodu, derslik_adi, kapasite, sira_sayisi, sutun_sayisi
            FROM Derslikler
            WHERE bolum_id = ?
        """, (self.bolum_id,))
        data = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, col_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

    def add_or_update_derslik(self):
        kod = self.kod_input.text().strip()
        ad = self.ad_input.text().strip()
        kapasite = self.kapasite_input.value()
        sira = self.sira_input.value()
        sutun = self.sutun_input.value()

        if not kod or not ad:
            QMessageBox.warning(self, "Uyarı", "Lütfen tüm alanları doldurun.")
            return

        conn = sqlite3.connect("sinav_takvimi.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT derslik_id FROM Derslikler WHERE derslik_kodu = ? AND bolum_id = ?
        """, (kod, self.bolum_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE Derslikler
                SET derslik_adi = ?, kapasite = ?, sira_sayisi = ?, sutun_sayisi = ?
                WHERE derslik_kodu = ? AND bolum_id = ?
            """, (ad, kapasite, sira, sutun, kod, self.bolum_id))
            QMessageBox.information(self, "Güncellendi", f"{kod} güncellendi.")
        else:
            cursor.execute("""
                INSERT INTO Derslikler (derslik_kodu, derslik_adi, kapasite, sira_sayisi, sutun_sayisi, bolum_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (kod, ad, kapasite, sira, sutun, self.bolum_id))
            QMessageBox.information(self, "Eklendi", f"{kod} başarıyla eklendi.")

        conn.commit()
        conn.close()
        self.load_data()

    def delete_derslik(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Uyarı", "Silmek için bir satır seçin.")
            return

        derslik_id = self.table.item(selected, 0).text()

        conn = sqlite3.connect("sinav_takvimi.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Derslikler WHERE derslik_id = ?", (derslik_id,))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Silindi", "Derslik başarıyla silindi.")
        self.load_data()

    def select_row(self, row, col):
        self.kod_input.setText(self.table.item(row, 1).text())
        self.ad_input.setText(self.table.item(row, 2).text())
        self.kapasite_input.setValue(int(self.table.item(row, 3).text()))
        self.sira_input.setValue(int(self.table.item(row, 4).text()))
        self.sutun_input.setValue(int(self.table.item(row, 5).text()))

