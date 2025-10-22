from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QComboBox, QMessageBox, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
import sqlite3


class KullaniciWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kullanıcı Yönetimi (Admin Modülü)")
        self.setGeometry(400, 200, 700, 520)

        # 🔹 Arka plan görseli yolu
        self.bg_path =" C:\\Users\\PC\\Documents\\GitHub\\SinavTakvimiProjesi\\kou.jpg"

        self.conn = sqlite3.connect("sinav_takvimi.db")
        self.cur = self.conn.cursor()

        self.setup_ui()
        self.load_users()

    # 🔹 Arka plan resmi
    def paintEvent(self, event):
        painter = QPainter(self)
        pixmap = QPixmap(self.bg_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.setOpacity(0.35)
            painter.drawPixmap(0, 0, scaled)
        painter.setOpacity(1.0)
        super().paintEvent(event)

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; color: black; }
            QLabel {
                color: black; font-size: 15px; font-weight: 600;
                background-color: rgba(255, 255, 255, 180);
                border-radius: 4px; padding: 2px 4px;
            }
            QLineEdit, QComboBox {
                border: 2px solid #007b5e; border-radius: 6px; padding: 6px;
                background-color: rgba(255, 255, 255, 220); font-size: 14px; color: black;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #005b44; background-color: rgba(255, 255, 255, 240);
            }
            QPushButton { border-radius: 6px; padding: 8px; font-weight: bold; font-size: 14px; }
            QTableWidget {
                background-color: rgba(255, 255, 255, 230);
                color: black; border: 2px solid #007b5e; border-radius: 6px;
                gridline-color: #00823b; selection-background-color: #c8f7c5;
                selection-color: black; font-size: 13px;
            }
            QHeaderView::section {
                background-color: #00823b; color: white; padding: 6px;
                font-weight: bold; border: none;
            }
        """)

        # --- Başlık ---
        title = QLabel("👤 Kullanıcı Yönetimi")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            background-color: rgba(0, 130, 59, 220);
            color: white; font-size: 18px; font-weight: bold;
            padding: 10px; border-radius: 4px; margin-bottom: 10px;
        """)

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
        btn_add.setStyleSheet("""
            QPushButton { background-color: #00823b; color: white; }
            QPushButton:hover { background-color: #006b30; }
        """)
        btn_add.clicked.connect(self.add_user)

        # --- Kullanıcı tablosu ---
        self.tbl_users = QTableWidget()
        self.tbl_users.setColumnCount(4)
        self.tbl_users.setHorizontalHeaderLabels(["ID", "E-posta", "Rol", "Bölüm"])
        self.tbl_users.setColumnWidth(1, 200)

        btn_delete = QPushButton("Seçili Kullanıcıyı Sil")
        btn_delete.setStyleSheet("""
            QPushButton { background-color: #e74c3c; color: white; }
            QPushButton:hover { background-color: #c0392b; }
        """)
        btn_delete.clicked.connect(self.delete_user)

        # --- Layout ---
        form = QHBoxLayout()
        form.setSpacing(8)
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
        vbox.setSpacing(10)
        vbox.addWidget(title)
        vbox.addLayout(form)
        vbox.addWidget(self.tbl_users)
        vbox.addWidget(btn_delete)
        self.setLayout(vbox)

    # --- Veritabanı işlemleri ---
    def load_departments(self):
        self.cmb_bolum.clear()
        self.cur.execute("SELECT bolum_adi FROM Bolumler")
        for row in self.cur.fetchall():
            self.cmb_bolum.addItem(row[0])

    def load_users(self):
        self.tbl_users.setRowCount(0)
        query = """
            SELECT K.kullanici_id, K.eposta, K.rol, B.bolum_adi
            FROM Kullanicilar K
            LEFT JOIN Bolumler B ON K.bolum_id = B.bolum_id
        """
        self.cur.execute(query)
        for row_idx, row_data in enumerate(self.cur.fetchall()):
            self.tbl_users.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                item.setForeground(Qt.GlobalColor.black)
                self.tbl_users.setItem(row_idx, col_idx, item)

    def add_user(self):
        try:
            email = self.txt_email.text().strip()
            sifre = self.txt_pass.text().strip()
            rol = self.cmb_role.currentText()
            bolum_adi = self.cmb_bolum.currentText()

            if not email or not sifre:
                QMessageBox.warning(self, "Uyarı", "Lütfen e-posta ve şifre giriniz.")
                return

            # Bölüm ID'sini al
            self.cur.execute("SELECT bolum_id FROM Bolumler WHERE bolum_adi=?", (bolum_adi,))
            result = self.cur.fetchone()

            if result is None:
                QMessageBox.critical(self, "Hata", f"Bölüm '{bolum_adi}' bulunamadı!")
                return

            bolum_id = result[0]

            # E-posta zaten var mı kontrol et
            self.cur.execute("SELECT COUNT(*) FROM Kullanicilar WHERE eposta=?", (email,))
            if self.cur.fetchone()[0] > 0:
                QMessageBox.warning(self, "Uyarı", "Bu e-posta adresi zaten kayıtlı!")
                return

            # Yeni kullanıcıyı ekle
            self.cur.execute("""
                INSERT INTO Kullanicilar (eposta, sifre, rol, bolum_id)
                VALUES (?, ?, ?, ?)
            """, (email, sifre, rol, bolum_id))

            self.conn.commit()
            QMessageBox.information(self, "Başarılı", "Kullanıcı başarıyla eklendi.")
            self.load_users()

            # Alanları temizle
            self.txt_email.clear()
            self.txt_pass.clear()
            self.cmb_role.setCurrentIndex(0)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Veritabanı Hatası", f"SQLite hatası oluştu:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Beklenmeyen bir hata oluştu:\n{e}")

    def delete_user(self):
        selected = self.tbl_users.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek kullanıcıyı seçin.")
            return

        user_id = self.tbl_users.item(selected, 0).text()
        self.cur.execute("DELETE FROM Kullanicilar WHERE kullanici_id=?", (user_id,))
        self.conn.commit()
        QMessageBox.information(self, "Silindi", "Kullanıcı silindi.")
        self.load_users()
