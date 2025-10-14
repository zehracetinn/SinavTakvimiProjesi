# sinav_programi_window.py
import sqlite3
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QDateEdit, QSpinBox, QComboBox,
    QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import QDate, Qt


class SinavProgramiWindow(QWidget):
    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("📅 Sınav Programı Oluştur")
        self.resize(600, 600)
        self.setup_ui()
        self.load_dersler()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Ders Listesi (checkbox list)
        layout.addWidget(QLabel("Dahil Edilecek Dersler:"))
        self.ders_list = QListWidget()
        layout.addWidget(self.ders_list)

        # Tarih Aralığı
        tarih_layout = QHBoxLayout()
        tarih_layout.addWidget(QLabel("Başlangıç Tarihi:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        tarih_layout.addWidget(self.start_date)

        tarih_layout.addWidget(QLabel("Bitiş Tarihi:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(5))
        tarih_layout.addWidget(self.end_date)
        layout.addLayout(tarih_layout)

        # Sınav Türü
        tur_layout = QHBoxLayout()
        tur_layout.addWidget(QLabel("Sınav Türü:"))
        self.tur_combo = QComboBox()
        self.tur_combo.addItems(["Vize", "Final", "Bütünleme"])
        tur_layout.addWidget(self.tur_combo)
        layout.addLayout(tur_layout)

        # Süre ve Bekleme
        sure_layout = QHBoxLayout()
        sure_layout.addWidget(QLabel("Sınav Süresi (dk):"))
        self.sure_spin = QSpinBox()
        self.sure_spin.setRange(30, 180)
        self.sure_spin.setValue(75)
        sure_layout.addWidget(self.sure_spin)

        sure_layout.addWidget(QLabel("Bekleme Süresi (dk):"))
        self.bekleme_spin = QSpinBox()
        self.bekleme_spin.setRange(5, 60)
        self.bekleme_spin.setValue(15)
        sure_layout.addWidget(self.bekleme_spin)
        layout.addLayout(sure_layout)

        # Program oluştur butonu
        self.olustur_btn = QPushButton("📅 Programı Oluştur")
        self.olustur_btn.clicked.connect(self.create_program)
        layout.addWidget(self.olustur_btn)

        self.setLayout(layout)

    def load_dersler(self):
        """Veritabanından bölüm derslerini yükle"""
        conn = sqlite3.connect("sinav_takvimi.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, ders_adi, ders_kodu FROM Dersler WHERE bolum_id=?",
            (self.bolum_id,)
        )
        dersler = cursor.fetchall()
        conn.close()

        self.ders_list.clear()
        for ders in dersler:
            item = QListWidgetItem(f"{ders[2]} - {ders[1]}")
            item.setData(Qt.ItemDataRole.UserRole, ders[0])  # id
            item.setCheckState(Qt.CheckState.Checked)
            self.ders_list.addItem(item)

    def create_program(self):
        import random
        from datetime import timedelta

        try:
            conn = sqlite3.connect("sinav_takvimi.db")
            cursor = conn.cursor()

            # --- Eğer tablo yoksa oluştur ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS SinavProgrami (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ders_id INTEGER,
                    derslik_id INTEGER,
                    tarih TEXT,
                    saat TEXT,
                    sure INTEGER,
                    sinav_turu TEXT,
                    bolum_id INTEGER
                )
            """)
            conn.commit()

            # --- 1. Parametreleri oku ---
            baslangic = self.start_date.date().toPyDate()
            bitis = self.end_date.date().toPyDate()
            sinav_turu = self.tur_combo.currentText()
            sure = self.sure_spin.value()
            bekleme = self.bekleme_spin.value()  # şimdilik kullanılmıyor, ileride çakışma çözümünde kullanılacak

            # --- 2. Seçili dersleri al ---
            secili_dersler = []
            for i in range(self.ders_list.count()):
                item = self.ders_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    secili_dersler.append(item.data(Qt.ItemDataRole.UserRole))

            if not secili_dersler:
                QMessageBox.warning(self, "Uyarı", "Lütfen en az bir ders seçin!")
                return

            # --- 3. Derslikleri çek ---
            cursor.execute(
                "SELECT id, sinif_ismi, kapasite FROM Derslikler WHERE bolum_id=?",
                (self.bolum_id,)
            )
            derslikler = cursor.fetchall()
            if not derslikler:
                QMessageBox.warning(self, "Uyarı", "Bu bölüme ait derslik bulunamadı!")
                return

            # --- 4. Öğrenci sayısı kontrolü ---
            ders_ogrenci_sayilari = {}
            for ders_id in secili_dersler:
                cursor.execute("""
                    SELECT COUNT(DISTINCT ogrenci_id)
                    FROM OgrenciDers
                    WHERE ders_id=?
                """, (ders_id,))
                count = cursor.fetchone()[0] or 0
                ders_ogrenci_sayilari[ders_id] = count

            # --- 5. Tarih ve saat aralıklarını oluştur ---
            tarih_listesi = []
            gun_sayisi = (bitis - baslangic).days + 1
            for i in range(gun_sayisi):
                tarih_listesi.append(baslangic + timedelta(days=i))

            saat_listesi = ["09:00", "11:00", "13:00", "15:00"]

            # --- 6. Eski programı temizle (bu bölüm için) ---
            cursor.execute("DELETE FROM SinavProgrami WHERE bolum_id=?", (self.bolum_id,))
            conn.commit()

            # --- 7. Yeni program oluştur ---
            program = []
            for ders_id in secili_dersler:
                # Ders bilgilerini çek
                cursor.execute("SELECT ders_kodu, ders_adi FROM Dersler WHERE id=?", (ders_id,))
                row = cursor.fetchone()
                if not row:
                    # Ders silinmiş olabilir
                    QMessageBox.warning(self, "Uyarı", f"id={ders_id} dersi bulunamadı, atlandı.")
                    continue

                ders_kodu, ders_adi = row

                ogr_sayisi = ders_ogrenci_sayilari.get(ders_id, 0)
                uygun_derslik = next((d for d in derslikler if d[2] >= ogr_sayisi), None)

                if not uygun_derslik:
                    QMessageBox.warning(self, "Uyarı", f"{ders_adi} için uygun kapasitede derslik bulunamadı!")
                    continue

                tarih = random.choice(tarih_listesi)
                saat = random.choice(saat_listesi)

                cursor.execute("""
                    INSERT INTO SinavProgrami (ders_id, derslik_id, tarih, saat, sure, sinav_turu, bolum_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ders_id, uygun_derslik[0], tarih.strftime("%Y-%m-%d"), saat, sure, sinav_turu, self.bolum_id))

                program.append([
                    f"{ders_kodu} - {ders_adi}",
                    uygun_derslik[1],
                    tarih.strftime("%d.%m.%Y"),
                    saat,
                    sinav_turu
                ])

            conn.commit()
            conn.close()

            # --- 8. Excel çıktısı ---
            if program:
                df = pd.DataFrame(program, columns=["Ders", "Derslik", "Tarih", "Saat", "Tür"])
                df.to_excel("sinav_programi.xlsx", index=False)

                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Sınav programı başarıyla oluşturuldu!\n\n"
                    f"Toplam {len(program)} sınav planlandı.\n\n"
                    f"Dosya: sinav_programi.xlsx"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Bilgi",
                    "Hiç sınav planlanamadı, tüm dersler kapasite dışı kalmış olabilir."
                )

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sınav programı oluşturulurken hata oluştu:\n{str(e)}")
