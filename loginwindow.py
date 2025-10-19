import sys



import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap, QBrush, QColor

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sınav Takvimi Giriş Ekranı")
        self.setGeometry(500, 250, 420, 280)
        self.bg_path = "/Users/USER/Desktop/SinavTakvimiProjesi/hakkimizdabanner.jpg"
        self.setup_ui()

    def paintEvent(self, event):
        """Arka plan resmini çiz"""
        painter = QPainter(self)
        pixmap = QPixmap(self.bg_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
            painter.setOpacity(0.4)  # 🔹 %40 saydamlık (silik görünüm)
            painter.drawPixmap(0, 0, scaled)
        painter.setOpacity(1.0)  # Normal saydamlığa geri dön
        super().paintEvent(event)

    def setup_ui(self):
        # --- Genel Stil ---
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #003300;
            }
            QLabel {
                font-size: 15px;
                font-weight: 600;
                color: #004d26;
                background-color: rgba(255, 255, 255, 180);
                border-radius: 4px;
                padding: 2px 4px;
            }
            QLineEdit {
                border: 2px solid #007b5e;
                border-radius: 6px;
                padding: 6px;
                background-color: rgba(255, 255, 255, 210);
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #005b44;
                background-color: rgba(255, 255, 255, 235);
            }
            QPushButton {
                background-color: #00823b;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #006b30;
            }
        """)

        # --- Başlık ---
        self.header = QLabel("Kocaeli Üniversitesi Dinamik Sınav Takvimi Sistemi")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header.setStyleSheet("""
            background-color: rgba(0, 130, 59, 200);
            color: white;
            font-size: 17px;
            font-weight: bold;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
        """)

        # --- E-posta ---
        self.email_label = QLabel("E-posta Adresi")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("örnek: admin@kocaeli.edu.tr")

        # --- Şifre ---
        self.password_label = QLabel("Şifre")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Şifrenizi girin")

        # --- Giriş butonu ---
        self.login_button = QPushButton("Giriş Yap")
        self.login_button.clicked.connect(self.login_action)

        # --- Düzen ---
        vbox = QVBoxLayout()
        vbox.setSpacing(10)
        vbox.addWidget(self.header)
        vbox.addWidget(self.email_label)
        vbox.addWidget(self.email_input)
        vbox.addWidget(self.password_label)
        vbox.addWidget(self.password_input)
        vbox.addWidget(self.login_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(vbox)

    def login_action(self):
        eposta = self.email_input.text().strip()
        sifre = self.password_input.text().strip()

        if not eposta or not sifre:
            QMessageBox.warning(self, "Uyarı", "E-posta ve şifre alanı boş bırakılamaz.")
            return

        try:
            conn = sqlite3.connect("sinav_takvimi.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rol, bolum_id FROM Kullanicilar
                WHERE eposta = ? AND sifre = ?
            """, (eposta, sifre))
            result = cursor.fetchone()
            conn.close()

            if result:
                rol, bolum_id = result
                from main_window import MainWindow
                self.main_window = MainWindow(rol, bolum_id)
                self.main_window.show()
                self.close()
            else:
                QMessageBox.critical(self, "Hata", "Geçersiz e-posta veya şifre!")

        except Exception as e:
            QMessageBox.critical(self, "Veritabanı Hatası", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
