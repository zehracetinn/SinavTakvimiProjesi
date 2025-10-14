# oturma_plan_window.py
import sqlite3
import random
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QMessageBox, QScrollArea, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class OturmaPlanWindow(QWidget):
    def __init__(self, bolum_id):
        super().__init__()
        self.bolum_id = bolum_id
        self.setWindowTitle("🪑 Ders Bazlı Oturma Planı")
        self.resize(900, 650)
        self.setup_ui()
        self.load_sinavlar()
        self.current_plan = []  # (ogr_no, ad, sıra, sütun, koltuk_no)

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("📘 Ders Bazlı Oturma Planı")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight:bold; font-size:18px; margin-bottom:10px;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Sınav Seç:"))
        self.sinav_combo = QComboBox()
        layout.addWidget(self.sinav_combo)

        btn_layout = QHBoxLayout()
        self.btn_show = QPushButton("📋 Oturma Planını Oluştur")
        self.btn_pdf = QPushButton("📄 PDF Olarak Kaydet")
        self.btn_show.clicked.connect(self.show_plan)
        self.btn_pdf.clicked.connect(self.export_pdf)
        btn_layout.addWidget(self.btn_show)
        btn_layout.addWidget(self.btn_pdf)
        layout.addLayout(btn_layout)

        self.scroll = QScrollArea()
        self.container = QWidget()
        self.grid = QGridLayout()
        self.container.setLayout(self.grid)
        self.scroll.setWidget(self.container)
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)

        self.setLayout(layout)

    def load_sinavlar(self):
        conn = sqlite3.connect("sinav_takvimi.db")
        c = conn.cursor()
        c.execute("""
            SELECT sp.id, d.ders_adi, dl.derslik_adi, sp.tarih, sp.saat
            FROM SinavProgrami sp
            LEFT JOIN Dersler d ON sp.ders_id = d.rowid
            LEFT JOIN Derslikler dl ON sp.derslik_id = dl.rowid
            WHERE sp.bolum_id=?
        """, (self.bolum_id,))


        sinavlar = c.fetchall()
        conn.close()

        self.sinav_combo.clear()
        for s in sinavlar:
            self.sinav_combo.addItem(f"{s[1]} | {s[2]} | {s[3]} {s[4]}", s[0])

    def show_plan(self):
        """Seçilen sınava göre oturma planı oluşturur (çakışma + yan yana kontrolü dahil)"""
        sinav_id = self.sinav_combo.currentData()
        if not sinav_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir sınav seçiniz.")
            return

        conn = sqlite3.connect("sinav_takvimi.db")
        c = conn.cursor()

        # Sınav bilgilerini al
        c.execute("""
            SELECT d.ders_adi, dl.derslik_adi, sp.tarih, sp.saat
            FROM SinavProgrami sp
            LEFT JOIN Dersler d ON sp.ders_id = d.rowid
            LEFT JOIN Derslikler dl ON sp.derslik_id = dl.rowid
            WHERE sp.id=?
        """, (sinav_id,))


        ders, derslik, tarih, saat = c.fetchone()

        # Derslik bilgileri
        c.execute("SELECT enine_sira, boyuna_sira, sira_yapisi, kapasite FROM Derslikler WHERE sinif_adi=?", (derslik,))
        derslik_bilgi = c.fetchone()
        if not derslik_bilgi:
            QMessageBox.critical(self, "Hata", f"{derslik} için derslik bilgisi eksik!")
            conn.close()
            return

        enine, boyuna, sira_yapisi, kapasite = derslik_bilgi

        # Dersi alan öğrenciler
        c.execute("SELECT id FROM Dersler WHERE ders_adi=?", (ders.split(" - ")[-1],))
        d_row = c.fetchone()
        if not d_row:
            QMessageBox.warning(self, "Uyarı", f"{ders} dersi veritabanında bulunamadı.")
            conn.close()
            return

        ders_id = d_row[0]

        # Öğrencileri çek
        c.execute("""
            SELECT ogrenci_no, ad_soyad, sinif
            FROM Ogrenciler
            WHERE ders_id=?
            ORDER BY ogrenci_no
        """, (ders_id,))
        ogrenciler = c.fetchall()

        toplam_koltuk = enine * boyuna * int(sira_yapisi)
        if len(ogrenciler) > toplam_koltuk:
            QMessageBox.warning(
                self,
                "Uyarı",
                f"Sınıf kapasitesi yetersiz! (Kapasite: {toplam_koltuk}, Öğrenci: {len(ogrenciler)})"
            )
            ogrenciler = ogrenciler[:toplam_koltuk]

        # 🔍 Çakışma kontrolü
        cakisan_ogrenciler = []
        for ogr_no, ad, _ in ogrenciler:
            c.execute("""
                SELECT sp.ders, sp.tarih, sp.saat 
                FROM SinavProgrami sp
                JOIN Dersler d ON sp.ders LIKE '%' || d.ders_adi || '%'
                JOIN Ogrenciler o ON o.ders_id = d.id
                WHERE o.ogrenci_no = ? AND sp.id != ?
            """, (ogr_no, sinav_id))
            diger_sinavlar = c.fetchall()
            for diger_ders, diger_tarih, diger_saat in diger_sinavlar:
                if diger_tarih == tarih and diger_saat == saat:
                    cakisan_ogrenciler.append((ogr_no, ad, diger_ders))

        if cakisan_ogrenciler:
            mesaj = "⚠️ Çakışan Öğrenciler:\n\n"
            for ogr_no, ad, diger_ders in cakisan_ogrenciler:
                mesaj += f"{ogr_no} - {ad} → aynı anda: {diger_ders}\n"
            QMessageBox.critical(self, "Ders Çakışması", mesaj)
            conn.close()
            return

        # 🧩 Yan yana oturmama kontrolü
        def soyad(ad):
            return ad.split()[-1].lower() if ad else ""

        def yan_yana_mi(a, b):
            if not a or not b:
                return False
            return a[2] == b[2] or soyad(a[1]) == soyad(b[1])

        random.shuffle(ogrenciler)
        for i in range(len(ogrenciler) - 1):
            if yan_yana_mi(ogrenciler[i], ogrenciler[i + 1]):
                j = random.randint(0, len(ogrenciler) - 1)
                ogrenciler[i], ogrenciler[j] = ogrenciler[j], ogrenciler[i]

        sorunlu = []
        for i in range(len(ogrenciler) - 1):
            if yan_yana_mi(ogrenciler[i], ogrenciler[i + 1]):
                sorunlu.append((ogrenciler[i][1], ogrenciler[i + 1][1]))

        if sorunlu:
            mesaj = "⚠️ Yan Yana Oturma Sorunu:\n\n"
            for a, b in sorunlu:
                mesaj += f"{a} ve {b} yan yana oturmayacak şekilde plan oluşturulamadı!\n"
            QMessageBox.warning(self, "Yerleşim Uyarısı", mesaj)

        # --- Grid oluştur ---
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        index = 0
        self.current_plan.clear()
        for row in range(boyuna):
            for col in range(enine):
                masa = QFrame()
                masa.setFrameShape(QFrame.Shape.Box)
                masa.setStyleSheet("background-color:#f3f3f3; border:1px solid #aaa;")
                masa_layout = QHBoxLayout()

                for s in range(int(sira_yapisi)):
                    slot = QVBoxLayout()
                    label = QLabel()
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    label.setStyleSheet("font-size:10px;")
                    if index < len(ogrenciler):
                        ogr_no, ad, sinif = ogrenciler[index]
                        label.setText(f"{ogr_no}\n{ad}")
                        self.current_plan.append((ogr_no, ad, row + 1, col + 1, s + 1))
                        index += 1
                    else:
                        label.setText("—")
                    slot.addWidget(label)
                    masa_layout.addLayout(slot)

                masa.setLayout(masa_layout)
                self.grid.addWidget(masa, row, col)

        QMessageBox.information(
            self,
            "Başarılı",
            f"{ders} için oturma planı oluşturuldu.\n{len(self.current_plan)} öğrenci yerleştirildi."
        )
        conn.close()

    def export_pdf(self):
        if not self.current_plan:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce oturma planını oluşturun.")
            return

        sinav_id = self.sinav_combo.currentData()
        conn = sqlite3.connect("sinav_takvimi.db")
        c = conn.cursor()
        c.execute("SELECT ders, derslik, tarih, saat FROM SinavProgrami WHERE id=?", (sinav_id,))
        ders, derslik, tarih, saat = c.fetchone()
        c.execute("SELECT enine_sira, boyuna_sira, sira_yapisi FROM Derslikler WHERE sinif_adi=?", (derslik,))
        enine, boyuna, sira_yapisi = c.fetchone()
        conn.close()

        pdf_name = f"oturma_plani_{ders.replace(' ', '_')}.pdf"
        pdf = canvas.Canvas(pdf_name, pagesize=A4)
        w, h = A4

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, h - 50, "DERS BAZLI OTURMA PLANI")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, h - 70, f"Ders: {ders}")
        pdf.drawString(50, h - 90, f"Derslik: {derslik}")
        pdf.drawString(50, h - 110, f"Tarih: {tarih}  Saat: {saat}")

        x_start, y_start = 70, h - 150
        box_w, box_h = 60, 35
        gap = 10

        pdf.setFont("Helvetica", 8)
        for ogr_no, ad, row, col, sira in self.current_plan:
            x = x_start + ((col - 1) * (int(sira_yapisi) * (box_w + gap))) + ((sira - 1) * (box_w + 5))
            y = y_start - ((row - 1) * (box_h + gap))
            pdf.rect(x, y, box_w, box_h)
            pdf.drawString(x + 4, y + 22, str(ogr_no))
            pdf.drawString(x + 4, y + 12, ad[:15])
            pdf.drawString(x + 4, y + 2, f"S:{row},K:{col},Y:{sira}")

        pdf.save()
        QMessageBox.information(self, "PDF Kaydedildi", f"{pdf_name} oluşturuldu.")
