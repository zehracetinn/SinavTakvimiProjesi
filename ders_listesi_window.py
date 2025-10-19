import sqlite3
import os # <--- DOSYA YOLU İÇİN EKLENDİ
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QListWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter # <--- GÖRSEL İŞLEMLERİ İÇİN EKLENDİ
from database_helper import DatabaseHelper


class DersListesiWindow(QWidget):
    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("📘 Ders Listesi ve Öğrenciler")
        self.setGeometry(400, 200, 900, 600)
        
        # KODUN HER YERDE ÇALIŞMASI İÇİN GÖRSEL YOLUNU AYARLAYALIM
        # Lütfen kou.jpg dosyasının ana proje dizininizde olduğundan emin olun.
        self.background_image_path = self.prepare_background_image("kou.jpg") # <--- YENİ FONKSİYON
        
        self.setup_ui()
        self.load_dersler()

    def prepare_background_image(self, image_path, opacity=0.08):
        """Verilen görseli şeffaflaştırır ve geçici bir dosyaya kaydeder."""
        if not os.path.exists(image_path):
            print(f"Uyarı: Arka plan görseli bulunamadı: {image_path}")
            return None

        original_pixmap = QPixmap(image_path)
        if original_pixmap.isNull():
            print(f"Uyarı: Görsel yüklenemedi: {image_path}")
            return None
            
        # Şeffaf bir katman oluştur
        transparent_pixmap = QPixmap(original_pixmap.size())
        transparent_pixmap.fill(Qt.GlobalColor.transparent)

        # Painter ile orijinal görseli şeffaf katmanın üzerine çiz
        painter = QPainter(transparent_pixmap)
        painter.setOpacity(opacity) # <--- GÖRSELİN SOLGUNLUĞU (0.0 ile 1.0 arası)
        painter.drawPixmap(0, 0, original_pixmap)
        painter.end()

        # Yeni şeffaf görseli kaydet
        output_path = "kou_bg_transparent.png"
        transparent_pixmap.save(output_path)
        return output_path

    def setup_ui(self):
        # Kocaeli Üniversitesi web sitesinden ilham alan renk paleti
        kocaeli_yesil = "#38761d"
        kocaeli_yesil_hover = "#4a9b2a"
        acik_gri_zemin = "rgba(240, 242, 245, 0.85)" # Yazıların okunabilmesi için hafif beyazlatılmış
        kenarlik_rengi = "#d0d0d0"
        yazi_rengi_koyu = "#333333"

        # ARKA PLAN GÖRSELİ STİLİ
        background_style = ""
        if self.background_image_path:
            # Not: Windows'ta dosya yolları için ters slash yerine normal slash kullanmak daha güvenlidir.
            safe_path = self.background_image_path.replace("\\", "/")
            background_style = f"""
                border-image: url({safe_path}) 0 0 0 0 stretch stretch;
            """

        self.setStyleSheet(f"""
            /* Ana Pencereye Arka Planı Ekle */
            DersListesiWindow {{
                {background_style}
            }}

            QWidget {{
                background-color: transparent; /* Arka planın görünmesi için */
                font-family: 'Segoe UI', Arial, sans-serif;
                color: {yazi_rengi_koyu};
            }}

            /* Liste ve Tablo stilleri (Okunabilirlik için yarı şeffaf arkaplan) */
            QListWidget, QTableWidget {{
                background-color: {acik_gri_zemin};
                border: 1px solid {kenarlik_rengi};
                border-radius: 5px;
                font-size: 13px;
            }}

            QHeaderView::section {{
                background-color: {kocaeli_yesil};
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }}
            
            QListWidget::item:selected {{
                background-color: {kocaeli_yesil};
                color: white;
            }}

            QListWidget::item:hover {{
                background-color: #e6f7ff;
            }}
            
            QPushButton {{
                background-color: {kocaeli_yesil};
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                border: none;
            }}

            QPushButton:hover {{
                background-color: {kocaeli_yesil_hover};
            }}
        """)

        # Ana başlık
        title = QLabel("📘 Ders Listesi ve Dersi Alan Öğrenciler")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                background-color: {kocaeli_yesil};
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 12px;
                border-radius: 5px;
                margin: 5px;
            }}
        """)

        # --- GERİ KALAN KODUNUZ AYNI ŞEKİLDE DEVAM EDİYOR ---
        
        self.ders_list = QListWidget()
        self.ders_list.itemClicked.connect(self.show_dersi_alan_ogrenciler)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Öğrenci No", "Ad Soyad"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"alternate-background-color: rgba(220, 225, 230, 0.85);")

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 5)
        layout.setSpacing(10)
        layout.addWidget(self.ders_list, 2)
        layout.addWidget(self.table, 5)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(0)
        vbox.addWidget(title)
        vbox.addLayout(layout)
        self.setLayout(vbox)

    # ... (load_dersler ve show_dersi_alan_ogrenciler metodları burada)
    # ...



    # ------------------ DERSLERİ YÜKLE ------------------
    def load_dersler(self):
        try:
            conn = DatabaseHelper.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT ders_kodu, ders_adi 
                FROM Dersler
                WHERE bolum_id=?
                ORDER BY ders_kodu
            """, (self.bolum_id,))
            dersler = cur.fetchall()

            if not dersler:
                QMessageBox.information(self, "Bilgi", "Bu bölüme ait ders bulunamadı.")
                return

            for ders in dersler:
                ders_kodu, ders_adi = ders
                self.ders_list.addItem(f"{ders_kodu} – {ders_adi}")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dersler yüklenirken hata oluştu:\n{e}")

    # ------------------ DERSİN ÖĞRENCİLERİNİ GÖSTER ------------------
    def show_dersi_alan_ogrenciler(self, item):
        try:
            ders_kodu = item.text().split("–")[0].strip()

            conn = DatabaseHelper.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT ogrenci_no, ad_soyad
                FROM Ogrenci_Ders_Kayitlari
                WHERE ders_kodu=? AND bolum_id=?
                ORDER BY ogrenci_no
            """, (ders_kodu, self.bolum_id))
            rows = cur.fetchall()

            self.table.setRowCount(0)
            if not rows:
                QMessageBox.information(self, "Bilgi", "Bu dersi alan öğrenci bulunamadı.")
                return

            for i, (ogr_no, ad) in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(ogr_no)))
                self.table.setItem(i, 1, QTableWidgetItem(str(ad)))

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öğrenci listesi alınamadı:\n{e}")
