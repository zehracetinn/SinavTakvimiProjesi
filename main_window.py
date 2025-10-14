import sys
from PyQt6.QtWidgets import QSizePolicy

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class MainWindow(QWidget):
    def __init__(self, rol, bolum_id):
        super().__init__()
        self.rol = rol
        self.bolum_id = bolum_id

        self.setWindowTitle("Sınav Takvimi Ana Menü")
        self.setGeometry(450, 200, 600, 400)
        self.setup_ui()

    def setup_ui(self):
        title = QLabel("📅 Dinamik Sınav Takvimi Sistemi")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        subtitle = QLabel(f"Giriş yapan rol: {self.rol}")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #555; margin-bottom: 20px;")

        # Ortak menü
        btn_logout = QPushButton("Çıkış Yap")
        btn_logout.setStyleSheet("background-color:#c0392b; color:white; font-weight:bold; padding:7px;")
        try:
            btn_logout.clicked.disconnect()
        except TypeError:
            pass
        btn_logout.clicked.connect(self.logout)

        vbox = QVBoxLayout()
        vbox.setSpacing(8)
        vbox.setContentsMargins(20, 20, 20, 20)

        vbox.addWidget(title)
        vbox.addWidget(subtitle)

        # Rol bazlı menü oluşturma
        if self.rol == "Admin":
            vbox.addWidget(self.create_button("👤 Kullanıcı Yönetimi", self.open_user_management))
            vbox.addWidget(self.create_button("🏫 Bölümleri Görüntüle", self.open_departments))

        elif self.rol == "Bölüm Koordinatörü":
            vbox.addWidget(self.create_button("🏢 Derslik Yönetimi", self.open_derslik_panel))
            vbox.addWidget(self.create_button("📘 Ders Listesi Yükle", self.open_ders_panel))
            vbox.addWidget(self.create_button("🎓 Öğrenci Listesi Yükle", self.open_ogrenci_panel))
            vbox.addWidget(self.create_button("🗓️ Sınav Programı Oluştur", self.open_sinav_panel))
            vbox.addWidget(self.create_button("🪑 Oturma Planı", self.open_oturma_plan_panel))


        vbox.addStretch()
        vbox.addWidget(btn_logout)
        vbox.setSpacing(10)
        vbox.setContentsMargins(40, 20, 40, 20)

        self.setLayout(vbox)

    def create_button(self, text, func):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #005BBB; color: white;
                font-weight: bold; padding: 10px; border-radius: 6px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #004099;
            }
        """)
        btn.clicked.connect(func)
        return btn

    # --- Menü Fonksiyonları ---
    def open_user_management(self):
        try:
            from kullanici_window import KullaniciWindow
            self.user_window = KullaniciWindow()
            self.user_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kullanıcı yönetimi ekranı açılırken hata oluştu:\n{str(e)}")

    def open_departments(self):
        try:
            from bolum_window import BolumWindow
            self.bolum_window = BolumWindow()
            self.bolum_window.show()
        except Exception as e:
                QMessageBox.critical(self, "Hata", f"Bölümler ekranı açılırken hata oluştu:\n{str(e)}")

    def open_derslik_panel(self):
        
        from derslik_window import DerslikWindow
        self.derslik_window = DerslikWindow(self.bolum_id)
        self.derslik_window.show()

    def open_ders_panel(self):
        from ders_yukle_window import DersYukleWindow
        self.ders_window = DersYukleWindow(self.bolum_id)
        self.ders_window.show()

    def open_ogrenci_panel(self):
        QMessageBox.information(self, "Bilgi", "Öğrenci yükleme ve listeleme ekranı açılacak.")

    def open_sinav_panel(self):
        try:
            from sinav_programi_window import SinavProgramiWindow
            self.sinav_window = SinavProgramiWindow(self.bolum_id)
            self.sinav_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sınav Programı ekranı açılırken hata oluştu:\n{str(e)}")
        

    def open_oturma_plan_panel(self):
        try:
            from oturma_plan_window import OturmaPlanWindow
            self.oturma_window = OturmaPlanWindow(self.bolum_id)
            self.oturma_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Oturma Planı ekranı açılırken hata oluştu:\n{str(e)}")
        



    def logout(self):
        QMessageBox.information(self, "Çıkış", "Oturum sonlandırıldı.")
        self.close()
    def open_ders_yukle_window(self):
        from ders_yukle_window import DersYukleWindow
        # Admin kullanıcıları için örnek bolum_id = 1
        self.ders_yukle_window = DersYukleWindow(bolum_id=1)
        self.ders_yukle_window.show()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Test için sahte giriş:
    window = MainWindow("Bölüm Koordinatörü", 1)
    window.show()
    sys.exit(app.exec())
