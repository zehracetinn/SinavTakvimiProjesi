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
            "SELECT rowid AS id, ders_adi, ders_kodu, sinif FROM Dersler WHERE bolum_id=?",
            (self.bolum_id,)
        )
        dersler = cursor.fetchall()
        conn.close()

        self.ders_list.clear()
        for ders in dersler:
            # ders: (id, ders_adi, ders_kodu, sinif)
            item = QListWidgetItem(f"{ders[2]} - {ders[1]} (Sınıf: {ders[3]})")
            item.setData(Qt.ItemDataRole.UserRole, ders[0])  # id
            item.setCheckState(Qt.CheckState.Checked)
            self.ders_list.addItem(item)

    def create_program(self):
        import random
        from datetime import timedelta, datetime

        def parse_time(hhmm: str) -> tuple[int, int]:
            h, m = hhmm.split(":")
            return int(h), int(m)

        try:
            conn = sqlite3.connect("sinav_takvimi.db")
            cur = conn.cursor()

            # --- Tablo garanti ---
            cur.execute("""
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

            # 1) Parametreler
            baslangic = self.start_date.date().toPyDate()
            bitis     = self.end_date.date().toPyDate()
            sinav_turu = self.tur_combo.currentText()
            sure       = self.sure_spin.value()
            min_gap    = self.bekleme_spin.value()  # dk

            # 2) Seçili dersler (id=rowid)
            secili_dersler = []
            for i in range(self.ders_list.count()):
                it = self.ders_list.item(i)
                if it.checkState() == Qt.CheckState.Checked:
                    secili_dersler.append(it.data(Qt.ItemDataRole.UserRole))

            if not secili_dersler:
                QMessageBox.warning(self, "Uyarı", "Lütfen en az bir ders seçin!")
                return

            # 3) Derslikler (en küçük kapasiteyi tercih etmek için kapasitelerine göre sırala)
            cur.execute(
                "SELECT rowid AS id, derslik_adi, kapasite FROM Derslikler WHERE bolum_id=?",
                (self.bolum_id,)
            )
            derslikler = cur.fetchall()
            if not derslikler:
                QMessageBox.warning(self, "Uyarı", "Bu bölüme ait derslik bulunamadı!")
                return
            derslikler.sort(key=lambda x: x[2])  # kapasite artan

            # 4) Ders -> (kod, ad, sinif, ogr_sayisi, ogrenciler listesi)
            ders_bilgisi = {}
            for ders_id in secili_dersler:
                cur.execute("SELECT ders_kodu, ders_adi, sinif FROM Dersler WHERE rowid=?", (ders_id,))
                row = cur.fetchone()
                if not row:
                    ders_bilgisi[ders_id] = None
                    continue
                ders_kodu, ders_adi, sinif = row

                cur.execute("""
                    SELECT DISTINCT ogrenci_no
                    FROM Ogrenci_Ders_Kayitlari
                    WHERE ders_kodu=? AND bolum_id=?
                """, (ders_kodu, self.bolum_id))
                ogrenciler = [r[0] for r in cur.fetchall()]
                ders_bilgisi[ders_id] = (ders_kodu, ders_adi, sinif, len(ogrenciler), ogrenciler)

            # Var olmayanları at
            missing = [d for d in secili_dersler if not ders_bilgisi.get(d)]
            if missing:
                QMessageBox.warning(self, "Uyarı", f"{len(missing)} ders bulunamadı ve atlandı.")
                secili_dersler = [d for d in secili_dersler if d not in missing]
                if not secili_dersler:
                    return

            # 5) Zaman aralıkları
            tarih_listesi = []
            gun_sayisi = (bitis - baslangic).days + 1
            for i in range(gun_sayisi):
                tarih_listesi.append(baslangic + timedelta(days=i))
            saat_listesi = ["09:00", "11:00", "13:00", "15:00"]

            # 6) Eski programı temizle
            cur.execute("DELETE FROM SinavProgrami WHERE bolum_id=?", (self.bolum_id,))
            conn.commit()

            # --- Çakışma kontrol state'leri ---
            # a) Öğrenci -> (datetime listesi)
            ogrenci_program = {}  # {ogr_no: [datetime_start_of_exam, ...]}
            # b) Slot -> kullanılan derslik id'leri
            slot_rooms = {}       # {(date_str, hour_str): set(room_id)}
            # c) Sınıf (grade) -> hangi gün indeksi sırada (farklı güne dağıtma için round-robin)
            grade_next_day = {}   # {sinif: next_index}

            # Dersleri zorluk sırasına göre (çok öğrencili önce) planla
            ders_siralama = sorted(
                secili_dersler,
                key=lambda d: ders_bilgisi[d][3],  # ogr_sayisi
                reverse=True
            )

            program = []      # Excel için
            uyarilar = []     # toplanan uyarılar

            # Yardımcı: slot uygun mu?
            def slot_uygun_mu(ogrenciler, day, hour) -> bool:
                h, m = parse_time(hour)
                slot_dt = datetime(day.year, day.month, day.day, h, m)
                for ogr in ogrenciler:
                    lst = ogrenci_program.get(ogr, [])
                    for var_dt in lst:
                        # aynı saat çakışma veya min_gap ihlali?
                        diff = abs((slot_dt - var_dt).total_seconds()) / 60.0
                        if diff < min_gap or diff == 0:
                            return False
                return True

            # Yardımcı: en küçük uygun derslik
            def uygun_derslik_bul(kac_ogr, day, hour):
                key = (day.isoformat(), hour)
                kullanilan = slot_rooms.get(key, set())
                for (rid, rname, cap) in derslikler:
                    if cap >= kac_ogr and rid not in kullanilan:
                        return (rid, rname, cap)
                return None

            # Yardımcı: sınıf (grade) için bir gün öner (farklı günlere dağıt)
            def grade_icin_gun_oner(grade):
                if grade not in grade_next_day:
                    grade_next_day[grade] = 0
                idx = grade_next_day[grade] % len(tarih_listesi)
                grade_next_day[grade] += 1
                return tarih_listesi[idx]

            # PLANLAMA
            for ders_id in ders_siralama:
                ders_kodu, ders_adi, sinif, ogr_say, ogr_list = ders_bilgisi[ders_id]

                # Önce bu sınıf için önerilen günü dene; sonra tüm günleri fallback
                once_gunler = [grade_icin_gun_oner(sinif)]
                diger_gunler = [d for d in tarih_listesi if d != once_gunler[0]]
                denenecek_gunler = once_gunler + diger_gunler

                yerlesti = False
                secilen_tarih = None
                secilen_saat  = None
                secilen_derslik = None

                for gun in denenecek_gunler:
                    # önce çakışma olasılığı daha düşük saatleri dene
                    for saat in saat_listesi:
                        if not slot_uygun_mu(ogr_list, gun, saat):
                            continue
                        oda = uygun_derslik_bul(ogr_say, gun, saat)
                        if not oda:
                            continue
                        # yer bulundu
                        secilen_tarih, secilen_saat, secilen_derslik = gun, saat, oda
                        yerlesti = True
                        break
                    if yerlesti:
                        break

                if not yerlesti:
                    # nedenlerini ayrı uyarıla
                    uyarilar.append(
                        f"⚠️ {ders_kodu} - {ders_adi}: "
                        f"Uygun slot/derslik bulunamadı (ogr:{ogr_say}, min bekleme:{min_gap} dk)."
                    )
                    continue

                # Yaz ve state güncelle
                cur.execute("""
                    INSERT INTO SinavProgrami (ders_id, derslik_id, tarih, saat, sure, sinav_turu, bolum_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    ders_id, secilen_derslik[0],
                    secilen_tarih.strftime("%Y-%m-%d"),
                    secilen_saat, sure, sinav_turu, self.bolum_id
                ))

                # Öğrencilerin programına ekle
                h, m = parse_time(secilen_saat)
                slot_dt = datetime(secilen_tarih.year, secilen_tarih.month, secilen_tarih.day, h, m)
                for ogr in ogr_list:
                    ogrenci_program.setdefault(ogr, []).append(slot_dt)

                # O saatte kullanılan derslikler
                key = (secilen_tarih.isoformat(), secilen_saat)
                slot_rooms.setdefault(key, set()).add(secilen_derslik[0])

                program.append([
                    f"{ders_kodu} - {ders_adi}",
                    secilen_derslik[1],
                    secilen_tarih.strftime("%d.%m.%Y"),
                    secilen_saat,
                    sinav_turu
                ])

            conn.commit()
            conn.close()

            # Excel + mesajlar
            if program:
                df = pd.DataFrame(program, columns=["Ders", "Derslik", "Tarih", "Saat", "Tür"])
                df.to_excel("sinav_programi.xlsx", index=False)

                msg = (f"Sınav programı oluşturuldu. Toplam {len(program)} sınav planlandı.\n"
                       f"Dosya: sinav_programi.xlsx")
                if uyarilar:
                    msg += "\n\n" + "\n".join(uyarilar[:10])  # en fazla 10 uyarı göster
                QMessageBox.information(self, "Başarılı", msg)
            else:
                bilgi = "Seçilen aralık ve kısıtlarla yerleştirme yapılamadı."
                if uyarilar:
                    bilgi += "\n\n" + "\n".join(uyarilar)
                QMessageBox.warning(self, "Bilgi", bilgi)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sınav programı oluşturulurken hata oluştu:\n{str(e)}")
