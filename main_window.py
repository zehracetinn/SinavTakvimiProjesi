import sys
from PyQt6.QtWidgets import QSizePolicy
import sqlite3
from PyQt6.QtGui import QPixmap, QPainter

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
        self.bg_path = "/Users/USER/SinavTakvimiProjesi-2/kou.jpg"  # 💾 arka plan görseli

        self.setWindowTitle("Sınav Takvimi Ana Menü")
        self.setGeometry(450, 200, 600, 400)
        self.setup_ui()



    def paintEvent(self, event):
        """Arka plan resmini ekrana uygula"""
        painter = QPainter(self)
        pixmap = QPixmap(self.bg_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            painter.setOpacity(0.12)  # arka plan saydamlığı (0.0–1.0)
            painter.drawPixmap(0, 0, scaled)
        painter.end()
   

    def setup_ui(self):

        self.setStyleSheet("""
            QWidget {
                background-color: #F8F9F9;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2E2E2E;
            }

            QLabel#titleLabel {
                color: #1B5E20;
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 10px;
            }

            QLabel#subtitleLabel {
                color: #4E4E4E;
                font-size: 13px;
                margin-bottom: 20px;
            }

            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: #1B5E20;
            }

            QPushButton:disabled {
                background-color: #A5D6A7;
                color: #F1F8E9;
            }

            QScrollArea, QListWidget {
                background-color: white;
                border: 1px solid #C8E6C9;
                border-radius: 8px;
            }
        """)



        title = QLabel("Kocaeli Üniversitesi Bilgi Yönetim Sistemleri")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(f"Giriş yapan rol: {self.rol}")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)


       


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

            # 🟢 Yeni Menü Butonları (başlangıçta devre dışı)
            self.ogrenci_listesi_button = self.create_button("👩‍🎓 Öğrenci Listesi Görüntüle", self.open_ogrenci_listesi_panel)
            self.ders_listesi_button = self.create_button("📖 Ders Listesi Görüntüle", self.open_ders_listesi_panel)
            self.ogrenci_listesi_button.setEnabled(False)
            self.ders_listesi_button.setEnabled(False)
            vbox.addWidget(self.ogrenci_listesi_button)
            vbox.addWidget(self.ders_listesi_button)

           

                        # 🔍 Derslik kontrolü
            derslik_var = self.check_derslik_bilgisi()

            if not derslik_var:
                self.sinav_button = self.create_button("📅 Sınav Programı Oluştur", self.show_derslik_uyari)
                self.oturma_button = self.create_button("🪑 Oturma Planı", self.show_derslik_uyari)
                self.sinav_button.setEnabled(False)
                self.oturma_button.setEnabled(False)
                vbox.addWidget(self.sinav_button)
                vbox.addWidget(self.oturma_button)
            else:
                self.sinav_button = self.create_button("📅 Sınav Programı Oluştur", self.open_sinav_panel)
                self.oturma_button = self.create_button("🪑 Oturma Planı", self.open_oturma_plan_panel)
                vbox.addWidget(self.sinav_button)
                vbox.addWidget(self.oturma_button)


        # buradan SONRA gelen kısım (aşağıdakiler) kalacak 👇
        vbox.addStretch()
        vbox.addWidget(btn_logout)
        vbox.setSpacing(10)
        vbox.setContentsMargins(40, 20, 40, 20)
        self.setLayout(vbox)


    def create_button(self, text, func):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #1B5E20;
                border: 2px solid #1B5E20;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2E7D32;
                color: white;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #9E9E9E;
                border: 2px solid #BDBDBD;
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
        try:
            from derslik_window import DerslikWindow
            self.derslik_window = DerslikWindow(self.bolum_id)
            self.derslik_window.show()
        except Exception as e:
                QMessageBox.critical(self, "Hata", f"Derslik paneli açılırken hata oluştu:\n{str(e)}")


    def open_ders_panel(self):
        try:
            from ders_yukle_window import DersYukleWindow
            self.ders_window = DersYukleWindow(self.bolum_id)
            self.ders_window.show()
        except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ders paneli açılırken hata oluştu:\n{str(e)}")

    def open_ogrenci_panel(self):
        try:
            from ogrenci_yukle_window import OgrenciYukleWindow

            self.ogrenci_window = OgrenciYukleWindow(self.bolum_id)

        # 💡 Excel başarıyla yüklendiğinde sinyal gönderir
            self.ogrenci_window.data_loaded.connect(self.enable_menus_after_excel)

            self.ogrenci_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öğrenci yükleme ekranı açılırken hata oluştu:\n{str(e)}")




    def open_ders_listesi_panel(self):
        try:
            from ders_listesi_window import DersListesiWindow
            self.ders_listesi_window = DersListesiWindow(self.bolum_id)
            self.ders_listesi_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ders Listesi ekranı açılırken hata oluştu:\n{str(e)}")



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



    def open_ogrenci_listesi_panel(self):
        try:
            from ogrenci_listesi_window import OgrenciListesiWindow
            self.ogrenci_listesi_window = OgrenciListesiWindow(self.bolum_id)
            self.ogrenci_listesi_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öğrenci Listesi ekranı açılırken hata oluştu:\n{str(e)}")

        



    def logout(self):
        QMessageBox.information(self, "Çıkış", "Oturum sonlandırıldı.")
        self.close()
    def enable_menus_after_excel(self):
        try:
            # 🎯 Öğrenci ve Ders Listesi menülerini aktif et
            self.ogrenci_listesi_button.setEnabled(True)
            self.ders_listesi_button.setEnabled(True)

            QMessageBox.information(
                self,
                "Bilgi",
                "🎉 Excel başarıyla yüklendi! Artık Öğrenci ve Ders Listesi menüleri aktif."
            )
            self.open_ogrenci_listesi_panel()
            self.open_ders_listesi_panel()


        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Menüler aktif edilirken hata oluştu:\n{e}")



    def check_derslik_bilgisi(self):
        """Derslik tablosunda kayıt var mı kontrol eder"""
        try:
            conn = sqlite3.connect("sinav_takvimi.db")
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Derslikler WHERE bolum_id=?", (self.bolum_id,))
            count = cur.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Derslik kontrolü yapılırken hata oluştu:\n{e}")
            return False

    def show_derslik_uyari(self):
        QMessageBox.warning(
            self,
            "Uyarı",
            "Derslik bilgileri girilmeden bu alana erişemezsiniz.\n\n"
            "Lütfen önce '🏢 Derslik Yönetimi' ekranından derslik bilgilerini tamamlayın."
        )


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
  
