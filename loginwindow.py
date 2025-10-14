import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sınav Takvimi Giriş Ekranı")
        self.setGeometry(500, 250, 400, 250)
        self.setup_ui()

    def setup_ui(self):
        # --- Başlık ---
        self.title_label = QLabel("Dinamik Sınav Takvimi Sistemi")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")

        # --- E-posta ---
        self.email_label = QLabel("E-posta:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("örnek: admin@kocaeli.edu.tr")

        # --- Şifre ---
        self.password_label = QLabel("Şifre:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Şifrenizi girin")

        # --- Giriş butonu ---
        self.login_button = QPushButton("Giriş Yap")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #005BBB; color: white;
                font-weight: bold; padding: 8px; border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #004099;
            }
        """)
        self.login_button.clicked.connect(self.login_action)

        # --- Düzen ---
        vbox = QVBoxLayout()
        vbox.addWidget(self.title_label)
        vbox.addWidget(self.email_label)
        vbox.addWidget(self.email_input)
        vbox.addWidget(self.password_label)
        vbox.addWidget(self.password_input)
        vbox.addWidget(self.login_button)

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

                # 🔹 Giriş başarılı → main_window aç
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
