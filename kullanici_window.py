from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QComboBox, QMessageBox, QTableWidget, QTableWidgetItem
)
import sqlite3

class KullaniciWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kullanıcı Yönetimi (Admin Modülü)")
        self.setGeometry(400, 200, 600, 500)

        self.conn = sqlite3.connect("sinav_takvimi.db")
        self.cur = self.conn.cursor()

        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        title = QLabel("👤 Kullanıcı Yönetimi")
        title.setStyleSheet("font-size:18px; font-weight:bold; margin-bottom:10px;")

        # --- Kullanıcı ekleme alanı ---
        lbl_email = QLabel("E-posta:")
        self.txt_email = QLineEdit()
        lbl_pass = QLabel("Şifre:")
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)

        lbl_role = QLabel("Rol:")
        self.cmb_role = QComboBox()
        self.cmb_role.addItems(["Admin", "Bölüm Koordinatörü"])

        lbl_bolum = QLabel("Bölüm:")
        self.cmb_bolum = QComboBox()
        self.load_departments()

        btn_add = QPushButton("Kullanıcı Ekle")
        btn_add.setStyleSheet("background-color:#2ecc71; color:white; font-weight:bold;")
        btn_add.clicked.connect(self.add_user)

        # --- Kullanıcı tablosu ---
        self.tbl_users = QTableWidget()
        self.tbl_users.setColumnCount(4)
        self.tbl_users.setHorizontalHeaderLabels(["ID", "E-posta", "Rol", "Bölüm"])
        self.tbl_users.setColumnWidth(1, 200)

        btn_delete = QPushButton("Seçili Kullanıcıyı Sil")
        btn_delete.setStyleSheet("background-color:#e74c3c; color:white; font-weight:bold;")
        btn_delete.clicked.connect(self.delete_user)

        # --- Layout ---
        form = QHBoxLayout()
        form.addWidget(lbl_email)
        form.addWidget(self.txt_email)
        form.addWidget(lbl_pass)
        form.addWidget(self.txt_pass)
        form.addWidget(lbl_role)
        form.addWidget(self.cmb_role)
        form.addWidget(lbl_bolum)
        form.addWidget(self.cmb_bolum)
        form.addWidget(btn_add)

        vbox = QVBoxLayout()
        vbox.addWidget(title)
        vbox.addLayout(form)
        vbox.addWidget(self.tbl_users)
        vbox.addWidget(btn_delete)

        self.setLayout(vbox)

    def load_departments(self):
        self.cmb_bolum.clear()
        self.cur.execute("SELECT bolum_adi FROM Bolumler")
        for row in self.cur.fetchall():
            self.cmb_bolum.addItem(row[0])

    def load_users(self):
        self.tbl_users.setRowCount(0)
        query = """
            SELECT K.id, K.eposta, K.rol, B.bolum_adi 
            FROM Kullanicilar K 
            LEFT JOIN Bolumler B ON K.bolum_id = B.id
        """
        self.cur.execute(query)
        for row_idx, row_data in enumerate(self.cur.fetchall()):
            self.tbl_users.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                self.tbl_users.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

    def add_user(self):
        email = self.txt_email.text().strip()
        sifre = self.txt_pass.text().strip()
        rol = self.cmb_role.currentText()
        bolum_adi = self.cmb_bolum.currentText()

        if not email or not sifre:
            QMessageBox.warning(self, "Uyarı", "Lütfen e-posta ve şifre giriniz.")
            return

        self.cur.execute("SELECT id FROM Bolumler WHERE bolum_adi=?", (bolum_adi,))
        bolum_id = self.cur.fetchone()[0]

        self.cur.execute("INSERT INTO Kullanicilar (eposta, sifre, rol, bolum_id) VALUES (?, ?, ?, ?)",
                         (email, sifre, rol, bolum_id))
        self.conn.commit()
        QMessageBox.information(self, "Başarılı", "Kullanıcı eklendi.")
        self.load_users()

    def delete_user(self):
        selected = self.tbl_users.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek kullanıcıyı seçin.")
            return

        user_id = self.tbl_users.item(selected, 0).text()
        self.cur.execute("DELETE FROM Kullanicilar WHERE id=?", (user_id,))
        self.conn.commit()
        QMessageBox.information(self, "Silindi", "Kullanıcı silindi.")
        self.load_users()
