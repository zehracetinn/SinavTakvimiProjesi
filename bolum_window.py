from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem
)
import sqlite3

class BolumWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bölüm Yönetimi (Admin Modülü)")
        self.setGeometry(400, 200, 500, 400)

        self.conn = sqlite3.connect("sinav_takvimi.db")
        self.cur = self.conn.cursor()

        self.setup_ui()
        self.load_departments()

    def setup_ui(self):
        title = QLabel("🏫 Bölüm Yönetimi")
        title.setStyleSheet("font-size:18px; font-weight:bold; margin-bottom:10px;")

        lbl_name = QLabel("Bölüm Adı:")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Örn: Bilgisayar Mühendisliği")

        btn_add = QPushButton("Bölüm Ekle")
        btn_add.setStyleSheet("background-color:#2ecc71; color:white; font-weight:bold;")
        btn_add.clicked.connect(self.add_department)

        btn_delete = QPushButton("Seçili Bölümü Sil")
        btn_delete.setStyleSheet("background-color:#e74c3c; color:white; font-weight:bold;")
        btn_delete.clicked.connect(self.delete_department)

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(2)
        self.tbl.setHorizontalHeaderLabels(["ID", "Bölüm Adı"])
        self.tbl.setColumnWidth(1, 300)

        hbox = QHBoxLayout()
        hbox.addWidget(lbl_name)
        hbox.addWidget(self.txt_name)
        hbox.addWidget(btn_add)

        vbox = QVBoxLayout()
        vbox.addWidget(title)
        vbox.addLayout(hbox)
        vbox.addWidget(self.tbl)
        vbox.addWidget(btn_delete)
        self.setLayout(vbox)

    def load_departments(self):
        self.tbl.setRowCount(0)
        self.cur.execute("SELECT id, bolum_adi FROM Bolumler")
        for row_idx, row_data in enumerate(self.cur.fetchall()):
            self.tbl.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                self.tbl.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

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
