# oturma_plan_window.py
import sqlite3
import random
from typing import List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QMessageBox, QScrollArea, QGridLayout, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class OturmaPlanWindow(QWidget):
    def __init__(self, bolum_id: int):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("🪑 Ders Bazlı Oturma Planı")
        self.resize(1050, 700)

        # (ogr_no, ad_soyad, sira(row), sutun(col), slot(1..n), derslik_adi)
        self.current_plan: List[Tuple[str, str, int, int, int, str]] = []

        self._setup_ui()
        self._load_sinavlar()

    # ---------- UI ----------
    def _setup_ui(self):
        root = QVBoxLayout(self)

        title = QLabel("📘 Ders Bazlı Oturma Planı")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight:bold; font-size:18px; margin-bottom:10px;")
        root.addWidget(title)

        top = QHBoxLayout()
        top.addWidget(QLabel("Sınav Seç:"))
        self.cmb_exam = QComboBox()
        top.addWidget(self.cmb_exam, 1)
        self.btn_make = QPushButton("📋 Oturma Planını Oluştur")
        self.btn_pdf = QPushButton("📄 PDF Olarak Kaydet")
        self.btn_make.clicked.connect(self.make_plan)
        self.btn_pdf.clicked.connect(self.export_pdf)
        top.addWidget(self.btn_make)
        top.addWidget(self.btn_pdf)
        root.addLayout(top)

        mid = QHBoxLayout()

        # Sol: ızgara (derslik yerleşimi)
        self.scroll = QScrollArea()
        self.room_container = QWidget()
        self.grid = QGridLayout(self.room_container)
        self.grid.setSpacing(6)
        self.scroll.setWidget(self.room_container)
        self.scroll.setWidgetResizable(True)
        mid.addWidget(self.scroll, 3)

        # Sağ: yerleşenlerin listesi
        right_title = QLabel("Yerleşen Öğrenciler")
        right_title.setStyleSheet("font-weight:600;")
        self.tbl = QTableWidget(0, 6)
        self.tbl.setHorizontalHeaderLabels(["Öğrenci No", "Ad Soyad", "Derslik", "Sıra", "Sütun", "Slot"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        right = QVBoxLayout()
        right.addWidget(right_title)
        right.addWidget(self.tbl, 1)
        mid.addLayout(right, 2)

        root.addLayout(mid)

    # ---------- DB helpers ----------
    def _conn(self):
        return sqlite3.connect("sinav_takvimi.db")

    def _load_sinavlar(self):
        """Sınav programındaki sınavları listele (ders + derslik + tarih+saat)."""
        try:
            conn = self._conn()
            c = conn.cursor()
            c.execute("""
                SELECT sp.id, d.ders_kodu, d.ders_adi, dl.derslik_adi,
                       sp.tarih, sp.saat, sp.ders_id, sp.derslik_id
                FROM SinavProgrami sp
                LEFT JOIN Dersler    d  ON sp.ders_id    = d.rowid
                LEFT JOIN Derslikler dl ON sp.derslik_id = dl.rowid
                WHERE sp.bolum_id=?
                ORDER BY sp.tarih, sp.saat
            """, (self.bolum_id,))
            rows = c.fetchall()
        finally:
            conn.close()

        self.cmb_exam.clear()
        for (sp_id, kod, ad, derslik, tarih, saat, ders_id, derslik_id) in rows:
            label = f"{(kod or '')} - {(ad or '')} | {(derslik or '?')} | {tarih} {saat}"
            # data: (sp_id, ders_id, derslik_id, tarih, saat, ders_kodu, ders_adi, derslik_adi)
            self.cmb_exam.addItem(label, (sp_id, ders_id, derslik_id, tarih, saat, kod, ad, derslik))

    # ---------- grid & table temizleme ----------
    def _clear_grid_and_table(self):
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            w = item.widget()
            if w:
                w.deleteLater()
        self.tbl.setRowCount(0)

    # ---------- PLAN OLUŞTUR ----------
    def make_plan(self):
        try:
            data = self.cmb_exam.currentData()
            if not data:
                QMessageBox.warning(self, "Uyarı", "Lütfen bir sınav seçiniz.")
                return

            sp_id, ders_id, derslik_id, tarih, saat, ders_kodu, ders_adi, derslik_adi = data

            conn = self._conn()
            c = conn.cursor()

            # Derslik şemasında 'duzen_tipi' var mı?
            c.execute("PRAGMA table_info(Derslikler)")
            cols = [row[1] for row in c.fetchall()]
            has_duzen = "duzen_tipi" in cols

            if has_duzen:
                c.execute("""
                    SELECT sira_sayisi, sutun_sayisi, duzen_tipi, kapasite
                    FROM Derslikler WHERE rowid=?
                """, (derslik_id,))
                row = c.fetchone()
                if not row:
                    conn.close()
                    QMessageBox.critical(self, "Hata", f"Derslik bilgisi bulunamadı (id={derslik_id}).")
                    return
                boyuna_sira, enine_sutun, duzen_tipi, kapasite = row
                kisi_per_masa = 3 if (duzen_tipi and "3" in str(duzen_tipi)) else 2
            else:
                c.execute("""
                    SELECT sira_sayisi, sutun_sayisi, kapasite
                    FROM Derslikler WHERE rowid=?
                """, (derslik_id,))
                row = c.fetchone()
                if not row:
                    conn.close()
                    QMessageBox.critical(self, "Hata", f"Derslik bilgisi bulunamadı (id={derslik_id}).")
                    return
                boyuna_sira, enine_sutun, kapasite = row
                kisi_per_masa = 2

            toplam_koltuk = int(boyuna_sira) * int(enine_sutun) * int(kisi_per_masa)

            # --- Öğrenciler (ders kodunu normalize ederek ara) ---
            # 1) boşlukları sil + büyük harfe çevir
            c.execute("""
                SELECT ogrenci_no, ad_soyad, sinif
                FROM Ogrenci_Ders_Kayitlari
                WHERE UPPER(REPLACE(ders_kodu, ' ', '')) = UPPER(REPLACE(?, ' ', ''))
                  AND bolum_id=?
                ORDER BY ogrenci_no
            """, (ders_kodu, self.bolum_id))
            ogrenciler = c.fetchall()

            # 2) hâlâ boşsa ders_id ile eşleştirerek dene
            if not ogrenciler:
                c.execute("""
                    SELECT odk.ogrenci_no, odk.ad_soyad, odk.sinif
                    FROM Ogrenci_Ders_Kayitlari odk
                    WHERE odk.bolum_id=?
                      AND EXISTS (
                        SELECT 1
                        FROM Dersler d
                        WHERE d.rowid = ?
                          AND UPPER(REPLACE(d.ders_kodu,' ','')) = UPPER(REPLACE(odk.ders_kodu,' ', ''))
                      )
                    ORDER BY odk.ogrenci_no
                """, (self.bolum_id, ders_id))
                ogrenciler = c.fetchall()

            uyarilar = []

            if not ogrenciler:
                conn.close()
                QMessageBox.information(self, "Bilgi",
                                        f"{ders_kodu} - {ders_adi} için öğrenci kaydı bulunamadı.")
                self._clear_grid_and_table()
                return

            # Kapasite uyarısı
            if len(ogrenciler) > toplam_koltuk:
                uyarilar.append(
                    f"📌 Kapasite yetersiz: {derslik_adi} (kapasite={toplam_koltuk}) "
                    f"→ {len(ogrenciler)-toplam_koltuk} öğrenci yerleşemeyecek."
                )
                ogrenciler = ogrenciler[:toplam_koltuk]

            # Çakışma kontrolü (aynı tarih-saat)
            cakisan = []
            for ogr_no, ad, _sinif in ogrenciler:
                c.execute("""
                    SELECT COUNT(1)
                    FROM SinavProgrami sp
                    JOIN Dersler d ON sp.ders_id = d.rowid
                    JOIN Ogrenci_Ders_Kayitlari odk
                      ON odk.ders_kodu = d.ders_kodu AND odk.ogrenci_no = ?
                    WHERE sp.tarih=? AND sp.saat=? AND sp.id != ? AND sp.bolum_id=?
                """, (ogr_no, tarih, saat, sp_id, self.bolum_id))
                if (c.fetchone() or [0])[0] > 0:
                    cakisan.append((ogr_no, ad))
            if cakisan:
                uyarilar.append("⛔ Aynı tarih-saatte başka sınavı olan öğrenciler: " +
                                ", ".join([f"{o} ({a})" for o, a in cakisan]))

            # Yan yana oturmama (aynı sınıf veya soyad)
            def soyad(x: str) -> str:
                return (x or "").strip().split()[-1].lower() if x else ""

            def yan_yana_olamaz(a, b) -> bool:
                if not a or not b:
                    return False
                return (a[2] == b[2]) or (soyad(a[1]) == soyad(b[1]))

            random.shuffle(ogrenciler)
            for i in range(len(ogrenciler) - 1):
                if yan_yana_olamaz(ogrenciler[i], ogrenciler[i + 1]):
                    j = random.randint(0, len(ogrenciler) - 1)
                    ogrenciler[i], ogrenciler[j] = ogrenciler[j], ogrenciler[i]

            sorunlu_komsu = []
            for i in range(len(ogrenciler) - 1):
                if yan_yana_olamaz(ogrenciler[i], ogrenciler[i + 1]):
                    sorunlu_komsu.append((ogrenciler[i][1], ogrenciler[i + 1][1]))
            if sorunlu_komsu:
                uyarilar.append("⚠️ Yan yana ayrıştırılamayan çiftler: " +
                                ", ".join([f"{a} & {b}" for a, b in sorunlu_komsu]))

            # --- Çizim öncesi temizle ---
            self._clear_grid_and_table()

            # --- Yerleştir & Çiz ---
            self.current_plan.clear()
            index = 0
            for r in range(int(boyuna_sira)):       # satır
                for ccol in range(int(enine_sutun)): # masa (sütun)
                    masa = QFrame()
                    masa.setFrameShape(QFrame.Shape.Box)
                    masa.setStyleSheet("background-color:#f3f3f3; border:1px solid #aaa;")
                    masa_layout = QHBoxLayout()
                    masa_layout.setContentsMargins(4, 4, 4, 4)
                    masa_layout.setSpacing(6)

                    for s in range(int(kisi_per_masa)):  # slot
                        vbox = QVBoxLayout()
                        lbl = QLabel()
                        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        lbl.setStyleSheet("font-size:11px;")
                        if index < len(ogrenciler):
                            ogr_no, ad, sinif = ogrenciler[index]
                            lbl.setText(f"{ogr_no}\n{ad}")
                            self.current_plan.append(
                                (str(ogr_no), str(ad), r + 1, ccol + 1, s + 1, derslik_adi)
                            )
                            index += 1
                        else:
                            lbl.setText("—")
                        vbox.addWidget(lbl)
                        masa_layout.addLayout(vbox)

                    masa.setLayout(masa_layout)
                    self.grid.addWidget(masa, r, ccol)

            # Sağdaki tabloyu doldur
            self.tbl.setRowCount(len(self.current_plan))
            for i, (ogr_no, ad, rowi, coli, sloti, d_adi) in enumerate(self.current_plan):
                self.tbl.setItem(i, 0, QTableWidgetItem(ogr_no))
                self.tbl.setItem(i, 1, QTableWidgetItem(ad))
                self.tbl.setItem(i, 2, QTableWidgetItem(d_adi))
                self.tbl.setItem(i, 3, QTableWidgetItem(str(rowi)))
                self.tbl.setItem(i, 4, QTableWidgetItem(str(coli)))
                self.tbl.setItem(i, 5, QTableWidgetItem(str(sloti)))

            info = (f"{ders_kodu} - {ders_adi}\n"
                    f"{derslik_adi} için oturma planı oluşturuldu.\n"
                    f"Yerleşen öğrenci: {len(self.current_plan)} / {len(ogrenciler)} "
                    f"(toplam kapasite: {toplam_koltuk}).")
            if uyarilar:
                info += "\n\n" + "\n".join(uyarilar)
            QMessageBox.information(self, "Bilgi", info)

            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Oturma planı oluşturulurken hata oluştu:\n{e}")

    # ---------- PDF export ----------
    def export_pdf(self):
        try:
            if not self.current_plan:
                QMessageBox.warning(self, "Uyarı", "Lütfen önce oturma planını oluşturun.")
                return

            data = self.cmb_exam.currentData()
            if not data:
                QMessageBox.warning(self, "Uyarı", "Sınav bilgisi bulunamadı.")
                return
            sp_id, ders_id, derslik_id, tarih, saat, ders_kodu, ders_adi, derslik_adi = data

            conn = self._conn()
            c = conn.cursor()

            # duzen_tipi var mı?
            c.execute("PRAGMA table_info(Derslikler)")
            cols = [row[1] for row in c.fetchall()]
            has_duzen = "duzen_tipi" in cols

            if has_duzen:
                c.execute("""
                    SELECT sira_sayisi, sutun_sayisi, duzen_tipi
                    FROM Derslikler WHERE rowid=?
                """, (derslik_id,))
                row = c.fetchone()
                if not row:
                    conn.close()
                    QMessageBox.warning(self, "Uyarı", "Derslik bilgisi alınamadı.")
                    return
                boyuna_sira, enine_sutun, duzen_tipi = row
                kisi_per_masa = 3 if (duzen_tipi and "3" in str(duzen_tipi)) else 2
            else:
                c.execute("""
                    SELECT sira_sayisi, sutun_sayisi
                    FROM Derslikler WHERE rowid=?
                """, (derslik_id,))
                row = c.fetchone()
                if not row:
                    conn.close()
                    QMessageBox.warning(self, "Uyarı", "Derslik bilgisi alınamadı.")
                    return
                boyuna_sira, enine_sutun = row
                kisi_per_masa = 2

            conn.close()

            pdf_name = f"oturma_plani_{(ders_kodu or 'ders').replace(' ', '_')}.pdf"
            pdf = canvas.Canvas(pdf_name, pagesize=A4)
            w, h = A4

            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, h - 50, "DERS BAZLI OTURMA PLANI")
            pdf.setFont("Helvetica", 12)
            pdf.drawString(50, h - 70, f"Ders: {ders_kodu or ''} - {ders_adi or ''}")
            pdf.drawString(50, h - 90, f"Derslik: {derslik_adi or ''}")
            pdf.drawString(50, h - 110, f"Tarih: {tarih}  Saat: {saat}")

            x_start, y_start = 50, h - 150
            box_w, box_h = 58, 34
            gap = 10

            pdf.setFont("Helvetica", 8)
            for (ogr_no, ad, rowi, coli, sloti, _dadi) in self.current_plan:
                x = x_start + ((coli - 1) * (int(kisi_per_masa) * (box_w + gap))) + ((sloti - 1) * (box_w + 4))
                y = y_start - ((rowi - 1) * (box_h + gap))
                pdf.rect(x, y, box_w, box_h)
                pdf.drawString(x + 4, y + 22, str(ogr_no))
                pdf.drawString(x + 4, y + 12, (ad or "")[:22])
                pdf.drawString(x + 4, y + 2, f"S:{rowi},K:{coli},Y:{sloti}")

            pdf.save()
            QMessageBox.information(self, "PDF Kaydedildi", f"{pdf_name} oluşturuldu.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF üretirken hata oluştu:\n{e}")
